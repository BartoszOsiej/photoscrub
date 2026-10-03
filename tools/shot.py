#!/usr/bin/env python3
"""Narzedzie deweloperskie: uruchamia GUI na wirtualnym ekranie i robi screeny.
Uzywam tego zamiast prosic ciebie o oczy - widze wynik sam."""
import glob
import os
import subprocess
import sys
import threading
import time

os.environ.setdefault('DISPLAY', ':98')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gui as G
import photoscrub as ps

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/opencode/shot.png'
FOLDER = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser('~/zdjecia-testowe')


def shot(name):
    p = f'{OUT.rsplit(".", 1)[0]}_{name}.png'
    subprocess.run(['scrot', '-o', p], check=False)
    print('zapisano', p, flush=True)


def main():
    app = G.App()

    def boot():
        time.sleep(1.0)
        files = sorted(glob.glob(f'{FOLDER}/*.jpg'))
        reps, thumbs = [], []
        for f in files:
            reps.append(ps.scan_file(f))
            thumbs.append(app._thumb(f))
        app.after(0, app._fill, reps, thumbs)
        time.sleep(1.6)
        shot('main')
        time.sleep(0.4)
        for r in reps:
            if r.findings:
                app.show_detail(r)
                break
        time.sleep(0.6)
        shot('detail')
        time.sleep(0.3)
        app.quit()

    threading.Thread(target=boot, daemon=True).start()
    app.after(12000, app.quit)
    app.mainloop()


if __name__ == '__main__':
    main()
