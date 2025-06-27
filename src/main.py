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

from gi.repository import Gtk, Gio, Adw, GLib
from .window import TeleprompterWindow
from .osc_server import OSCServer

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

        # OSC server
        self.osc_server = None
        
        # Action for toggling OSC
        self.create_action('toggle-osc', self.on_toggle_osc)

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

        self.win.scroll_text_view.hmirror = False
        self.win.scroll_text_view.vmirror = False

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

    def on_toggle_osc(self, *args):
        """Toggle OSC server"""
        if self.osc_server and self.osc_server.running:
            self.osc_server.stop()
            self.osc_server = None
        else:
            osc_port = self.saved_settings.get_int("osc-port")
            if osc_port == 0:
                osc_port = 7400  # Default port
            
            self.osc_server = OSCServer(self.win, osc_port)
            self.osc_server.start()

    def do_activate(self):
        self.win = self.props.active_window
        if not self.win:
            self.win = TeleprompterWindow(application=self)
            self.create_action(
                'play', self.win.play, ['<primary>space'])
            self.create_action(
                'fullscreen', self.win.toggle_fullscreen, ['F11'])
            
            # Auto-start OSC server if enabled in settings
            if self.saved_settings.get_boolean("osc-autostart"):
                self.on_toggle_osc()
                
        self.win.present()

    def do_shutdown(self):
        """Cleanup when application terminates"""
        if self.osc_server:
            self.osc_server.stop()
        super().do_shutdown()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name='Teleprompter',
            application_icon='io.github.nokse22.teleprompter',
            developer_name='Nokse',
            version='1.1.0',
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

        bold_highlight_row = Adw.SwitchRow(title=_("Bold Highlight"))
        bold_highlight_row.set_active(self.win.settings.bold_highlight)
        text_group.add(bold_highlight_row)

        font_color_picker_row = Adw.ActionRow(title=_("Font color"))
        text_group.add(font_color_picker_row)

        font_picker_row = Adw.ActionRow(title=_("Font"))
        text_group.add(font_picker_row)

        font_picker = Gtk.FontButton(valign=Gtk.Align.CENTER)
        font_picker.set_font(self.win.settings.font)
        font_picker_row.add_suffix(font_picker)

        font_color_picker = Gtk.ColorButton(valign=Gtk.Align.CENTER)
        font_color_picker.set_rgba(self.win.settings.text_color)
        font_color_picker_row.add_suffix(font_color_picker)

        # New OSC settings page
        osc_page = Adw.PreferencesPage(title=_("OSC Remote Control"))
        osc_page.set_icon_name("network-wireless-symbolic")
        pref.add(osc_page)

        osc_group = Adw.PreferencesGroup(
            title=_("OSC Settings"),
            description=_("Open Sound Control allows remote control of the teleprompter"))
        osc_page.add(osc_group)

        # OSC server toggle
        osc_enable_row = Adw.SwitchRow(
            title=_("Enable OSC Server"),
            subtitle=_("Allow remote control via OSC protocol"))
        osc_enable_row.set_active(self.osc_server and self.osc_server.running)
        osc_group.add(osc_enable_row)

        # OSC port
        osc_port_row = Adw.SpinRow(
            title=_("OSC Port"),
            subtitle=_("UDP port for OSC communication"))
        osc_group.add(osc_port_row)

        port_adj = Gtk.Adjustment(upper=65535, step_increment=1, lower=1024)
        current_port = self.saved_settings.get_int("osc-port")
        if current_port == 0:
            current_port = 7400
        port_adj.set_value(current_port)
        osc_port_row.set_adjustment(port_adj)

        # OSC auto-start
        osc_autostart_row = Adw.SwitchRow(
            title=_("Auto-start OSC Server"),
            subtitle=_("Start OSC server automatically when app launches"))
        osc_autostart_row.set_active(self.saved_settings.get_boolean("osc-autostart"))
        osc_group.add(osc_autostart_row)

        # OSC commands information
        osc_info_group = Adw.PreferencesGroup(
            title=_("OSC Commands"),
            description=_("Available OSC addresses for remote control"))
        osc_page.add(osc_info_group)

        commands_text = """/teleprompter/play - Start playback
/teleprompter/pause - Pause playback  
/teleprompter/stop - Stop and reset position
/teleprompter/speed [float] - Set speed in WPM
/teleprompter/fontsize [int] - Set font size
/teleprompter/position [float] - Set position (0.0-1.0)
/teleprompter/fullscreen [bool] - Toggle fullscreen
/teleprompter/text [string] - Set text content
/teleprompter/load [string] - Load text file
/teleprompter/mirror/horizontal [bool] - Mirror horizontally
/teleprompter/mirror/vertical [bool] - Mirror vertically
/teleprompter/reset - Reset all settings
/teleprompter/status - Get current status"""

        osc_commands_row = Adw.ActionRow(title=_("Commands"))
        osc_info_group.add(osc_commands_row)

        commands_label = Gtk.Label(
            label=commands_text,
            selectable=True,
            wrap=True,
            margin_start=12,
            margin_end=12,
            margin_top=6,
            margin_bottom=6)
        commands_label.add_css_class("caption")
        osc_commands_row.set_child(commands_label)

        # Connect OSC settings handlers
        osc_enable_row.connect("notify::active", self.on_osc_enable_changed)
        port_adj.connect("value-changed", self.on_osc_port_changed)
        osc_autostart_row.connect("notify::active", self.on_osc_autostart_changed)

        pref.present(self.win)

        highlight_color_picker.connect(
            "color-set", self.on_highlight_color_changed)
        font_color_picker.connect(
            "color-set", self.on_text_color_changed)
        font_picker.connect(
            "font-set", self.on_font_changed)
        speed_adj.connect(
            "value-changed", self.on_speed_changed)
        bold_highlight_row.connect(
            "notify::active", self.on_bold_highlight_set)

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_text_color_changed(self, colorWidget):
        self.win.settings.text_color = colorWidget.get_rgba()

        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

    def on_highlight_color_changed(self, colorWidget):
        self.win.settings.highlight_color = colorWidget.get_rgba()

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

    def on_bold_highlight_set(self, switch, *args):
        self.win.settings.bold_highlight = switch.get_active()

        self.win.update_font()
        self.win.apply_text_tags()
        start = self.win.text_buffer.get_start_iter()
        self.win.search_and_mark_highlight(start)
        self.win.save_app_settings(self.win.settings)

    def on_osc_enable_changed(self, switch, *args):
        """Handle OSC server enable/disable"""
        if switch.get_active():
            if not (self.osc_server and self.osc_server.running):
                self.on_toggle_osc()
        else:
            if self.osc_server and self.osc_server.running:
                self.on_toggle_osc()

    def on_osc_port_changed(self, port_adj):
        """Handle OSC port change"""
        port = int(port_adj.get_value())
        self.saved_settings.set_int("osc-port", port)
        
        # Restart server if it's running
        if self.osc_server and self.osc_server.running:
            self.osc_server.stop()
            self.osc_server = OSCServer(self.win, port)
            self.osc_server.start()

    def on_osc_autostart_changed(self, switch, *args):
        """Handle OSC auto-start change"""
        self.saved_settings.set_boolean("osc-autostart", switch.get_active())


def main(version):
    """The application's entry point."""
    app = TeleprompterApplication()
    return app.run(sys.argv)