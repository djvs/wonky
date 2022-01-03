#!/usr/bin/env python3 

import gi, json, time, subprocess as sp
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GtkLayerShell
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from pathlib import Path

print("Initializing...")

homeDir = str(Path.home())
configDir = homeDir + "/.config/wonky/"
configJsonPath = str(configDir) + "config.json" 
configCssPath = str(configDir) + "style.css"

config = json.load(open(configJsonPath))

css_provider = Gtk.CssProvider()
css_provider.load_from_path(configCssPath)

gtkCtx = Gtk.StyleContext()
screen = Gdk.Screen.get_default()
gtkCtx.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

window = Gtk.Window()

GtkLayerShell.init_for_window(window)

if "exclusive" in config:
    GtkLayerShell.auto_exclusive_zone_enable(window) # Optional 

GtkLayerShell.set_layer(window, 1)

GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, 5)
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, 5)
GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, 1)
GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, 1)
GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.BOTTOM, 1)

outerContainer = Gtk.Box(spacing=6,orientation=Gtk.Orientation.VERTICAL)
window.add(outerContainer)

state = {
    "widgets": {},
}

def render_container():
    #print("Loop...")
    #print(dir(outerContainer))
    try:
        config = json.load(open(configJsonPath))
    except:
        print("config.json is malformed!")
        return True

    for i, w in enumerate(config['widgets']):
        si = w['id']
        currentTime = time.time()
        if si in state['widgets']:
            initializing = False
            ref = state["widgets"][si] 
            label = state["widgets"][si]['widget']
            timeDiff = currentTime - ref["lastRun"]
            if "interval" in w and "lastRun" in ref and timeDiff < w["interval"]:
                #print("skipping", currentTime, timeDiff, w)
                continue
        else:
            initializing = True
            labelCnt = Gtk.Box()
            label = Gtk.Label()
            labelCnt.add(label)
            label.set_valign(Gtk.Align.START)
            label.set_halign(Gtk.Align.START)
            if "maxWidthChars" in w:
                print("Setting max width to", w['maxWidthChars'])
                label.set_line_wrap(True)
                label.set_max_width_chars(w['maxWidthChars'])
            if "class" in w:
                labelCtx = label.get_style_context()
                labelCtx.add_class(w['class'])
            state["widgets"][si] = { "widget": label }
            ref = state["widgets"][si]
            ref['cnt'] = labelCnt
            print("Initializing widget...")

        ref['lastRun'] = currentTime
        

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
                    cmd = w["cmd"].replace("$HOME", homeDir)
                    result = sp.Popen(cmd, shell=True, stdout=sp.PIPE).communicate()[0]
                    labelText = result.decode('utf-8').strip()
                    if "escape" in w:
                        labelText = GLib.markup_escape_text(labelText)
                    labelText = w['fmt'].replace('$OUTPUT', labelText)
                    label.set_markup(labelText)
                except:
                    labelText = "Command #" + si + " failed: " + str(w['cmd'])
                    label.set_markup(labelText)

        # add if not previously initialized
        if initializing:
            print("Initializing widget #", si)
            outerContainer.add(labelCnt)
    return True

window.connect('destroy', Gtk.main_quit)

render_container()
GLib.timeout_add((config['interval'] or 2) * 1000, render_container)
window.show_all()
Gtk.main()

#print(dir(label))

#def on_button1_clicked(self):
#        print("clicked")

#button1 = Gtk.Button(label="Hello")
#button1.connect("clicked", on_button1_clicked)
#outerContainer.pack_start(button1, True, True, 0)

# ^ TODO - launcher buttons 
