#!/usr/bin/env python3 
import gi, json, time, os, threading, subprocess as sp
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GtkLayerShell
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from pathlib import Path

print('Initializing...')

homeDir = str(Path.home())
configDir = homeDir + '/.config/wonky/'
configJsonPath = str(configDir) + 'config.json' 
configCssPath = str(configDir) + 'style.css'

config = json.load(open(configJsonPath))

css_provider = Gtk.CssProvider()
css_provider.load_from_path(configCssPath)

gtkCtx = Gtk.StyleContext()
screen = Gdk.Screen.get_default()
print('n monitors', screen.get_n_monitors())
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

if 'exclusive' in config:
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
        if 'lines' in w:
            env['LINES'] = str(w['lines'])
        if 'columns' in w:
            env['COLUMNS'] = str(w['columns'])

state = {
    'widgets': {},
    'topOutput': '',
    'topPause': False,
    'launcherButtons': {}
}


def capture_top():
    cmd = ['top','-b', '-d', str(topcfg['interval']), '-w']

    with sp.Popen(cmd, stdout=sp.PIPE, bufsize=1, universal_newlines=True, env=env) as p:
        if p.stdout:
            for line in p.stdout:
                if line.startswith('top '):
                  state['topOutput'] = ''
                state['topOutput'] += line

    if p.returncode != 0:
        print('Top errored out!')
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

# closure generator for widget pause
def genPauseWidget(wid):
    def pauseWidget(self):
        widget = state['widgets'][wid]
        if widget['paused']:
            widget['paused'] = False
            widget['pauseButton'].set_label('pause')
        else:
            widget['paused'] = True
            widget['pauseButton'].set_label('unpause')
    return pauseWidget

def initWidget(w, wid, currentTime):
    widgetCnt = Gtk.Box(spacing=0, orientation=Gtk.Orientation.HORIZONTAL)
    label = Gtk.Label()
    boxCnt = Gtk.Box(spacing=0, orientation=Gtk.Orientation.VERTICAL)
    widgetCnt.pack_end(boxCnt, False, False, 0)
    widgetCnt.add(label)
    label.set_valign(Gtk.Align.START)
    label.set_halign(Gtk.Align.START)

    # Assign max width if specified
    if 'maxWidthChars' in w:
        label.set_line_wrap(True)
        label.set_max_width_chars(w['maxWidthChars'])

    # Assign a css class if specified
    if 'class' in w:
        labelCtx = label.get_style_context()
        labelCtx.add_class(w['class'])

    state['widgets'][wid] = {
        'label': label,
        'paused': False
    }
    widget = state['widgets'][wid]
    widget['cnt'] = widgetCnt

    print('Initializing widget...')

    if 'pausable' in w and w['pausable']:
        widget['pauseButton'] = getButton('pause')
        widget['pauseButton'].connect('clicked', genPauseWidget(wid))
        boxCnt.pack_start(widget['pauseButton'], False, False, 0)

    if w['type'] == 'top':
        pass

    if w['type'] == 'launchers':
        buttonsCnt = Gtk.FlowBox()
        buttonsCnt.set_min_children_per_line( lookup(w, ['minPerLine'], 6))
        buttonsCnt.set_max_children_per_line( lookup(w, ['maxPerLine'], 8))
        buttonsCnt.set_selection_mode(Gtk.SelectionMode.NONE)
        widgetCnt.add(buttonsCnt)
        for l in w['launchers']:
            k = l['label']
            state['launcherButtons'][k] = getButton(k)
            state['launcherButtons'][k].connect('clicked', processForker(l['cmd']))
            buttonsCnt.insert(state['launcherButtons'][k], -1)

    return [widgetCnt, widget, label, False]

def getWidget(w, wid, currentTime):
    doContinue = False

    widget = state['widgets'][wid] 
    widgetCnt = widget['cnt']
    label = state['widgets'][wid]['label']
    # Don't bother trying to update text or spacer, requires restart to update
    if w['type'] in ['text','spacer','launchers']:
        doContinue = True
    # skip widgets not due for update (except top which has its own schedule)
    if 'lastRun' in widget and 'interval' in w and w['type'] != 'top':
        timeDiff = currentTime - widget['lastRun']
        if timeDiff < w['interval']:
            doContinue = True
    return [widgetCnt, widget, label, doContinue]


def updateWidget(w, wid, label):
    widget = state['widgets'][wid]
    if widget['paused']:
        return
    match w['type']:
        case 'spacer':
            labelText = ' '
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
            pass

        case 'sh':
            try:
                cmd = w['cmd'].replace('$HOME', homeDir)
                result = sp.Popen(cmd, shell=True, stdout=sp.PIPE).communicate()[0]
                labelText = result.decode('utf-8').strip()
                if 'escape' in w:
                    labelText = GLib.markup_escape_text(labelText)
                labelText = w['fmt'].replace('$OUTPUT', labelText)
                label.set_markup(labelText)
            except:
                labelText = 'Command #' + wid + ' failed: ' + str(w['cmd'])
                label.set_markup(labelText)



def render_container():
    #print('Loop...')
    try:
        config = json.load(open(configJsonPath))
    except:
        print('config.json is malformed!')
        return True

    for i, w in enumerate(config['widgets']):
        wid = w['id']
        currentTime = time.time()
        initializing = False
        if wid in state['widgets']:
            # Lookup routine
            widgetCnt, widget, label, doContinue = getWidget(w, wid, currentTime)
            if doContinue: continue
        else:
            # Initialization routines
            initializing = True
            widgetCnt, widget, label, doContinue = initWidget(w, wid, currentTime )
            if doContinue: continue

        widget['lastRun'] = currentTime

        # Update routines
        updateWidget(w, wid, label)

        if initializing:
            outerContainer.add(widgetCnt)

    # Must return true for timeout_add to continue
    return True

window.connect('destroy', Gtk.main_quit)

render_container()
GLib.timeout_add((config['interval'] or 2) * 1000, render_container)
window.show_all()
Gtk.main()
