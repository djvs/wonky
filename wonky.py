#!/usr/bin/env python3 

import gi, json, time, os, threading, subprocess as sp
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

# lens-style utility fn
def lookup(d, list_of_keys, default):
    for k in list_of_keys:
        if k not in d: 
            return default
        d=d[k]
    return d

if "exclusive" in config:
    GtkLayerShell.auto_exclusive_zone_enable(window) # Optional 

GtkLayerShell.set_layer(window, 1)

GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, lookup(config, ['window','margin','top'], 5))
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.RIGHT, lookup(config, ['window','margin','right'], 1000))
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.BOTTOM, lookup(config, ['window','margin','bottom'], 5))
GtkLayerShell.set_margin(window, GtkLayerShell.Edge.LEFT, lookup(config, ['window','margin','left'], 5))
if lookup(config, ['window','anchor','top'], False): GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, 1)
if lookup(config, ['window','anchor','right'], False): GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, 1)
if lookup(config, ['window','anchor','bottom'], False): GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.BOTTOM, 1)
if lookup(config, ['window','anchor','left'], False): GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, 1)

outerContainer = Gtk.Box(spacing=6,orientation=Gtk.Orientation.VERTICAL)
window.add(outerContainer)

# long-running top process setup
env = os.environ.copy()
runtop = False
for w in config['widgets']:
    if w['type'] == 'top':
        runtop = True
        topcfg = w
        if "lines" in w:
            env['LINES'] = str(w['lines'])
        if "columns" in w:
            env['COLUMNS'] = str(w['columns'])

state = {
    "widgets": {},
    "topOutput": "",
    "topPause": False,
    "launcherButtons": {}
}

def pausetop(self):
    if state['topPause']:
        state['topPause'] = False
        state['topPauseButton'].set_label('pause')
    else:
        state['topPause'] = True
        state['topPauseButton'].set_label('unpause')

def capture_top():
    cmd = ["top","-b", "-d", str(topcfg['interval']), "-w"]

    with sp.Popen(cmd, stdout=sp.PIPE, bufsize=1, universal_newlines=True, env=env) as p:
        for line in p.stdout:
            if line.startswith('top '):
              state['topOutput'] = ''
            state['topOutput'] += line

    if p.returncode != 0:
        print("Top errored out!")
        #raise sp.CalledProcessError(p.returncode, p.args)

if runtop:
    thr = threading.Thread(target=capture_top)
    thr.start()

def getButton(label):
    b = Gtk.Button(label=label)
    b.set_relief(Gtk.ReliefStyle.NONE)
    return b

# closure generator for launcher button signal handlers
def processForker(cmd):
    def signalHandler(event):
        sp.Popen(cmd)
    return signalHandler

def render_container():
    #print("Loop...")
    try:
        config = json.load(open(configJsonPath))
    except:
        print("config.json is malformed!")
        return True

    for i, w in enumerate(config['widgets']):
        si = w['id']
        currentTime = time.time()
        if si in state['widgets']:
            # Lookup routine
            initializing = False
            ref = state["widgets"][si] 
            label = state["widgets"][si]['widget']
            # Don't bother trying to update text or spacer, requires restart to update
            if w['type'] in ['text','spacer','launchers']:
                continue
            # skip widgets not due for update
            if 'lastRun' in ref and 'interval' in w:
                timeDiff = currentTime - ref["lastRun"]
                if timeDiff < w["interval"]:
                    continue
        else:
            # Initialization routine
            initializing = True
            widgetCnt = Gtk.Box(spacing=0, orientation=Gtk.Orientation.HORIZONTAL)
            label = Gtk.Label()
            widgetCnt.add(label)
            label.set_valign(Gtk.Align.START)
            label.set_halign(Gtk.Align.START)

            # Assign max width if specified
            if "maxWidthChars" in w:
                label.set_line_wrap(True)
                label.set_max_width_chars(w['maxWidthChars'])

            # Assign a css class if specified
            if "class" in w:
                labelCtx = label.get_style_context()
                labelCtx.add_class(w['class'])

            state["widgets"][si] = { "widget": label }
            ref = state["widgets"][si]
            ref['cnt'] = widgetCnt

            if w['type'] == 'top':
                # Make a fancy top pause button for top widgets
                boxCnt = Gtk.Box(spacing=0, orientation=Gtk.Orientation.VERTICAL)
                widgetCnt.pack_end(boxCnt, False, False, 0)
                state['topPauseButton'] = getButton("pause")
                state['topPauseButton'].connect("clicked", pausetop)
                boxCnt.pack_start(state['topPauseButton'], False, False, 0)

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

            case 'top':
                if not state['topPause']:
                    labelText = GLib.markup_escape_text(str(state['topOutput']))
                    labelText = w['fmt'].replace('$OUTPUT', labelText)
                    label.set_markup(labelText)

            case 'launchers':
                buttonsCnt = Gtk.FlowBox()
                buttonsCnt.set_min_children_per_line( lookup(w, ['minPerLine'], 6))
                buttonsCnt.set_max_children_per_line( lookup(w, ['maxPerLine'], 8))
                buttonsCnt.set_selection_mode(Gtk.SelectionMode.NONE)
                widgetCnt.add(buttonsCnt)
                for l in w['launchers']:
                    k = l['label']
                    state['launcherButtons'][k] = getButton(k)
                    state['launcherButtons'][k].connect("clicked", processForker(l['cmd']))
                    buttonsCnt.insert(state['launcherButtons'][k], 1)

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
            outerContainer.add(widgetCnt)
    return True

window.connect('destroy', Gtk.main_quit)

render_container()
GLib.timeout_add((config['interval'] or 2) * 1000, render_container)
window.show_all()
Gtk.main()

#print(dir(label))

#def on_button1_clicked(self):
#        print("clicked")

#button1 = getButton("Hello")
#button1.connect("clicked", on_button1_clicked)
#outerContainer.pack_start(button1, True, True, 0)

# ^ TODO - launcher buttons 
