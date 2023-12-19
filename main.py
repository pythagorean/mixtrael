import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Pango

class MainWindow(Gtk.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Window configuration
        self.set_default_size(800, 600)
        self.set_title("Chat Interface")

        # Widget instantiation
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scrolled_window1 = Gtk.ScrolledWindow()
        scrolled_window2 = Gtk.ScrolledWindow()

        self.textview1 = Gtk.TextView()
        self.textbuffer1 = self.textview1.get_buffer()

        self.textview2 = Gtk.TextView()
        self.textbuffer2 = self.textview2.get_buffer()

        button_response = Gtk.Button(label="Respond")
        button_clear = Gtk.Button(label="Clear Screen")

        # Signal connection
        button_response.connect("clicked", self.on_button_respond_clicked)
        button_clear.connect("clicked", self.on_button_clear_clicked)

        # Styling
        self.textview1.modify_font(Pango.FontDescription("Monospace 12"))
        self.textview2.modify_font(Pango.FontDescription("Monospace 12"))
        style_context = self.textview1.get_style_context()
        style_context.add_class("dark")
        style_context = self.textview2.get_style_context()
        style_context.add_class("light")

        # Packing
        scrolled_window1.add(self.textview1)
        scrolled_window2.add(self.textview2)
        vbox.pack_start(scrolled_window1, True, True, 0)
        vbox.pack_start(scrolled_window2, True, True, 0)
        hbox = Gtk.Box(spacing=6)
        hbox.pack_start(button_response, False, False, 0)
        hbox.pack_start(button_clear, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        self.add(vbox)

    @staticmethod
    def on_button_respond_clicked(*args):
        # TODO: Process user input and populate TextView2 with generated response
        pass

    @staticmethod
    def on_button_clear_clicked(*args):
        # Clear both TextViews
        buffer1 = MainWindow.textview1.get_buffer()
        buffer2 = MainWindow.textview2.get_buffer()
        buffer1.set_text("")
        buffer2.set_text("")

if __name__ == "__main__":
    win = MainWindow()
    win.show_all()
    Gtk.main()
