# photoscrub

Shows you what your photos leak — then removes it in one click.

Passive, local, no upload, no account. Windows and Linux.

## What it finds

- **GPS coordinates** (HIGH) — exact position, 6 decimal places
- **Embedded thumbnail** (HIGH) — a JPEG can carry a second, *complete* copy of
  the original image as a 160×120 preview. Stripping EXIF does not remove it.
  This is the one most "metadata removers" get wrong.
- **Body serial number** (HIGH) — identifies the device, and through purchase
  history, you
- **Artist / copyright / software / lens** (MED)
- **Timestamps** (LOW) — when you took it, and in what order
- **Zip archives** — `.DS_Store`, `Thumbs.db`, `._name` sidecar files

## Why it exists

Tools like `exiftool` do this well but are command-line tools. GUI tools look
like they were written in 2008 and tell you *that* a tag exists, not what it
means. photoscrub prints the actual value, grades the risk, and explains why
each field is a problem.

## Use

```
photoscrub.py PATH              # report only
photoscrub.py PATH --scrub OUT  # write metadata-free copies to OUT
photoscrub.py PATH --json       # machine readable
```

Originals are never modified. `--scrub` writes new files.

## License

MIT.
