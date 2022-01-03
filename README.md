# wonky

Wayland layer-shell semi-minimalist replacement for `conky` in Python with GTK.

## Installation
Copy `config.json` and `style.css` into `~/.config/wonky/`.  Edit them as needed.  `config.json` markup should be pretty obvious, but the program will probably just break if you do something too messed up.  `style.css` is in GTK markup corresponding to the output widgets - the default should be fine for a lot of use cases.  Anything beyond that and you'll probably want to just edit the code.  

## Notes

Basically just forks off subprocesses, grabs their output, dumps them into Pango formatting and throws them on the "BOTTOM" layer of a Wayland session, above the background image but below your windows.

Example sub-scripts are just cobbled together stuff from the past.  Use whatever you want as subprocesses - see "sh" examples in `config.json`.

PRs welcome!  Just don't break my config please!

![Screenshot](/screenshot.png)
