#
# Copyright 2023 Lorenzo
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

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

from gi.repository import Adw
from gi.repository import Pango, GLib, Gio, cairo

def toHexStr(color):
    text_color = "#{:02X}{:02X}{:02X}".format(
        int(color.red * 255),
        int(color.green * 255),
        int(color.blue * 255)
    )
    return text_color

def save_app_settings(settings):
    schema_id = "com.github.nokse22.teleprompter"
    print("saving")

    # Create a Gio.Settings object for the schema
    gio_settings = Gio.Settings(schema_id)

    gio_settings.set_string("text", toHexStr(settings.textColor))
    gio_settings.set_string("background", toHexStr(settings.backgroundColor))
    gio_settings.set_string("highlight", toHexStr(settings.highlightColor))

    gio_settings.set_string("font", settings.font)

    gio_settings.set_int("speed", settings.speed * 10)
    gio_settings.set_int("slow-speed", settings.slowSpeed * 10)

def on_file_selected(dialog, response, self):
    if response == Gtk.ResponseType.OK:
        # filename = file_obj.get_path() if file_obj else None
        # print("Selected file: {}".format(filename))
        selected_file = dialog.get_file()
        if selected_file:
            file_path = selected_file.get_path()
            try:
                with open(file_path, 'r') as file:
                    file_contents = file.read()
                    self.text_buffer.set_text("\n\n\n\n\n\n\n\n\n" + file_contents + "\n\n\n\n\n\n\n\n\n\n\n")
                    apply_text_tags(self)
                    updateFont(self)
                    start = self.text_buffer.get_start_iter()
                    search_and_mark_highlight(self, start)
            except OSError as e:
                dialog.destroy()
                toast = Adw.Toast()
                toast.set_title("Error reading file")
                toast.set_timeout(1)
                self.overlay.add_toast(toast)

        dialog.destroy()
        toast = Adw.Toast()
        toast.set_title("File successfully opened")
        toast.set_timeout(1)
        self.overlay.add_toast(toast)

    if response == Gtk.ResponseType.CANCEL:
        dialog.destroy()

def show_file_chooser_dialog(self):
    dialog = Gtk.FileChooserDialog(
        title="Open File",
        action=Gtk.FileChooserAction.OPEN,
        transient_for=None
    )
    dialog.add_button("Open", Gtk.ResponseType.OK)
    dialog.add_button("Close", Gtk.ResponseType.CANCEL)

    # Create a filter to display only .txt files
    filter_txt = Gtk.FileFilter()
    filter_txt.set_name("Text files")
    filter_txt.add_pattern("*.txt")
    dialog.add_filter(filter_txt)
    dialog.set_filter(filter_txt)


    dialog.connect("response", on_file_selected, self)
    dialog.show()

def load_app_settings():
    print("loading")
    schema_id = "com.github.nokse22.teleprompter"

    # Create a Gio.Settings object for the schema
    gio_settings = Gio.Settings(schema_id)

    # Retrieve the settings values
    settings = AppSettings()

    color1 = Gdk.RGBA()
    color2 = Gdk.RGBA()
    color3 = Gdk.RGBA()

    color1.parse(gio_settings.get_string("text"))
    settings.textColor = color1

    color2.parse(gio_settings.get_string("background"))
    settings.backgroundColor = color2

    color3.parse(gio_settings.get_string("highlight"))
    settings.highlightColor = color3

    settings.font = gio_settings.get_string("font")

    settings.speed = gio_settings.get_int("speed") / 10
    settings.slowSpeed = gio_settings.get_int("slow-speed") / 10

    print("settings loaded")

    return settings

def autoscroll(self, scrolled_window):
    adjustment = scrolled_window.get_vadjustment()
    adjustment.set_value(adjustment.get_value() + wordPerMinuteToSpeed(self, self.settings.speed))
    scrolled_window.set_vadjustment(adjustment)

    # self.progress_scale_adjustment.set_value((self.adj/adjustment.get_upper() - adjustment.get_lower())*100)

    if not self.playing:
        return 0
    else:
        return 1

def apply_text_tags(self):
    # print("apply tags")

    start_iter = self.text_buffer.get_start_iter()
    end_iter = Gtk.TextIter()

    tag_color1 = Gtk.TextTag()
    tag_color1.set_property("foreground", toHexStr(self.settings.textColor))
    self.text_buffer.get_tag_table().add(tag_color1)

    tag_color2 = Gtk.TextTag()
    tag_color2.set_property("foreground", toHexStr(self.settings.highlightColor))
    self.text_buffer.get_tag_table().add(tag_color2)

    # Get the text buffer's start and end iterators
    start_iter = self.text_buffer.get_start_iter()
    end_iter = self.text_buffer.get_end_iter()

    self.text_buffer.apply_tag(tag_color1, start_iter, end_iter)

def search_and_mark_highlight(self, start):
    end = self.text_buffer.get_end_iter()
    text = "["

    tag_color2 = Gtk.TextTag()
    tag_color2.set_property("foreground", toHexStr(self.settings.highlightColor))
    tag_color2.set_property("weight", Pango.Weight.BOLD)
    self.text_buffer.get_tag_table().add(tag_color2)

    match = start.forward_search(text, 0, end)

    if match is not None:
        match_start, match_end = match
        match_end_highlight = search_end_highligh(self, match_end)
        if match_end_highlight != None:
            self.text_buffer.apply_tag(tag_color2, match_start, match_end_highlight)
        search_and_mark_highlight(self, match_end)

