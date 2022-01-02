# wonky

Wayland layer-shell semi-minimalist replacement for `conky` in Python with GTK.

Basically just forks off subprocesses, grabs their output, dumps them into Pango formatting and throws them on the "BOTTOM" layer of a Wayland session, above the background image but below your windows.

Edit `config.json` for output control.  `style.css` for GTK-compatible "CSS".  Edit the code directly for anything else.  See the code for config.json markup, although the stuff in config.json pretty much covers it currently.

Example sub-scripts are just cobbled together stuff from the past.  Use whatever you want as subprocesses.
