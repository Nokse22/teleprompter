# preferences.py
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

from gi.repository import Gtk, Adw, Gio, Gdk, Pango


@Gtk.Template(resource_path="/io/github/nokse22/teleprompter/gtk/preferences.ui")
class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "PreferencesDialog"

    # General settings widgets
    scroll_speed_row = Gtk.Template.Child()
    highlight_color_picker = Gtk.Template.Child()
    bold_highlight_row = Gtk.Template.Child()
    font_color_picker = Gtk.Template.Child()
    font_picker = Gtk.Template.Child()

    # OSC settings widgets
    osc_enable_row = Gtk.Template.Child()
    osc_port_row = Gtk.Template.Child()
    osc_autostart_row = Gtk.Template.Child()
    osc_commands_row = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings.new("io.github.nokse22.teleprompter")

        self.settings.bind(
            "speed", self.scroll_speed_row, "value", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "bold-highlight",
            self.bold_highlight_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        self.settings.bind(
            "osc-port", self.osc_port_row, "value", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "osc-autostart",
            self.osc_autostart_row,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )

        # Set initial value
        self.set_color_button_rgba(
            self.highlight_color_picker, self.settings.get_string("highlight-color")
        )
        self.set_color_button_rgba(
            self.font_color_picker, self.settings.get_string("text-color")
        )
        self.font_picker.set_font_desc(
            Pango.FontDescription(self.settings.get_string("font"))
        )

        # Connect signals
        self.highlight_color_picker.connect(
            "notify::rgba", self.on_rgba_changed, "highlight-color"
        )
        self.font_color_picker.connect(
            "notify::rgba", self.on_rgba_changed, "text-color"
        )
        self.font_picker.connect(
            "notify::font-desc", self.on_font_desc_changed
        )

    def on_font_desc_changed(self, font_button, font_desc):
        self.settings.set_string("font", font_button.get_font_desc().to_string())

    def on_rgba_changed(self, color_button, rgba, setting_key):
        self.settings.set_string(setting_key, color_button.get_rgba().to_string())

    def set_color_button_rgba(self, color_button, rgba_string):
        rgba = Gdk.RGBA()
        rgba.parse(rgba_string)
        color_button.set_rgba(rgba)
