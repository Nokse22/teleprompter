# osc_server.py
#
# Copyright 2024 AnmiTaliDev
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import threading
import socket
import struct

from gi.repository import GLib, Adw


class OSCMessage:
    def __init__(self, address, args=None):
        self.address = address
        self.args = args or []

    def pack(self):
        """Pack OSC message into bytes"""
        # Address with null terminator and padding
        addr_bytes = self.address.encode("utf-8") + b"\x00"
        addr_bytes += b"\x00" * (4 - len(addr_bytes) % 4)

        # Argument types
        type_tag = ","
        arg_bytes = b""

        for arg in self.args:
            if isinstance(arg, int):
                type_tag += "i"
                arg_bytes += struct.pack(">i", arg)
            elif isinstance(arg, float):
                type_tag += "f"
                arg_bytes += struct.pack(">f", arg)
            elif isinstance(arg, str):
                type_tag += "s"
                str_bytes = arg.encode("utf-8") + b"\x00"
                str_bytes += b"\x00" * (4 - len(str_bytes) % 4)
                arg_bytes += str_bytes
            elif isinstance(arg, bool):
                type_tag += "T" if arg else "F"

        # Type tag with null terminator and padding
        type_bytes = type_tag.encode("utf-8") + b"\x00"
        type_bytes += b"\x00" * (4 - len(type_bytes) % 4)

        return addr_bytes + type_bytes + arg_bytes


def parse_osc_message(data):
    """Parse OSC message from bytes"""
    offset = 0

    # Parse address
    addr_end = data.find(b"\x00", offset)
    address = data[offset:addr_end].decode("utf-8")
    offset = (addr_end + 4) & ~3  # Align to 4 bytes

    # Parse type tag
    type_start = offset
    type_end = data.find(b"\x00", type_start)
    type_tag = data[type_start:type_end].decode("utf-8")
    offset = (type_end + 4) & ~3

    # Parse arguments
    args = []
    for t in type_tag[1:]:  # Skip first comma
        if t == "i":
            args.append(struct.unpack(">i", data[offset : offset + 4])[0])
            offset += 4
        elif t == "f":
            args.append(struct.unpack(">f", data[offset : offset + 4])[0])
            offset += 4
        elif t == "s":
            str_end = data.find(b"\x00", offset)
            args.append(data[offset:str_end].decode("utf-8"))
            offset = (str_end + 4) & ~3
        elif t == "T":
            args.append(True)
        elif t == "F":
            args.append(False)

    return OSCMessage(address, args)


