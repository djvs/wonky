import gi 
import json 
#import asyncio, threading
import subprocess as sp
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GtkLayerShell
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from pathlib import Path

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
GtkLayerShell.set_layer(window,    1)

GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, 5)
GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, 1)
GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, 1)

outerContainer = Gtk.VBox(spacing=6)
window.add(outerContainer)

# initial config load
config = json.load(open(configJsonPath))

widgetref = {}

def render_container():
    #print("Loop...")
    #print(dir(outerContainer))
    config = json.load(open(configJsonPath))

    for i, w in enumerate(config['widgets']):
        si = str(i)
        if si in widgetref:
            label = widgetref[si]
        else:
            label = Gtk.Label()
            label.set_valign(Gtk.Align.START)
            label.set_halign(Gtk.Align.START)
            if "class" in w:
                labelCtx = label.get_style_context()
                labelCtx.add_class(w['class'])

        # assign text
        match w['type']:
            case 'spacer':
                labelText = " "
                label.set_markup(labelText)

            case 'text':
                labelText = w['text']
                label.set_markup(labelText)

            case 'sh':
                try:
                    result = sp.run(w['cmd'], capture_output=True)
                    labelText = w['fmt'].replace('$OUTPUT', result.stdout.decode('utf-8'))
                    label.set_markup(labelText.strip())
                except:
                    labelText = "Command #" + si + " failed: " + str(w['cmd'])
                    label.set_markup(labelText)

        # add if not previously initialized
        if not si in widgetref:
            print("Initializing widget #", si)
            outerContainer.add(label)
            widgetref[si] = label
    return True

window.connect('destroy', Gtk.main_quit)

render_container()
GLib.timeout_add(config['interval'], render_container)
window.show_all()
Gtk.main()

#print(dir(label))

#def on_button1_clicked(self):
#        print("clicked")

#button1 = Gtk.Button(label="Hello")
#button1.connect("clicked", on_button1_clicked)
#outerContainer.pack_start(button1, True, True, 0)

