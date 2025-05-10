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

from gi.repository import Gtk, Gdk, Pango, GLib, Gio, Adw

from .scroll_text_view import TeleprompterScrollTextView

from gettext import gettext as _


class AppSettings:
    def __init__(self):
        self.font = 'Cantarell 40'
        self.text_color = Gdk.RGBA()
        self.text_color.parse("#62A0EA")
        self.speed = 150
        self.highlight_color = Gdk.RGBA()
        self.highlight_color.parse("#ED333B")
        self.bold_highlight = True


@Gtk.Template(resource_path='/io/github/nokse22/teleprompter/gtk/window.ui')
class TeleprompterWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TeleprompterWindow'

    scroll_text_view = Gtk.Template.Child()
    start_button = Gtk.Template.Child()
    fullscreen_button = Gtk.Template.Child()
    overlay = Gtk.Template.Child()
    title_widget = Gtk.Template.Child()

    playing = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.saved_settings = Gio.Settings("io.github.nokse22.teleprompter")

        self.settings = AppSettings()
        self.settings = self.load_app_settings()

        self.text_buffer = self.scroll_text_view.get_buffer()
        self.scrolled_window = self.scroll_text_view.get_scrolled_window()

        self.scroll_text_view.hmirror = self.saved_settings.get_boolean("hmirror")
        self.scroll_text_view.vmirror = self.saved_settings.get_boolean("vmirror")

        self.text_buffer.connect("paste-done", self.on_text_pasted)
        self.text_buffer.connect("changed", self.on_text_inserted, "", 0, 0)

        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)

        self.apply_text_tags()
        self.update_font()

        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)

        self.scroll_text_view.get_scrolled_window().get_vadjustment().connect(
            "value-changed", self.on_scroll_changed)

    def on_scroll_changed(self, adjustment):
        if adjustment.get_value() == 0:
            self.title_widget.set_visible(True)
        else:
            self.title_widget.set_visible(False)

    def on_text_pasted(self, text_buffer, clipboard):
        self.apply_text_tags()
        self.update_font()

    def on_text_inserted(self, text_buffer, loc, text, length):
        self.apply_text_tags()
        self.update_font()
        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)

    def color_to_hex(self, color):
        text_color = "#{:02X}{:02X}{:02X}".format(
            int(color.red * 255),
            int(color.green * 255),
            int(color.blue * 255)
        )
        return text_color

    def save_app_settings(self, settings):
        self.saved_settings.set_string(
            "text", self.color_to_hex(settings.text_color))
        self.saved_settings.set_string(
            "highlight", self.color_to_hex(settings.highlight_color))

        self.saved_settings.set_string(
            "font", settings.font)

        self.saved_settings.set_int(
            "speed", settings.speed * 10)

        self.saved_settings.set_boolean(
            "bold-highlight", settings.bold_highlight)

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
                        self.update_font()
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
        color3 = Gdk.RGBA()

        color1.parse(self.saved_settings.get_string("text"))
        settings.text_color = color1

        color3.parse(self.saved_settings.get_string("highlight"))
        settings.highlight_color = color3

        settings.font = self.saved_settings.get_string("font")

        settings.speed = self.saved_settings.get_int("speed") / 10

        settings.bold_highlight = self.saved_settings.get_boolean(
            "bold-highlight")

        return settings

    def autoscroll(self, scrolled_window):
        adjustment = scrolled_window.get_vadjustment()
        adjustment.set_value(
            adjustment.get_value() + self.wpm_to_speed(self.settings.speed))
        scrolled_window.set_vadjustment(adjustment)

        if (adjustment.get_value() ==
                adjustment.get_upper() - adjustment.get_page_size()):
            self.playing = False
            self.start_button.set_icon_name("media-playback-start-symbolic")
            return False

        if not self.playing:
            return False
        else:
            return True

    def apply_text_tags(self):
        start_iter = self.text_buffer.get_start_iter()
        end_iter = Gtk.TextIter()

        tag_color1 = Gtk.TextTag()
        tag_color1.set_property(
            "foreground", self.color_to_hex(self.settings.text_color))
        self.text_buffer.get_tag_table().add(tag_color1)

        tag_color2 = Gtk.TextTag()
        tag_color2.set_property(
            "foreground", self.color_to_hex(self.settings.highlight_color))
        self.text_buffer.get_tag_table().add(tag_color2)

        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()

        self.text_buffer.apply_tag(tag_color1, start_iter, end_iter)

    def search_and_mark_highlight(self, start):
        end = self.text_buffer.get_end_iter()
        text = "["

        tag_color2 = Gtk.TextTag()
        tag_color2.set_property(
            "foreground", self.color_to_hex(self.settings.highlight_color))

        if self.settings.bold_highlight:
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

    def update_font(self):
        tag = self.text_buffer.create_tag(
            None, font_desc=Pango.FontDescription(self.settings.font))

        self.text_buffer.apply_tag(
            tag,
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter())

    def wpm_to_speed(self, speed):
        font_properties = self.settings.font.split()
        font_size = font_properties[-1]

        font = int(font_size)
        width = self.scroll_text_view.get_width()
        speed = self.settings.speed * font * 0.2 / width

        if speed <= 0.25:
            speed = 0.25

        return speed

    def change_font_size(self, amount):
        font_properties = self.settings.font.split()
        font_size = font_properties[-1]

        if int(font_size) + amount > 10:
            new_font_size = int(font_size) + amount
        else:
            new_font_size = 10

        font_properties[-1] = str(new_font_size)

        self.settings.font = ' '.join(font_properties)

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
            self.update_font()
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
        self.change_font_size(-5)
        self.update_font()
        self.apply_text_tags()
        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)
        self.save_app_settings(self.settings)

    @Gtk.Template.Callback("increase_font_button_clicked")
    def increase_font_button_clicked(self, *args):
        self.change_font_size(5)
        self.update_font()
        self.apply_text_tags()
        start = self.text_buffer.get_start_iter()
        self.search_and_mark_highlight(start)
        self.save_app_settings(self.settings)

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