class OSCServer:
    def __init__(self, window, port=7400):
        self.window = window
        self.port = port
        self.socket = None
        self.running = False
        self.thread = None

        # Mapping of OSC addresses to methods
        self.handlers = {
            "/teleprompter/load": self.handle_load_file,
            "/teleprompter/text": self.handle_set_text,
            "/teleprompter/play": self.handle_play,
            "/teleprompter/pause": self.handle_pause,
            "/teleprompter/stop": self.handle_stop,
            "/teleprompter/speed": self.handle_set_speed,
            "/teleprompter/fontsize": self.handle_set_fontsize,
            "/teleprompter/position": self.handle_set_position,
            "/teleprompter/fullscreen": self.handle_fullscreen,
            "/teleprompter/mirror/horizontal": self.handle_hmirror,
            "/teleprompter/mirror/vertical": self.handle_vmirror,
            "/teleprompter/reset": self.handle_reset,
            "/teleprompter/status": self.handle_get_status,
        }

    def start(self):
        """Start OSC server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.settimeout(1.0)  # Timeout for graceful shutdown

            self.running = True
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()

            # Notification about successful startup
            GLib.idle_add(self._show_toast, f"OSC Server started on port {self.port}")

            return True
        except Exception as e:
            GLib.idle_add(self._show_toast, f"Failed to start OSC server: {str(e)}")
            return False

    def stop(self):
        """Stop OSC server"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join(timeout=2)

    def _run_server(self):
        """Main server loop"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                if data:
                    self._handle_message(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:  # Only show error if server is still running
                    GLib.idle_add(self._show_toast, f"OSC Error: {str(e)}")

    def _handle_message(self, data, addr):
        """Handle incoming OSC message"""
        try:
            message = parse_osc_message(data)

            if message.address in self.handlers:
                # Execute in main GTK thread
                GLib.idle_add(self.handlers[message.address], message.args, addr)
            else:
                GLib.idle_add(
                    self._show_toast, f"Unknown OSC address: {message.address}"
                )

        except Exception as e:
            GLib.idle_add(self._show_toast, f"Failed to parse OSC message: {str(e)}")

    def _show_toast(self, message):
        """Show notification in UI"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        self.window.overlay.add_toast(toast)

    def _send_response(self, addr, address, *args):
        """Send response to client"""
        try:
            response = OSCMessage(address, list(args))
            self.socket.sendto(response.pack(), addr)
        except Exception as e:
            self._show_toast(f"Failed to send OSC response: {str(e)}")

    # OSC command handlers

    def handle_load_file(self, args, addr):
        """Load text file: /teleprompter/load [string path]"""
        if not args:
            self._send_response(addr, "/teleprompter/error", "Missing file path")
            return

        file_path = args[0]
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.window.text_buffer.set_text(content)
                self.window.apply_text_tags()
                self.window.update_font()
                start = self.window.text_buffer.get_start_iter()
                self.window.search_and_mark_highlight(start)

                self._show_toast(f"Loaded file: {file_path}")
                self._send_response(addr, "/teleprompter/loaded", file_path)
        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            self._show_toast(error_msg)
            self._send_response(addr, "/teleprompter/error", error_msg)

    def handle_set_text(self, args, addr):
        """Set text content: /teleprompter/text [string content]"""
        if not args:
            self._send_response(addr, "/teleprompter/error", "Missing text content")
            return

        text_content = args[0]
        self.window.text_buffer.set_text(text_content)
        self.window.apply_text_tags()
        self.window.update_font()
        start = self.window.text_buffer.get_start_iter()
        self.window.search_and_mark_highlight(start)

        self._show_toast("Text updated via OSC")
        self._send_response(addr, "/teleprompter/text_set", len(text_content))

    def handle_play(self, args, addr):
        """Start playback: /teleprompter/play"""
        if not self.window.playing:
            self.window.play()
            self._send_response(addr, "/teleprompter/playing", True)
        else:
            self._send_response(addr, "/teleprompter/already_playing")

    def handle_pause(self, args, addr):
        """Pause playback: /teleprompter/pause"""
        if self.window.playing:
            self.window.play()  # Переключает состояние
            self._send_response(addr, "/teleprompter/paused")
        else:
            self._send_response(addr, "/teleprompter/already_paused")

    def handle_stop(self, args, addr):
        """Stop playback and reset position: /teleprompter/stop"""
        if self.window.playing:
            self.window.play()  # Stop if playing

        # Reset position to beginning
        adjustment = self.window.scrolled_window.get_vadjustment()
        adjustment.set_value(0)

        self._send_response(addr, "/teleprompter/stopped")

    def handle_set_speed(self, args, addr):
        """Set playback speed: /teleprompter/speed [float wpm]"""
        if not args:
            self._send_response(addr, "/teleprompter/error", "Missing speed value")
            return

        try:
            speed = float(args[0])
            if 10 <= speed <= 500:  # Reasonable limits
                self.window.settings.speed = speed
                self._send_response(addr, "/teleprompter/speed_set", speed)
            else:
                self._send_response(
                    addr, "/teleprompter/error", "Speed must be between 10-500 WPM"
                )
        except ValueError:
            self._send_response(addr, "/teleprompter/error", "Invalid speed value")

    def handle_set_fontsize(self, args, addr):
        """Set font size: /teleprompter/fontsize [int size]"""
        if not args:
            self._send_response(addr, "/teleprompter/error", "Missing font size")
            return

        try:
            size = int(args[0])
            if 10 <= size <= 200:  # Reasonable limits
                font_properties = self.window.settings.font.split()
                font_properties[-1] = str(size)
                self.window.settings.font = " ".join(font_properties)

                self.window.update_font()
                self.window.apply_text_tags()
                start = self.window.text_buffer.get_start_iter()
                self.window.search_and_mark_highlight(start)
                self.window.save_app_settings(self.window.settings)

                self._send_response(addr, "/teleprompter/fontsize_set", size)
            else:
                self._send_response(
                    addr, "/teleprompter/error", "Font size must be between 10-200"
                )
        except ValueError:
            self._send_response(addr, "/teleprompter/error", "Invalid font size")

    def handle_set_position(self, args, addr):
        """Set scroll position: /teleprompter/position [float 0.0-1.0]"""
        if not args:
            self._send_response(addr, "/teleprompter/error", "Missing position value")
            return

        try:
            position = float(args[0])
            if 0.0 <= position <= 1.0:
                adjustment = self.window.scrolled_window.get_vadjustment()
                max_value = adjustment.get_upper() - adjustment.get_page_size()
                new_value = max_value * position
                adjustment.set_value(new_value)

                self._send_response(addr, "/teleprompter/position_set", position)
            else:
                self._send_response(
                    addr, "/teleprompter/error", "Position must be between 0.0-1.0"
                )
        except ValueError:
            self._send_response(addr, "/teleprompter/error", "Invalid position value")

    def handle_fullscreen(self, args, addr):
        """Toggle fullscreen mode: /teleprompter/fullscreen [bool]"""
        if args:
            fullscreen = bool(args[0])
            if fullscreen and not self.window.is_fullscreen():
                self.window.fullscreen()
            elif not fullscreen and self.window.is_fullscreen():
                self.window.unfullscreen()
        else:
            # Toggle state
            self.window.toggle_fullscreen()

        self._send_response(
            addr, "/teleprompter/fullscreen", self.window.is_fullscreen()
        )

    def handle_hmirror(self, args, addr):
        """Horizontal mirroring: /teleprompter/mirror/horizontal [bool]"""
        if args:
            mirror = bool(args[0])
            self.window.scroll_text_view.hmirror = mirror
            app = self.window.get_application()
            app.hmirror_action.set_state(GLib.Variant.new_boolean(mirror))
            app.saved_settings.set_boolean("hmirror", mirror)
        else:
            # Toggle state
            current = self.window.scroll_text_view.hmirror
            self.window.scroll_text_view.hmirror = not current

        self._send_response(
            addr, "/teleprompter/hmirror", self.window.scroll_text_view.hmirror
        )

    def handle_vmirror(self, args, addr):
        """Vertical mirroring: /teleprompter/mirror/vertical [bool]"""
        if args:
            mirror = bool(args[0])
            self.window.scroll_text_view.vmirror = mirror
            app = self.window.get_application()
            app.vmirror_action.set_state(GLib.Variant.new_boolean(mirror))
            app.saved_settings.set_boolean("vmirror", mirror)
        else:
            # Toggle state
            current = self.window.scroll_text_view.vmirror
            self.window.scroll_text_view.vmirror = not current

        self._send_response(
            addr, "/teleprompter/vmirror", self.window.scroll_text_view.vmirror
        )

    def handle_reset(self, args, addr):
        """Reset mirroring and position: /teleprompter/reset"""
        # Reset mirroring
        self.window.scroll_text_view.hmirror = False
        self.window.scroll_text_view.vmirror = False

        app = self.window.get_application()
        app.vmirror_action.set_state(GLib.Variant.new_boolean(False))
        app.hmirror_action.set_state(GLib.Variant.new_boolean(False))

        # Reset position
        adjustment = self.window.scrolled_window.get_vadjustment()
        adjustment.set_value(0)

        # Stop playback
        if self.window.playing:
            self.window.play()

        self._send_response(addr, "/teleprompter/reset_complete")

    def handle_get_status(self, args, addr):
        """Get current status: /teleprompter/status"""
        adjustment = self.window.scrolled_window.get_vadjustment()
        max_value = adjustment.get_upper() - adjustment.get_page_size()
        position = adjustment.get_value() / max_value if max_value > 0 else 0

        # Send detailed status
        self._send_response(addr, "/teleprompter/status/playing", self.window.playing)
        self._send_response(
            addr, "/teleprompter/status/speed", self.window.settings.speed
        )
        self._send_response(addr, "/teleprompter/status/position", position)
        self._send_response(
            addr, "/teleprompter/status/fullscreen", self.window.is_fullscreen()
        )
        self._send_response(
            addr, "/teleprompter/status/hmirror", self.window.scroll_text_view.hmirror
        )
        self._send_response(
            addr, "/teleprompter/status/vmirror", self.window.scroll_text_view.vmirror
        )
