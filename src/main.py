# main.py
#
# Copyright 2023 Nokse
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
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, Gdk
from .window import TeleprompterWindow

# Create an instance of AdwStyleManager
style_manager = Adw.StyleManager.get_default()

# Set the preferred color scheme to dark
style_manager.set_color_scheme(4)

class TeleprompterApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.teleprompter',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<primary>comma'])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = TeleprompterWindow(application=self)
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Teleprompter',
                                application_icon='io.github.nokse22.teleprompter',
                                developer_name='Nokse',
                                version='0.1.0',
                                developers=['Nokse'],
                                license_type="GTK_LICENSE_GPL_3_0",
                                issue_url='https://github.com/Nokse22/teleprompter/issues',
                                website='https://github.com/Nokse22/teleprompter',
                                copyright='© 2023 Noske')
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""

        pref = Adw.PreferencesWindow()

        settingsPage = Adw.PreferencesPage(title="Generals")
        settingsPage.set_icon_name("applications-system-symbolic")
        pref.add(settingsPage)

        # stylePage = Adw.PreferencesPage(title="Style")
        # stylePage.set_icon_name("applications-graphics-symbolic")
        # pref.add(stylePage)

        scrollSettingsGroup = Adw.PreferencesGroup(title="Scroll Settings")
        settingsPage.add(scrollSettingsGroup)

        scrollSpeedRow = Adw.ActionRow(title="Scroll Speed", subtitle="Measured in words per minute")
        scrollSettingsGroup.add(scrollSpeedRow)

        scrollSpeedScale = Gtk.Scale(valign = Gtk.Align.CENTER)
        scrollSpeedScale.set_size_request(200, -1)
        scrollSpeedScale.set_value_pos(0)
        scrollSpeedScale.set_draw_value(True)

        scrollSpeedRow.add_suffix(scrollSpeedScale)
        speed = Gtk.Adjustment(upper=200, step_increment=1, lower=10)
        speed.set_value(TeleprompterWindow.settings.speed)
        scrollSpeedScale.set_adjustment(speed)


        slowScrollSpeedRow = Adw.ActionRow(title="Slow Scroll Speed", subtitle="When pressing the spacebar")
        # scrollSettingsGroup.add(slowScrollSpeedRow)

        slowScrollSpeedScale = Gtk.Scale(valign = Gtk.Align.CENTER)
        slowScrollSpeedScale.set_size_request(200, -1)
        slowScrollSpeedScale.set_value_pos(0)
        slowScrollSpeedScale.set_draw_value(True)

        slowScrollSpeedRow.add_suffix(slowScrollSpeedScale)
        speed2 = Gtk.Adjustment(upper=TeleprompterWindow.settings.speed / 2, step_increment=1, lower=5)
        speed2.set_value(TeleprompterWindow.settings.slowSpeed)
        slowScrollSpeedScale.set_adjustment(speed2)

        textGroup = Adw.PreferencesGroup(title="Text")
        settingsPage.add(textGroup)

        highlightColorPickerRow = Adw.ActionRow(title="Highlight color")
        textGroup.add(highlightColorPickerRow)

        highlightColorPicker = Gtk.ColorButton(valign = Gtk.Align.CENTER)
        highlightColorPicker.set_rgba(TeleprompterWindow.settings.highlightColor)
        highlightColorPickerRow.add_suffix(highlightColorPicker)

        boldHighlight = Adw.ActionRow(title="Bold Highlight")
        textGroup.add(boldHighlight)

        boldHighlightSwitch = Gtk.Switch(valign = Gtk.Align.CENTER)
        boldHighlightSwitch.set_active(TeleprompterWindow.settings.boldHighlight)

        boldHighlight.add_suffix(boldHighlightSwitch)

        fontColorPickerRow = Adw.ActionRow(title="Font color")
        textGroup.add(fontColorPickerRow)

        fontPickerRow = Adw.ActionRow(title="Font")
        textGroup.add(fontPickerRow)

        fontPicker = Gtk.FontButton(valign = Gtk.Align.CENTER)
        fontPicker.set_font(TeleprompterWindow.settings.font)
        fontPickerRow.add_suffix(fontPicker)

        fontColorPicker = Gtk.ColorButton(valign = Gtk.Align.CENTER)
        fontColorPicker.set_rgba(TeleprompterWindow.settings.textColor)
        fontColorPickerRow.add_suffix(fontColorPicker)


        # backgroundGroup = Adw.PreferencesGroup(title="Background")
        # stylePage.add(backgroundGroup)

        # backgroundColorPickerRow = Adw.ActionRow(title="Background color")
        # backgroundGroup.add(backgroundColorPickerRow)

        # backgroundColorPicker = Gtk.ColorButton(valign = Gtk.Align.CENTER)
        # backgroundColorPicker.set_rgba(TeleprompterWindow.settings.backgroundColor)
        # backgroundColorPickerRow.add_suffix(backgroundColorPicker)

        pref.present()

        # backgroundColorPicker.connect("color-set", self.on_background_color_changed)
        highlightColorPicker.connect("color-set", self.on_highlight_color_changed)
        fontColorPicker.connect("color-set", self.on_text_color_changed)
        fontPicker.connect("font-set", self.on_font_changed)
        scrollSpeedScale.connect("value-changed", self.on_speed_changed, speed2)
        slowScrollSpeedScale.connect("value-changed", self.on_slow_speed_changed)
        boldHighlightSwitch.connect("state-set", self.on_bold_highlight_set)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_background_color_changed(self, colorWidget):
        # print("background color changed")
        TeleprompterWindow.settings.backgroundColor = colorWidget.get_rgba()

    def on_text_color_changed(self, colorWidget):
        # print("font color changed")
        TeleprompterWindow.settings.textColor = colorWidget.get_rgba()

    def on_highlight_color_changed(self, colorWidget):
        # print("highlight color changed")
        TeleprompterWindow.settings.highlightColor = colorWidget.get_rgba()

    def on_font_changed(self, fontWidget):
        # print("font changed")
        TeleprompterWindow.settings.font = fontWidget.get_font()

    def on_speed_changed(self, sliderWidget, slowSpeedAdj):
        # print("speed changed")
        speed1 = sliderWidget.get_value()
        TeleprompterWindow.settings.speed = speed1
        if slowSpeedAdj.get_value() >= speed1 / 2:
            slowSpeedAdj.set_value(speed1 / 2)
            slowSpeedAdj.set_upper(sliderWidget.get_value() / 2)
        else:
            slowSpeedAdj.set_upper(sliderWidget.get_value() / 2)

    def on_slow_speed_changed(self, sliderWidget):
        # print("slow speed changed")
        TeleprompterWindow.settings.slowSpeed = sliderWidget.get_value()

    def on_bold_highlight_set(self, switch, foo):
        TeleprompterWindow.settings.boldHighlight = not switch.get_state()
        print(switch.get_state())

def main(version):
    """The application's entry point."""
    app = TeleprompterApplication()
    return app.run(sys.argv)
