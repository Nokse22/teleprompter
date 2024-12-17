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

from gi.repository import Gtk, Gio, Adw, GLib
from .window import TeleprompterWindow

import gettext
from gettext import gettext as _

from os import path

LOCALE_DIR = path.join(
    path.dirname(__file__).split('teleprompter')[0], 'locale')
gettext.bindtextdomain('teleprompter', LOCALE_DIR)
gettext.textdomain('teleprompter')


class TeleprompterApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.teleprompter',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action(
            'quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action(
            'about', self.on_about_action)
        self.create_action(
            'preferences', self.on_preferences_action, ['<primary>comma'])

        self.saved_settings = Gio.Settings("io.github.nokse22.teleprompter")

        theme_action = Gio.SimpleAction.new_stateful(
            "theme",
            GLib.VariantType.new("s"),
            GLib.Variant("s", self.saved_settings.get_string("theme")),
        )
        theme_action.connect("activate", self.on_theme_setting_changed)
        self.add_action(theme_action)

        self.vmirror_action = Gio.SimpleAction.new_stateful(
            "vmirror",
            None,
            GLib.Variant("b", self.saved_settings.get_boolean("vmirror"))
        )
        self.vmirror_action.connect("activate", self.on_vmirror)
        self.set_accels_for_action("app.vmirror", ['<primary><shift>V'])
        self.add_action(self.vmirror_action)

        self.hmirror_action = Gio.SimpleAction.new_stateful(
            "hmirror",
            None,
            GLib.Variant("b", self.saved_settings.get_boolean("hmirror"))
        )
        self.hmirror_action.connect("activate", self.on_hmirror)
        self.set_accels_for_action("app.hmirror", ['<primary><shift>H'])
        self.add_action(self.hmirror_action)

        self.create_action(
            'reset-mirrors', self.on_reset_mirrors, ['<primary><shift>R'])

        self.update_theme()

    def on_vmirror(self, action, state):
        new_state = not action.get_state().get_boolean()
        action.set_state(GLib.Variant.new_boolean(new_state))
        self.saved_settings.set_boolean("vmirror", new_state)

        self.win.scroll_text_view.vmirror = new_state

    def on_hmirror(self, action, state):
        new_state = not action.get_state().get_boolean()
        action.set_state(GLib.Variant.new_boolean(new_state))
        self.saved_settings.set_boolean("hmirror", new_state)

        self.win.scroll_text_view.hmirror = new_state

    def on_reset_mirrors(self, *_args):
        self.vmirror_action.set_state(GLib.Variant.new_boolean(False))
        self.hmirror_action.set_state(GLib.Variant.new_boolean(False))

    def on_theme_setting_changed(self, action, state):
        action.set_state(state)
        self.saved_settings.set_string("theme", state.get_string())

        self.update_theme()

    def update_theme(self):
        manager = Adw.StyleManager().get_default()
        match self.saved_settings.get_string("theme"):
            case "follow":
                manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
            case "light":
                manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            case "dark":
                manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.win = self.props.active_window
        if not self.win:
            self.win = TeleprompterWindow(application=self)
            self.create_action(
                'play', self.win.play, ['<primary>space'])
            self.create_action(
                'fullscreen', self.win.toggle_fullscreen, ['F11'])
        self.win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name='Teleprompter',
            application_icon='io.github.nokse22.teleprompter',
            developer_name='Nokse',
            version='1.0.1',
            developers=['Nokse'],
            license_type="GTK_LICENSE_GPL_3_0",
            issue_url='https://github.com/Nokse22/teleprompter/issues',
            website='https://github.com/Nokse22/teleprompter',
            copyright='© 2023 Noske')
        # Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_("translator-credits"))
        about.present(self.props.active_window)

    def on_preferences_action(self, *args):
        """Callback for the app.preferences action."""

        pref = Adw.PreferencesDialog()

        preferences_page = Adw.PreferencesPage(title=_("Generals"))
        preferences_page.set_icon_name("applications-system-symbolic")
        pref.add(preferences_page)

        scroll_settings_group = Adw.PreferencesGroup(
            title=_("Scroll Settings"))
        preferences_page.add(scroll_settings_group)

        scroll_speed_row = Adw.SpinRow(
            title=_("Scroll Speed"),
            subtitle=_("In words per minute (approximately)"))
        scroll_settings_group.add(scroll_speed_row)

        speed_adj = Gtk.Adjustment(upper=200, step_increment=1, lower=10)
        speed_adj.set_value(self.win.settings.speed)
        scroll_speed_row.set_adjustment(speed_adj)

        text_group = Adw.PreferencesGroup(title=_("Text"))
        preferences_page.add(text_group)

        highlight_color_picker_row = Adw.ActionRow(
            title=_("Highlight color"))
        text_group.add(highlight_color_picker_row)

        highlight_color_picker = Gtk.ColorButton(valign=Gtk.Align.CENTER)
        highlight_color_picker.set_rgba(self.win.settings.highlight_color)
        highlight_color_picker_row.add_suffix(highlight_color_picker)

        bold_highlight_row = Adw.ActionRow(title=_("Bold Highlight"))
        text_group.add(bold_highlight_row)

        bold_highlight_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        bold_highlight_switch.set_active(self.win.settings.bold_highlight)

        bold_highlight_row.add_suffix(bold_highlight_switch)

        font_color_picker_row = Adw.ActionRow(title=_("Font color"))
        text_group.add(font_color_picker_row)

        font_picker_row = Adw.ActionRow(title=_("Font"))
        text_group.add(font_picker_row)

        font_picker = Gtk.FontButton(valign=Gtk.Align.CENTER)
        font_picker.set_font(self.win.settings.font)
        font_picker_row.add_suffix(font_picker)

        font_color_picker = Gtk.ColorButton(valign=Gtk.Align.CENTER)
        font_color_picker.set_rgba(self.win.settings.textColor)
        font_color_picker_row.add_suffix(font_color_picker)

        pref.present(self.win)

        highlight_color_picker.connect(
            "color-set", self.on_highlight_color_changed)
        font_color_picker.connect(
            "color-set", self.on_text_color_changed)
        font_picker.connect(
            "font-set", self.on_font_changed)
        speed_adj.connect(
            "value-changed", self.on_speed_changed)
        bold_highlight_switch.connect(
            "state-set", self.on_bold_highlight_set)

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
        self.win.settings.backgroundColor = colorWidget.get_rgba()

    def on_text_color_changed(self, colorWidget):
        self.win.settings.textColor = colorWidget.get_rgba()

        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

    def on_highlight_color_changed(self, colorWidget):
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

        font_properties[-1] = str(new_font_size)

        self.win.settings.font = ' '.join(font_properties)

        self.win.update_font()
        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

    def on_speed_changed(self, speed_adj):
        speed = speed_adj.get_value()
        self.win.settings.speed = speed

        self.saved_settings.set_int("speed", speed * 10)

    def on_bold_highlight_set(self, switch, foo):
        self.win.settings.bold_highlight_row = not switch.get_state()

        self.win.update_font()
        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)


def main(version):
    """The application's entry point."""
    app = TeleprompterApplication()
    return app.run(sys.argv)
