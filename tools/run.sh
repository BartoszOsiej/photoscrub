#!/bin/sh
DIR="/usr/lib/photoscrub"
exec python3 -c "import sys; sys.path.insert(0,'$DIR'); import gui; gui.App().mainloop()" "$@"
