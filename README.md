# photoscrub

Shows you what your photos leak — then removes it.

Passive, local, no upload, no account. Windows and Linux.

## What it finds

| Finding | Level | Why it matters |
|---|---|---|
| **GPS coordinates** | HIGH | exact position, 6 decimal places |
| **Embedded thumbnail** | HIGH | a JPEG can carry a second, *complete* copy of the original image as a 160×120 preview. Stripping EXIF does not remove it |
| **Body serial number** | HIGH | identifies the device, and through purchase history, you |
| **XMP: City, Country, GPS** | HIGH | a second place for the same data — cleaning EXIF is not enough |
| **IPTC: byline, City, Country** | HIGH | editorial fields people forget about |
| **PNG tEXt / iTXt / zTXt / tIME / eXIf** | MED | author, description, comment, embedded EXIF |
| **Artist / Copyright / Software / Lens** | MED | who, with what, where |
| **Data appended after the image** | MED | invisible in preview, readable in a hex editor |
| **GPS in video (MP4/MOV udta atom)** | HIGH | video has no EXIF tags; location lives in the container |
| **Addresses, postcodes, phone numbers in free text** | MED | the leak nobody looks for, because it is not a tag |
| **ZIP: .DS_Store, Thumbs.db, ._sidecars** | LOW | usernames and full paths inside archives |

HEIC/HEIF (iPhone) and RAW extensions (DNG, CR2, NEF, ARW, ORF, RW2) are read.

## Rulesets

Rules are versioned, and your license says which version you bought.

- **v1 — basic**: EXIF, GPS, serial, artist, and the thumbnail hidden in the JPEG.
- **v2 — full**: everything above plus HEIC, XMP, IPTC, PNG chunks, JPEG comments,
  data appended after the image, GPS in video, and PII in free text.

A v1 license keeps working on v1 forever. Nothing is taken away. The upgrade exists
because v2 is real work, not because the file format changed under you.

## The model

A small classifier we trained ourselves (`tools/train_model.py`) scores publish risk
from 15 features. It is **not** an LLM: it is logistic regression, 1.8 KB, trained on
8000 synthetic metadata profiles, 97.4% accuracy on held-out data. It runs offline and
every decision comes from coefficients you can read in `model.json`.

It is also how we found our own bug: it classified a PNG whose description contained
"Mieszkanie, ul. Rodła 12" as safe. That is why `has_free_text_pii` exists.

## Use

```
photoscrub PATH              # report only
photoscrub PATH --scrub OUT  # write metadata-free copies to OUT
photoscrub PATH --json       # machine readable
```

Originals are never modified. `--scrub` refuses to write into the source folder.

## License keys

Keys are Ed25519-signed payloads; the signature travels with the key, so activation
works offline. A key is bound to one machine. Private keys never leave the issuing
machine (`~/.secrets/photoscrub/`).

```
python3 tools/issue.py --email you@example.com --name "Buyer" --ruleset 2
```

## License

Proprietary, all rights reserved. See `LICENSE`.

The source is closed. Buying a license key gives you the right to use the
compiled application on one machine — it does not transfer any rights in
this code, and redistribution is not permitted.
