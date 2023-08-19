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

        css = '''
        .hb-color{
            background:#242424ff;
            border-top-left-radius: 18px;
            border-top-right-radius: 18px;
        }
        .hb-color-fs{
            background:#242424ff;
        }
        .bg-color{
            background:#242424ff;
            border-radius: 14px;
            box-shadow:inset 0px 0px 0px 1px #373737;
        }
        .bg-color-fs{
            background:#242424ff;
        }
        .tr-color{
            border-radius: 14px;
            box-shadow:inset 0px 0px 0px 10px #242424;
            color: white;
        }
        .tr-color-fs{
            color: white;
        }
        '''
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css, -1)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<primary>comma'])
        self.create_action('transparent', self.on_transparent_action, ['<primary>t'])

        self.create_action('increase-font', self.on_increase_font, ['<primary>plus'])
        self.create_action('decrease-font', self.on_decrease_font, ['<primary>minus'])

        self.create_action('increase-speed', self.on_transparent_action, ['<primary>q'])
        self.create_action('decrease-speed', self.on_transparent_action, ['<primary>w'])

    def on_increase_font(self, widget=None, _=None):
        self.win.modifyFont(5)
        self.win.updateFont()
        self.win.save_app_settings(self.win.settings)

    def on_decrease_font(self, widget=None, _=None):
        self.win.modifyFont(-5)
        self.win.updateFont()
        self.win.save_app_settings(self.win.settings)

    def on_transparent_action(self, widget=None, _=None):
        if not self.win.transparent:
            if self.win.is_maximized() or self.win.is_fullscreen():
                self.win.box1.remove_css_class("bg-color")
                self.win.box1.add_css_class("tr-color-fs")
                self.win.box1.remove_css_class("bg-color-fs")
                self.win.headerbar.add_css_class("hb-color-fs")
                self.win.transparent = True
            else:
                self.win.box1.add_css_class("tr-color")
                self.win.box1.remove_css_class("bg-color")
                self.win.headerbar.add_css_class("hb-color")
                self.win.transparent = True

        else:
            if self.win.is_maximized() or self.win.is_fullscreen():
                self.win.box1.add_css_class("bg-color-fs")
                self.win.box1.remove_css_class("tr-color-fs")
                self.win.transparent = False

            else:
                self.win.box1.remove_css_class("tr-color")
                self.win.box1.add_css_class("bg-color")

                self.win.transparent = False
            self.win.headerbar.remove_css_class("hb-color")
            self.win.headerbar.remove_css_class("hb-color-fs")

            # self.win.box1.add_css_class("bg-color")
            # self.win.box1.remove_css_class("tr-color")
            # self.win.transparent = False

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.win = self.props.active_window
        if not self.win:
            self.win = TeleprompterWindow(application=self)
        self.win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Teleprompter',
                                application_icon='io.github.nokse22.teleprompter',
                                developer_name='Nokse',
                                version='0.1.4',
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

        scrollSettingsGroup = Adw.PreferencesGroup(title=gettext.gettext("Scroll Settings"))
        settingsPage.add(scrollSettingsGroup)

        scrollSpeedRow = Adw.ActionRow(title=gettext.gettext("Scroll Speed"), subtitle=gettext.gettext("In words per minute (approximately)"))
        scrollSettingsGroup.add(scrollSpeedRow)

        scrollSpeedScale = Gtk.Scale(valign = Gtk.Align.CENTER)
        scrollSpeedScale.set_size_request(200, -1)
        scrollSpeedScale.set_value_pos(0)
        scrollSpeedScale.set_draw_value(True)

        scrollSpeedRow.add_suffix(scrollSpeedScale)
        speed = Gtk.Adjustment(upper=200, step_increment=1, lower=10)
        speed.set_value(self.win.settings.speed)
        scrollSpeedScale.set_adjustment(speed)


        slowScrollSpeedRow = Adw.ActionRow(title=gettext.gettext("Slow Scroll Speed"), subtitle=gettext.gettext("When pressing the spacebar"))
        # scrollSettingsGroup.add(slowScrollSpeedRow)

        slowScrollSpeedScale = Gtk.Scale(valign = Gtk.Align.CENTER)
        slowScrollSpeedScale.set_size_request(200, -1)
        slowScrollSpeedScale.set_value_pos(0)
        slowScrollSpeedScale.set_draw_value(True)

        slowScrollSpeedRow.add_suffix(slowScrollSpeedScale)
        speed2 = Gtk.Adjustment(upper=self.win.settings.speed / 2, step_increment=1, lower=5)
        speed2.set_value(self.win.settings.slowSpeed)
        slowScrollSpeedScale.set_adjustment(speed2)

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


        # backgroundGroup = Adw.PreferencesGroup(title="Background")
        # stylePage.add(backgroundGroup)

        # backgroundColorPickerRow = Adw.ActionRow(title="Background color")
        # backgroundGroup.add(backgroundColorPickerRow)

        # backgroundColorPicker = Gtk.ColorButton(valign = Gtk.Align.CENTER)
        # backgroundColorPicker.set_rgba(self.win.settings.backgroundColor)
        # backgroundColorPickerRow.add_suffix(backgroundColorPicker)

        transparentGroup = Adw.PreferencesGroup(title=gettext.gettext("Transparent"))
        settingsPage.add(transparentGroup)

        transparentRow = Adw.ActionRow(title=gettext.gettext("Make the window transparent"))
        transparentGroup.add(transparentRow)

        transparentSwitch = Gtk.Switch(valign = Gtk.Align.CENTER)
        transparentSwitch.set_active(self.win.transparent)

        transparentRow.add_suffix(transparentSwitch)

        pref.present()

        # backgroundColorPicker.connect("color-set", self.on_background_color_changed)
        highlightColorPicker.connect("color-set", self.on_highlight_color_changed)
        fontColorPicker.connect("color-set", self.on_text_color_changed)
        fontPicker.connect("font-set", self.on_font_changed)
        scrollSpeedScale.connect("value-changed", self.on_speed_changed, speed2)
        slowScrollSpeedScale.connect("value-changed", self.on_slow_speed_changed)
        boldHighlightSwitch.connect("state-set", self.on_bold_highlight_set)

        transparentSwitch.connect("state-set", self.on_transparent_switch_set)

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

    def on_transparent_switch_set(self, switch, arg):
        self.on_transparent_action()

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

    def on_speed_changed(self, sliderWidget, slowSpeedAdj):
        speed1 = sliderWidget.get_value()
        self.win.settings.speed = speed1
        if slowSpeedAdj.get_value() >= speed1 / 2:
            slowSpeedAdj.set_value(speed1 / 2)
            slowSpeedAdj.set_upper(sliderWidget.get_value() / 2)
        else:
            slowSpeedAdj.set_upper(sliderWidget.get_value() / 2)

        self.win.save_app_settings(self.win.settings)

    def on_slow_speed_changed(self, sliderWidget):
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