def search_end_highligh(self, start):
    end = self.text_buffer.get_end_iter()

    match = start.forward_search("]", 0, end)

    if match is not None:
        match_start, match_end = match
        return match_end

    return start + 1

def updateFont(self):
    tag = self.text_buffer.create_tag(None, font_desc=Pango.FontDescription(self.settings.font))

    # Apply the tag to the entire text buffer
    self.text_buffer.apply_tag(tag, self.text_buffer.get_start_iter(), self.text_buffer.get_end_iter())

def colorBackground(self):
    css_data = """
        textview {{
            background-color: #242424;
        }}
    """.format(c2 = toHexStr(self.settings.backgroundColor))

    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(css_data, -1)

    # Apply the theme to the GTK app
    context = self.textview.get_style_context()
    context.add_provider(style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def wordPerMinuteToSpeed(self, speed):
    # Split the font string into font properties and size
    font_properties = self.settings.font.split()
    font_size = font_properties[-1]

    # Convert the font size to an integer and increase it by +5 or -5
    font = int(font_size)
    width = self.textview.get_allocation().width
    speed = self.settings.speed * font * 0.04 / width  # self.settings.speed * 4/ ((-font*0.2 + 0.05*width)*font*2.62) # to rework

    return speed

def modifyFont(self, amount):
    # Split the font string into font properties and size
    font_properties = self.settings.font.split()
    font_size = font_properties[-1]

    # Convert the font size to an integer and increase it by +5 or -5
    new_font_size = int(font_size) + amount

    # Update the font size in the font properties list
    font_properties[-1] = str(new_font_size)

    # Construct the updated font string
    self.settings.font = ' '.join(font_properties)

class AppSettings:
    def __init__(self):
        self.font = 'Cantarell 80'
        self.textColor = Gdk.RGBA()
        self.backgroundColor = Gdk.RGBA()
        self.speed = 150
        self.slowSpeed = 50
        self.highlightColor = Gdk.RGBA()

def  on_text_pasted(text_buffer, clipboard, self):
    apply_text_tags(self)
    updateFont(self)

def on_text_inserted(text_buffer, loc, text, lenght, self):
    apply_text_tags(self)
    updateFont(self)
    start = self.text_buffer.get_start_iter()
    search_and_mark_highlight(self, start)

@Gtk.Template(resource_path='/com/github/nokse22/teleprompter/window.ui')
class TeleprompterWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TeleprompterWindow'

    open_button = Gtk.Template.Child("open_button")
    scrolled_window = Gtk.Template.Child("scrolled_window")
    start_button = Gtk.Template.Child("start_button")
    paste_button = Gtk.Template.Child("paste_button")
    overlay = Gtk.Template.Child("overlay")

    playing = False

    settings = AppSettings()

    settings = load_app_settings()

    text_buffer = Gtk.Template.Child("text_buffer")
    textview = Gtk.Template.Child("text_view")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        apply_text_tags(self)
        colorBackground(self)
        updateFont(self)

        self.text_buffer.connect("paste-done", on_text_pasted, self)

        self.text_buffer.connect("insert-text", on_text_inserted, self)

        start = self.text_buffer.get_start_iter()
        search_and_mark_highlight(self, start)

        #self.text_buffer.connect("changed", apply_text_tags, self.text_buffer)
        #update(self)

    @Gtk.Template.Callback("play_button_clicked")
    def bar1(self, *args):
        apply_text_tags(self)
        if not self.playing:
            self.start_button.set_icon_name("media-playback-pause-symbolic")
            self.playing = True

            # Start continuous autoscrolling
            GLib.timeout_add(10, autoscroll, self, self.scrolled_window)
        else:
            self.start_button.set_icon_name("media-playback-start-symbolic")
            self.playing = False
            self.speed = 0

    @Gtk.Template.Callback("open_button_clicked")
    def bar2(self, *args):
        # print("open button clicked")
        show_file_chooser_dialog(self)

    @Gtk.Template.Callback("increase_speed_button_clicked")
    def bar3(self, *args):
        # print("increase speed clicked")
        self.settings.speed += 5
        save_app_settings(self.settings)

        start = self.text_buffer.get_start_iter()
        search_and_mark_highlight(self, start)

    @Gtk.Template.Callback("decrease_speed_button_clicked")
    def bar4(self, *args):
        # print("decrease speed clicked")
        self.settings.speed -= 5
        if self.settings.speed <= 0:
            self.settings.speed = 5
        save_app_settings(self.settings)

    @Gtk.Template.Callback("paste_button_clicked")
    def bar5(self, *args):
        # I spent one entire evening trying to make this work...
        clipboard = Gdk.Display().get_default().get_clipboard()

        def callback(clipboard, res, data):
            text = clipboard.read_text_finish(res)
            self.text_buffer.set_text("\n\n" + text + "\n\n\n\n\n\n\n\n\n")
            apply_text_tags(self)
            updateFont(self)
            start = self.text_buffer.get_start_iter()
            search_and_mark_highlight(self, start)
            toast = Adw.Toast()
            toast.set_title("Pasted Clipboard Content")
            toast.set_timeout(1)
            self.overlay.add_toast(toast)

        data = {}
        res = clipboard.read_text_async(None, callback, data)

    @Gtk.Template.Callback("decrease_font_button_clicked")
    def bar6(self, *args):
        modifyFont(self, -5)
        updateFont(self)
        save_app_settings(self.settings)

    @Gtk.Template.Callback("increase_font_button_clicked")
    def bar7(self, *args):
        modifyFont(self, 5)
        updateFont(self)
        save_app_settings(self.settings)






