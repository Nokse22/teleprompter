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

from gi.repository import Gtk, Gdk

from gi.repository import Adw
from gi.repository import Pango, GLib, Gio

from gettext import gettext as _


class AppSettings:
    def __init__(self):
        self.font = 'Cantarell 40'
        self.textColor = Gdk.RGBA()
        self.textColor.parse("#62A0EA")
        self.speed = 150
        self.highlightColor = Gdk.RGBA()
        self.highlightColor.parse("#ED333B")
        self.boldHighlight = True


@Gtk.Template(resource_path='/io/github/nokse22/teleprompter/window.ui')
class TeleprompterWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TeleprompterWindow'

    scrolled_window = Gtk.Template.Child("scrolled_window")
    start_button1 = Gtk.Template.Child("start_button1")
    fullscreen_button = Gtk.Template.Child("fullscreen_button")
    overlay = Gtk.Template.Child("overlay")
    sidebar_controls = Gtk.Template.Child("sidebar_controls")

    playing = False
    fullscreened = False

    text_buffer = Gtk.Template.Child("text_buffer")
    textview = Gtk.Template.Child("text_view")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.saved_settings = Gio.Settings("io.github.nokse22.teleprompter")

        self.settings = AppSettings()
        self.settings = self.load_app_settings()

        self.text_buffer.connect("paste-done", self.on_text_pasted)

        self.text_buffer.connect("changed", self.on_text_inserted, "", 0, 0)

        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)

        self.apply_text_tags()
        self.updateFont()

        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)

    def on_text_pasted(self, text_buffer, clipboard):
        self.apply_text_tags()
        self.updateFont()

    def on_text_inserted(self, text_buffer, loc, text, length):
        self.apply_text_tags()
        self.updateFont()
        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)

    def toHexStr(self, color):
        text_color = "#{:02X}{:02X}{:02X}".format(
            int(color.red * 255),
            int(color.green * 255),
            int(color.blue * 255)
        )
        return text_color

    def save_app_settings(self, settings):
        self.saved_settings.set_string(
            "text", self.toHexStr(settings.textColor))
        self.saved_settings.set_string(
            "highlight", self.toHexStr(settings.highlightColor))

        self.saved_settings.set_string(
            "font", settings.font)

        self.saved_settings.set_int(
            "speed", settings.speed * 10)

        self.saved_settings.set_boolean(
            "bold-highlight", settings.boldHighlight)

    def show_file_chooser_dialog(self):
        dialog = Gtk.FileDialog(
            title=_("Open File"),
        )

        dialog.open(self, None, self.on_open_file_response)

    def on_open_file_response(self, dialog, response):
        try:
            file = dialog.open_finish(response)
            if file:
                file_path = file.get_path()
                try:
                    with open(file_path, 'r') as file:
                        file_contents = file.read()
                        self.text_buffer.set_text(file_contents)
                        self.apply_text_tags()
                        self.updateFont()
                        start = self.text_buffer.get_start_iter()
                        self.search_and_mark_highlight(start)
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

    def load_app_settings(self):
        settings = AppSettings()

        color1 = Gdk.RGBA()
        color2 = Gdk.RGBA()
        color3 = Gdk.RGBA()

        color1.parse(self.saved_settings.get_string("text"))
        settings.textColor = color1

        color3.parse(self.saved_settings.get_string("highlight"))
        settings.highlightColor = color3

        settings.font = self.saved_settings.get_string("font")

        settings.speed = self.saved_settings.get_int("speed") / 10

        settings.boldHighlight = self.saved_settings.get_boolean(
            "bold-highlight")

        return settings

    def autoscroll(self, scrolled_window):
        adjustment = scrolled_window.get_vadjustment()
        adjustment.set_value(
            adjustment.get_value() + self.wordPerMinuteToSpeed(
                self.settings.speed))
        scrolled_window.set_vadjustment(adjustment)

        if (adjustment.get_value() ==
                adjustment.get_upper() - adjustment.get_page_size()):
            self.playing = False
            self.start_button1.set_icon_name("media-playback-start-symbolic")
            return 0

        if not self.playing:
            return 0
        else:
            return 1

    def apply_text_tags(self):
        start_iter = self.text_buffer.get_start_iter()
        end_iter = Gtk.TextIter()

        tag_color1 = Gtk.TextTag()
        tag_color1.set_property(
            "foreground", self.toHexStr(self.settings.textColor))
        self.text_buffer.get_tag_table().add(tag_color1)

        tag_color2 = Gtk.TextTag()
        tag_color2.set_property(
            "foreground", self.toHexStr(self.settings.highlightColor))
        self.text_buffer.get_tag_table().add(tag_color2)

        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()

        self.text_buffer.apply_tag(tag_color1, start_iter, end_iter)

    def search_and_mark_highlight(self, start):
        end = self.text_buffer.get_end_iter()
        text = "["

        tag_color2 = Gtk.TextTag()
        tag_color2.set_property(
            "foreground", self.toHexStr(self.settings.highlightColor))

        if self.settings.boldHighlight:
            tag_color2.set_property("weight", Pango.Weight.BOLD)

        self.text_buffer.get_tag_table().add(tag_color2)

        match = start.forward_search(text, 0, end)

        if match is not None:
            match_start, match_end = match
            match_end_highlight = self.search_end_highlight(match_end)
            if match_end_highlight is not None:
                self.text_buffer.apply_tag(
                    tag_color2, match_start, match_end_highlight)
            self.search_and_mark_highlight(match_end)

    def search_end_highlight(self, start):
        end = self.text_buffer.get_end_iter()

        # Perform forward search for "]" from the starting position
        match_right = start.forward_search("]", Gtk.TextSearchFlags(0), end)

        # Perform forward search for "[" from the starting position
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

    def updateFont(self):
        tag = self.text_buffer.create_tag(
            None, font_desc=Pango.FontDescription(self.settings.font))

        # Apply the tag to the entire text buffer
        self.text_buffer.apply_tag(
            tag, self.text_buffer.get_start_iter(), self.text_buffer.get_end_iter())

    def wordPerMinuteToSpeed(self, speed):
        font_properties = self.settings.font.split()
        font_size = font_properties[-1]

        font = int(font_size)
        width = self.textview.get_allocation().width
        speed = self.settings.speed * font * 0.2 / width

        if speed <= 0.25:
            speed = 0.25

        return speed

    def modifyFont(self, amount):
        # Split the font string into font properties and size
        font_properties = self.settings.font.split()
        font_size = font_properties[-1]

        if int(font_size) + amount > 10:
            new_font_size = int(font_size) + amount
        else:
            new_font_size = 10

        # Update the font size in the font properties list
        font_properties[-1] = str(new_font_size)

        # Construct the updated font string
        self.settings.font = ' '.join(font_properties)

    @Gtk.Template.Callback("play_button_clicked")
    def play(self, *args):
        # print("play")
        if not self.playing:
            self.start_button1.set_icon_name("media-playback-pause-symbolic")
            self.playing = True

            # Start continuous autoscrolling
            GLib.timeout_add(10, self.autoscroll, self.scrolled_window)
        else:
            self.start_button1.set_icon_name("media-playback-start-symbolic")
            self.playing = False
            self.speed = 0

    @Gtk.Template.Callback("open_button_clicked")
    def open_button_clicked(self, *args):
        self.show_file_chooser_dialog()

    @Gtk.Template.Callback("increase_speed_button_clicked")
    def increase_speed_button_clicked(self, *args):
        self.settings.speed += 10

    @Gtk.Template.Callback("decrease_speed_button_clicked")
    def decrease_speed_button_clicked(self, *args):
        self.settings.speed -= 10
        if self.settings.speed <= 40:
            self.settings.speed = 40

    @Gtk.Template.Callback("paste_button_clicked")
    def paste_button_clicked(self, *args):
        clipboard = Gdk.Display().get_default().get_clipboard()

        def callback(clipboard, res, data):
            text = clipboard.read_text_finish(res)
            self.text_buffer.set_text(text)
            self.apply_text_tags()
            self.updateFont()
            start = self.text_buffer.get_start_iter()
            self.search_and_mark_highlight(start)
            toast = Adw.Toast()
            toast.set_title("Pasted Clipboard Content")
            toast.set_timeout(1)
            self.overlay.add_toast(toast)

        data = {}
        clipboard.read_text_async(None, callback, data)

    @Gtk.Template.Callback("decrease_font_button_clicked")
    def decrease_font_button_clicked(self, *args):
        self.modifyFont(-5)
        self.updateFont()
        self.apply_text_tags()
        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)
        self.save_app_settings(self.settings)

    @Gtk.Template.Callback("increase_font_button_clicked")
    def increase_font_button_clicked(self, *args):
        self.modifyFont(5)
        self.updateFont()
        self.apply_text_tags()
        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)
        self.save_app_settings(self.settings)

    @Gtk.Template.Callback("fullscreen_button_clicked")
    def toggle_fullscreen(self, *args):
        if self.fullscreened:
            self.unfullscreen()
            self.fullscreen_button.set_icon_name("view-fullscreen-symbolic")
            self.fullscreened = False
        else:
            self.fullscreen()
            self.fullscreen_button.set_icon_name("view-restore-symbolic")
            self.fullscreened = True

    @Gtk.Template.Callback("on_apply_breakpoint")
    def on_apply_breakpoint(self, *args):
        self.sidebar_controls.remove_css_class("card")
        self.sidebar_controls.remove_css_class("overlay_toolbar")

    @Gtk.Template.Callback("on_unapply_breakpoint")
    def on_unapply_breakpoint(self, *args):
        self.sidebar_controls.add_css_class("card")
        self.sidebar_controls.add_css_class("overlay_toolbar")
