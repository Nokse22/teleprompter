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

import gettext
import locale
from os import path
from os.path import abspath, dirname, join, realpath

LOCALE_DIR = path.join(path.dirname(__file__).split('teleprompter')[0],'locale')
# print(LOCALE_DIR)
gettext.bindtextdomain('teleprompter', LOCALE_DIR)
gettext.textdomain('teleprompter')

# Set the color scheme to force dark always
style_manager = Adw.StyleManager.get_default()
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
        self.win = self.props.active_window
        if not self.win:
            self.win = TeleprompterWindow(application=self)
            self.create_action('play', self.win.bar1, ['<primary>space'])
            self.create_action('fullscreen', self.win.bar8, ['F11'])
        self.win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
                                application_name='Teleprompter',
                                application_icon='io.github.nokse22.teleprompter',
                                developer_name='Nokse',
                                version='0.1.8',
                                developers=['Nokse'],
                                license_type="GTK_LICENSE_GPL_3_0",
                                issue_url='https://github.com/Nokse22/teleprompter/issues',
                                website='https://github.com/Nokse22/teleprompter',
                                copyright='© 2023 Noske')
        # Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_("translator-credits"))        
        about.present(self.props.active_window)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""

        pref = Adw.PreferencesDialog()

        settingsPage = Adw.PreferencesPage(title="Generals")
        settingsPage.set_icon_name("applications-system-symbolic")
        pref.add(settingsPage)

        # stylePage = Adw.PreferencesPage(title="Style")
        # stylePage.set_icon_name("applications-graphics-symbolic")
        # pref.add(stylePage)

        scrollSettingsGroup = Adw.PreferencesGroup(title=gettext.gettext("Scroll Settings"))
        settingsPage.add(scrollSettingsGroup)

        scrollSpeedRow = Adw.SpinRow(title=gettext.gettext("Scroll Speed"), subtitle=gettext.gettext("In words per minute (approximately)"))
        scrollSettingsGroup.add(scrollSpeedRow)

        speed_adj = Gtk.Adjustment(upper=200, step_increment=1, lower=10)
        speed_adj.set_value(self.win.settings.speed)
        scrollSpeedRow.set_adjustment(speed_adj)

        textGroup = Adw.PreferencesGroup(title=gettext.gettext("Text"))
        settingsPage.add(textGroup)

        highlightColorPickerRow = Adw.ActionRow(title=gettext.gettext("Highlight color"))
        textGroup.add(highlightColorPickerRow)

        highlightColorPicker = Gtk.ColorButton(valign = Gtk.Align.CENTER)
        highlightColorPicker.set_rgba(self.win.settings.highlightColor)
        highlightColorPickerRow.add_suffix(highlightColorPicker)

        boldHighlight = Adw.ActionRow(title=gettext.gettext("Bold Highlight"))
        textGroup.add(boldHighlight)

        boldHighlightSwitch = Gtk.Switch(valign = Gtk.Align.CENTER)
        boldHighlightSwitch.set_active(self.win.settings.boldHighlight)

        boldHighlight.add_suffix(boldHighlightSwitch)

        fontColorPickerRow = Adw.ActionRow(title=gettext.gettext("Font color"))
        textGroup.add(fontColorPickerRow)

        fontPickerRow = Adw.ActionRow(title=gettext.gettext("Font"))
        textGroup.add(fontPickerRow)

        fontPicker = Gtk.FontButton(valign = Gtk.Align.CENTER)
        fontPicker.set_font(self.win.settings.font)
        fontPickerRow.add_suffix(fontPicker)

        fontColorPicker = Gtk.ColorButton(valign = Gtk.Align.CENTER)
        fontColorPicker.set_rgba(self.win.settings.textColor)
        fontColorPickerRow.add_suffix(fontColorPicker)

        pref.present(self.win)

        highlightColorPicker.connect("color-set", self.on_highlight_color_changed)
        fontColorPicker.connect("color-set", self.on_text_color_changed)
        fontPicker.connect("font-set", self.on_font_changed)
        speed_adj.connect("value-changed", self.on_speed_changed)
        # scrollSpeedRow.connect("value-changed", self.on_slow_speed_changed)
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
        self.win.settings.backgroundColor = colorWidget.get_rgba()

    def on_text_color_changed(self, colorWidget):
        # print("font color changed")
        self.win.settings.textColor = colorWidget.get_rgba()

        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

    def on_highlight_color_changed(self, colorWidget):
        # print("highlight color changed")
        self.win.settings.highlightColor = colorWidget.get_rgba()

        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

    def on_font_changed(self, fontWidget):
        # print("font changed")
        font_properties = fontWidget.get_font().split()
        font_size = font_properties[-1]

        if int(font_size) > 10:
            new_font_size = int(font_size)
        else:
            new_font_size = 10

        # Update the font size in the font properties list
        font_properties[-1] = str(new_font_size)

        # Construct the updated font string
        self.win.settings.font = ' '.join(font_properties)

        self.win.updateFont()
        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

    def on_speed_changed(self, speed_adj):
        # print("speed changed")
        speed = speed_adj.get_value()
        self.win.settings.speed = speed
        # if speed_adj.get_value() >= speed1 / 2:
        #     speed_adj.set_value(speed1 / 2)
        #     speed_adj.set_upper(sliderWidget.get_value() / 2)
        # else:
        #     speed_adj.set_upper(sliderWidget.get_value() / 2)

        self.win.save_app_settings(self.win.settings)

    def on_slow_speed_changed(self, sliderWidget):
        # print("slow speed changed")
        self.win.settings.slowSpeed = sliderWidget.get_value()

        self.win.save_app_settings(self.win.settings)

    def on_bold_highlight_set(self, switch, foo):
        self.win.settings.boldHighlight = not switch.get_state()
        print(switch.get_state())

        self.win.updateFont()
        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

def main(version):
    """The application's entry point."""
    app = TeleprompterApplication()
    return app.run(sys.argv)
