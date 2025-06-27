# scroll_text_view.py
#
# Copyright 2024 Nokse22
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
from gi.repository import Gtk, Adw, GObject, Graphene


class TeleprompterTextView(Adw.Bin):
    __gtype_name__ = "TeleprompterTextView"

    def __init__(self):
        super().__init__()

        self._text_view = Gtk.TextView(
            bottom_margin=300,
            top_margin=50,
            margin_start=12,
            margin_end=12,
            pixels_above_lines=6,
            pixels_below_lines=6,
            vexpand=True,
            wrap_mode=Gtk.WrapMode.WORD_CHAR,
        )

        self._text_view.add_css_class("transparent")

        self.set_child(self._text_view)

        self._mirror = False

    def do_snapshot(self, snapshot):
        width = self.get_allocation().width

        if self._mirror:
            snapshot.translate(Graphene.Point.alloc().init(width, 0))
            snapshot.scale(-1, 1)

        self.snapshot_child(self._text_view, snapshot)


@Gtk.Template(resource_path="/io/github/nokse22/teleprompter/gtk/scroll_text_view.ui")
class TeleprompterScrollTextView(Adw.Bin):
    __gtype_name__ = "TeleprompterScrollTextView"

    text_view = Gtk.Template.Child()
    scrolled_window = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self._mirror = False

        self.scrolled_window.get_vscrollbar().set_margin_top(40)

    def do_snapshot(self, snapshot):
        height = self.get_allocation().height

        if self._mirror:
            snapshot.translate(Graphene.Point.alloc().init(0, height))
            snapshot.scale(1, -1)

        self.snapshot_child(self.scrolled_window, snapshot)

    @GObject.Property(type=bool, default=False)
    def hmirror(self):
        return self.text_view._mirror

    @hmirror.setter
    def hmirror(self, value):
        self.text_view._mirror = value

    @GObject.Property(type=bool, default=False)
    def vmirror(self):
        return self._mirror

    @vmirror.setter
    def vmirror(self, value):
        self._mirror = value

        if value:
            self.scrolled_window.get_vscrollbar().set_margin_top(0)
            self.scrolled_window.get_vscrollbar().set_margin_bottom(40)
        else:
            self.scrolled_window.get_vscrollbar().set_margin_top(40)
            self.scrolled_window.get_vscrollbar().set_margin_bottom(0)

    def get_buffer(self):
        return self.text_view._text_view.get_buffer()

    def get_scrolled_window(self):
        return self.scrolled_window

    def get_width(self):
        return self.text_view._text_view.get_allocation().width
