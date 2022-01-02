'''This entire file is licensed under MIT.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import gi, inspect
import json 
import subprocess as sp
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GtkLayerShell
from gi.repository import Gdk
from gi.repository import Gio
from pathlib import Path


try:
    gi.require_version('GtkLayerShell', '0.1')
except ValueError:
    import sys
    raise RuntimeError('\n\n' +
        'If you haven\'t installed GTK Layer Shell, you need to point Python to the\n' +
        'library by setting GI_TYPELIB_PATH and LD_LIBRARY_PATH to <build-dir>/src/.\n' +
        'For example you might need to run:\n\n' +
        'GI_TYPELIB_PATH=build/src LD_LIBRARY_PATH=build/src python3 ' + ' '.join(sys.argv))


print("Initializing...")

configDir = str(Path.home()) + "/.config/wonky/"
configJsonPath = str(configDir) + "config.json" 
configCssPath = str(configDir) + "style.css"

css_provider = Gtk.CssProvider()
css_provider.load_from_path(configCssPath)

gtkCtx = Gtk.StyleContext()
screen = Gdk.Screen.get_default()
gtkCtx.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

window = Gtk.Window()
#window.set_size_request(480,640)

GtkLayerShell.init_for_window(window)
# GtkLayerShell.auto_exclusive_zone_enable(window)
GtkLayerShell.set_layer(window,  1)

GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, 5)
GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, 1)
GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, 1)


outerContainer = Gtk.VBox(spacing=6)
window.add(outerContainer)


def render_container(cnt):
    config = json.load(open(configJsonPath))
    for c in cnt.get_children():
      cnt.remove(c)

    for w in config['widgets']:
        print(w)
        match w['type']:
            case 'sh':
                result = sp.run(w['cmd'], capture_output=True)
                label = Gtk.Label()
                labelText = w['fmt'].replace('$OUTPUT', result.stdout.decode('utf-8'))
                label.set_markup(labelText.strip())
                labelCtx = label.get_style_context()
                #label.set_valign(top)
                label.set_valign(Gtk.Align.START)
                label.set_halign(Gtk.Align.START)
                if w['class']:
                    labelCtx.add_class(w['class'])
                cnt.add(label)

render_container(outerContainer)

window.show_all()
window.connect('destroy', Gtk.main_quit)
Gtk.main()

#print(dir(label))

#def on_button1_clicked(self):
#      print("clicked")

#button1 = Gtk.Button(label="Hello")
#button1.connect("clicked", on_button1_clicked)
#outerContainer.pack_start(button1, True, True, 0)

