# main.py
#
# Copyright 2023 Nokse
# Copyright 2025 AnmiTaliDev
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

import sys

from gi.repository import Gio, Adw, GLib
from .window import TeleprompterWindow
from .osc_server import OSCServer
from .preferences import PreferencesDialog

import gettext
from gettext import gettext as _

from os import path

LOCALE_DIR = path.join(path.dirname(__file__).split("teleprompter")[0], "locale")
gettext.bindtextdomain("teleprompter", LOCALE_DIR)
gettext.textdomain("teleprompter")


class TeleprompterApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.nokse22.teleprompter",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

        # Initialize OSC server reference
        self.osc_server = None
        self.win = None
        self.preferences = None

        # Initialize settings
        self.settings = Gio.Settings("io.github.nokse22.teleprompter")

        # Set up settings change listeners
        self._setup_settings_listeners()

        # Create actions
        self._setup_actions()

        # Apply initial theme
        self.update_theme()

    def _setup_settings_listeners(self):
        """Connect to settings change notifications"""
        self.settings.connect("changed::theme", self._on_theme_changed)
        self.settings.connect("changed::vmirror", self._on_vmirror_changed)
        self.settings.connect("changed::hmirror", self._on_hmirror_changed)
        self.settings.connect("changed::osc-port", self._on_osc_port_changed)
        self.settings.connect("changed::osc-autostart", self._on_osc_autostart_changed)

    def _setup_actions(self):
        """Set up all application actions"""
        # Basic actions
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action, ["<primary>comma"])

        # Theme action with state
        theme_action = Gio.SimpleAction.new_stateful(
            "theme",
            GLib.VariantType.new("s"),
            GLib.Variant("s", self.settings.get_string("theme")),
        )
        theme_action.connect("activate", self.on_theme_action_activated)
        self.add_action(theme_action)

        # Mirror actions with state
        self.vmirror_action = Gio.SimpleAction.new_stateful(
            "vmirror",
            None,
            GLib.Variant("b", self.settings.get_boolean("vmirror")),
        )
        self.vmirror_action.connect("activate", self.on_vmirror_action_activated)
        self.set_accels_for_action("app.vmirror", ["<primary><shift>V"])
        self.add_action(self.vmirror_action)

        self.hmirror_action = Gio.SimpleAction.new_stateful(
            "hmirror",
            None,
            GLib.Variant("b", self.settings.get_boolean("hmirror")),
        )
        self.hmirror_action.connect("activate", self.on_hmirror_action_activated)
        self.set_accels_for_action("app.hmirror", ["<primary><shift>H"])
        self.add_action(self.hmirror_action)

        # Reset and OSC actions
        self.create_action("reset-mirrors", self.on_reset_mirrors, ["<primary><shift>R"])
        self.create_action("toggle-osc", self.on_toggle_osc, ["<primary><shift>O"])

    def _on_theme_changed(self, settings, key):
        """Handle theme setting change"""
        self.update_theme()
        # Update the action state to keep UI in sync
        theme_action = self.lookup_action("theme")
        if theme_action:
            theme_action.set_state(GLib.Variant("s", settings.get_string(key)))

    def _on_vmirror_changed(self, settings, key):
        """Handle vertical mirror setting change"""
        new_value = settings.get_boolean(key)
        self.vmirror_action.set_state(GLib.Variant("b", new_value))
        if self.win:
            self.win.scroll_text_view.vmirror = new_value

    def _on_hmirror_changed(self, settings, key):
        """Handle horizontal mirror setting change"""
        new_value = settings.get_boolean(key)
        self.hmirror_action.set_state(GLib.Variant("b", new_value))
        if self.win:
            self.win.scroll_text_view.hmirror = new_value

    def _on_osc_port_changed(self, settings, key):
        """Handle OSC port setting change"""
        if self.osc_server and self.osc_server.running:
            # Restart server with new port
            self.osc_server.stop()
            new_port = settings.get_int(key) or 7400  # Default to 7400 if 0
            self.osc_server = OSCServer(self.win, new_port)
            self.osc_server.start()

    def _on_osc_autostart_changed(self, settings, key):
        """Handle OSC autostart setting change"""
        # This is mainly for preferences UI synchronization
        # The actual autostart logic runs in do_activate()
        pass

    def on_vmirror_action_activated(self, action, state):
        """Handle vmirror action activation"""
        new_state = not action.get_state().get_boolean()
        self.settings.set_boolean("vmirror", new_state)

    def on_hmirror_action_activated(self, action, state):
        """Handle hmirror action activation"""
        new_state = not action.get_state().get_boolean()
        self.settings.set_boolean("hmirror", new_state)

    def on_reset_mirrors(self, *_args):
        """Reset both mirror settings to False"""
        self.settings.set_boolean("vmirror", False)
        self.settings.set_boolean("hmirror", False)

    def on_theme_action_activated(self, action, state):
        """Handle theme action activation"""
        action.set_state(state)
        self.settings.set_string("theme", state.get_string())

    def update_theme(self):
        """Update the application theme based on settings"""
        manager = Adw.StyleManager().get_default()
        theme = self.settings.get_string("theme")

        match theme:
            case "follow":
                manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
            case "light":
                manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            case "dark":
                manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            case _:
                # Fallback to default for unknown values
                manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

    @property
    def osc_enabled(self):
        """Check if OSC server is currently running"""
        return self.osc_server is not None and self.osc_server.running

    def on_toggle_osc(self, *args):
        """Toggle OSC server on/off"""
        if self.osc_enabled:
            self.stop_osc_server()
        else:
            self.start_osc_server()

    def start_osc_server(self):
        """Start the OSC server"""
        if self.osc_enabled:
            return  # Already running

        if not self.win:
            return  # Window not available yet

        osc_port = self.settings.get_int("osc-port")
        if osc_port == 0:
            osc_port = 7400  # Default port

        try:
            self.osc_server = OSCServer(self.win, osc_port)
            self.osc_server.start()
        except Exception as e:
            print(f"Failed to start OSC server: {e}")
            self.osc_server = None

    def stop_osc_server(self):
        """Stop the OSC server"""
        if self.osc_server:
            try:
                self.osc_server.stop()
            except Exception as e:
                print(f"Error stopping OSC server: {e}")
            finally:
                self.osc_server = None

    def do_activate(self):
        """Called when the application is activated"""
        self.win = self.props.active_window
        if not self.win:
            self.win = TeleprompterWindow(application=self)

            # Create window-specific actions after window is created
            self.create_action("play", self.win.play, ["<primary>space"])
            self.create_action("fullscreen", self.win.toggle_fullscreen, ["F11"])

            # Auto-start OSC server if enabled in settings
            if self.settings.get_boolean("osc-autostart"):
                self.start_osc_server()

        self.win.present()

    def do_shutdown(self):
        """Cleanup when application terminates"""
        self.stop_osc_server()
        Adw.Application.do_shutdown(self)

    def on_about_action(self, *args):
        """Show the about dialog"""
        about = Adw.AboutDialog(
            application_name="Teleprompter",
            application_icon="io.github.nokse22.teleprompter",
            developer_name="Nokse",
            version="1.1.0",
            developers=["Nokse"],
            license_type="GTK_LICENSE_GPL_3_0",
            issue_url="https://github.com/Nokse22/teleprompter/issues",
            website="https://github.com/Nokse22/teleprompter",
            copyright="© 2023 Nokse",
        )

        about.add_link(_("Donate with Ko-Fi"), "https://ko-fi.com/nokse22")
        about.add_link(_("Donate with Github"), "https://github.com/sponsors/Nokse22")
        about.set_translator_credits(_("translator-credits"))

        about.present(self.props.active_window)

    def on_preferences_action(self, *args):
        """Show the preferences dialog"""
        if not self.preferences:
            self.preferences = PreferencesDialog()
        self.preferences.present(self.win)

    def create_action(self, name, callback, shortcuts=None):
        """Helper method to create a simple action"""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = TeleprompterApplication()
    return app.run(sys.argv)
