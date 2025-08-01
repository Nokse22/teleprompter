# window.py
#
# Copyright 2025 Nokse <nokse@posteo.com>
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

from gi.repository import Gtk, Gdk, Pango, GLib, Gio, Adw, GObject

from .scroll_text_view import TeleprompterScrollTextView

from gettext import gettext as _

GObject.type_register(TeleprompterScrollTextView)


@Gtk.Template(resource_path="/io/github/nokse22/teleprompter/gtk/window.ui")
class TeleprompterWindow(Adw.ApplicationWindow):
    __gtype_name__ = "TeleprompterWindow"

    scroll_text_view = Gtk.Template.Child()
    start_button = Gtk.Template.Child()
    fullscreen_button = Gtk.Template.Child()
    overlay = Gtk.Template.Child()
    title_widget = Gtk.Template.Child()

    playing = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings("io.github.nokse22.teleprompter")

        self.text_buffer = self.scroll_text_view.get_buffer()
        self.scrolled_window = self.scroll_text_view.get_scrolled_window()

        # Add text tags
        self.text_tag = Gtk.TextTag()
        self.highlight_tag = Gtk.TextTag()
        self.text_buffer.get_tag_table().add(self.text_tag)
        self.text_buffer.get_tag_table().add(self.highlight_tag)
        self.update_text_tags()

        # Bind mirror settings directly to the scroll text view
        self.settings.bind("hmirror", self.scroll_text_view, "hmirror", 0)
        self.settings.bind("vmirror", self.scroll_text_view, "vmirror", 0)

        adjustment = self.scroll_text_view.get_scrolled_window().get_vadjustment()
        adjustment.connect("value-changed", self.on_scroll_changed)

        self.settings.connect("changed::text-color", self.update_text_tags)
        self.settings.connect("changed::highlight-color", self.update_text_tags)
        self.settings.connect("changed::font", self.update_text_tags)
        self.settings.connect("changed::bold-highlight", self.update_text_tags)
        self.text_buffer.connect("paste-done", self.update_text_tags)
        self.text_buffer.connect("changed", self.update_text_tags)

    def on_scroll_changed(self, adjustment):
        if adjustment.get_value() == 0:
            self.title_widget.set_visible(True)
        else:
            self.title_widget.set_visible(False)

    def show_file_chooser_dialog(self):
        dialog = Gtk.FileDialog(title=_("Open File"))
        dialog.open(self, None, self.on_open_file_response)

    def on_open_file_response(self, dialog, response):
        try:
            file = dialog.open_finish(response)
            if not file:
                return
            file_path = file.get_path()
            try:
                with open(file_path, "r") as file:
                    file_contents = file.read()
                    self.text_buffer.set_text(file_contents)
                dialog.destroy()
                toast = Adw.Toast()
                toast.set_title("File successfully opened")
                toast.set_timeout(1)
                self.overlay.add_toast(toast)
            except Exception:
                toast = Adw.Toast()
                toast.set_title("Error reading file")
                toast.set_timeout(1)
                self.overlay.add_toast(toast)
        except Exception:
            return

    def autoscroll(self, scrolled_window):
        adjustment = scrolled_window.get_vadjustment()
        adjustment.set_value(adjustment.get_value() + self.wpm_to_speed())
        scrolled_window.set_vadjustment(adjustment)

        value = adjustment.get_value()
        upper = adjustment.get_upper()
        page_size = adjustment.get_page_size()

        if value == upper - page_size:
            self.playing = False
            self.start_button.set_icon_name("media-playback-start-symbolic")
            return False

        if not self.playing:
            return False
        else:
            return True

    def update_text_tags(self, *args):
        self.text_tag.set_property("foreground", self.settings.get_string("text-color"))
        self.text_tag.set_property(
            "font-desc", Pango.FontDescription(self.settings.get_string("font"))
        )

        self.highlight_tag.set_property(
            "foreground", self.settings.get_string("highlight-color")
        )
        if self.settings.get_boolean("bold-highlight"):
            self.highlight_tag.set_property("weight", Pango.Weight.BOLD)
        else:
            self.highlight_tag.set_property("weight", Pango.Weight.NORMAL)

        self.text_buffer.apply_tag(
            self.text_tag,
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
        )

        self.search_and_mark_highlight()

    def search_and_mark_highlight(self, start=None):
        if start is None:
            start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        text = "["

        match = start.forward_search(text, 0, end)

        if match is not None:
            match_start, match_end = match
            match_end_highlight = self.search_end_highlight(match_end)
            if match_end_highlight is not None:
                self.text_buffer.apply_tag(
                    self.highlight_tag, match_start, match_end_highlight
                )
            self.search_and_mark_highlight(match_end)

    def search_end_highlight(self, start):
        end = self.text_buffer.get_end_iter()

        match_right = start.forward_search("]", Gtk.TextSearchFlags(0), end)
        match_left = start.forward_search("[", Gtk.TextSearchFlags(0), end)

        if match_right is not None:
            _, match_end_right = match_right
            if match_left is not None:
                _, match_end_left = match_left
                if match_end_right.compare(match_end_left) < 0:
                    return match_end_right
            if match_left is None and match_right is not None:
                return match_end_right
            return None
        return None

    def wpm_to_speed(self):
        font_properties = self.settings.get_string("font").split()
        font_size = font_properties[-1]

        font = int(font_size)
        width = self.scroll_text_view.get_width()
        speed = self.settings.get_int("speed") * font * 0.2 / width

        if speed <= 0.25:
            speed = 0.25

        return speed

    def change_font_size(self, amount):
        font_properties = self.settings.get_string("font").split()
        font_size = font_properties[-1]

        if int(font_size) + amount > 10:
            new_font_size = int(font_size) + amount
        else:
            new_font_size = 10

        font_properties[-1] = str(new_font_size)

        self.settings.set_string("font", " ".join(font_properties))

    @Gtk.Template.Callback("play_button_clicked")
    def play(self, *args):
        if not self.playing:
            self.start_button.set_icon_name("media-playback-pause-symbolic")
            self.playing = True

            # Start continuous autoscrolling
            GLib.timeout_add(10, self.autoscroll, self.scrolled_window)
        else:
            self.start_button.set_icon_name("media-playback-start-symbolic")
            self.playing = False
            self.settings.set_int("speed", 0)

    @Gtk.Template.Callback("open_button_clicked")
    def open_button_clicked(self, *args):
        self.show_file_chooser_dialog()

    @Gtk.Template.Callback("increase_speed_button_clicked")
    def increase_speed_button_clicked(self, *args):
        self.settings.set_int("speed", self.settings.get_int("speed") + 10)

    @Gtk.Template.Callback("decrease_speed_button_clicked")
    def decrease_speed_button_clicked(self, *args):
        new_speed = self.settings.get_int("speed") - 10
        if new_speed <= 40:
            new_speed = 40
        self.settings.set_int("speed", new_speed)

    @Gtk.Template.Callback("paste_button_clicked")
    def paste_button_clicked(self, *args):
        clipboard = Gdk.Display().get_default().get_clipboard()

        def callback(clipboard, res, data):
            text = clipboard.read_text_finish(res)
            self.text_buffer.set_text(text)
            toast = Adw.Toast()
            toast.set_title("Pasted Clipboard Content")
            toast.set_timeout(1)
            self.overlay.add_toast(toast)

        data = {}
        clipboard.read_text_async(None, callback, data)

    @Gtk.Template.Callback("decrease_font_button_clicked")
    def decrease_font_button_clicked(self, *args):
        self.change_font_size(-5)

    @Gtk.Template.Callback("increase_font_button_clicked")
    def increase_font_button_clicked(self, *args):
        self.change_font_size(5)

    @Gtk.Template.Callback("fullscreen_button_clicked")
    def toggle_fullscreen(self, *args):
        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()

    @Gtk.Template.Callback("on_fullscreened_changed")
    def on_fullscreened_changed(self, *_args):
        if self.is_fullscreen():
            self.fullscreen_button.set_icon_name("view-restore-symbolic")
        else:
            self.fullscreen_button.set_icon_name("view-fullscreen-symbolic")
