"""metadata_viewer.py - SAFE, LOCAL photo-metadata viewer / cleaner (optional feature).

* Reads metadata ONLY from a file you choose on your own computer.
* Nothing is uploaded or sent anywhere. No network code is used.
* Shows only metadata that is explicitly present in the file; it does NOT guess hidden
  locations and does NOT reverse-geocode GPS values.
* Metadata removal writes a CLEAN COPY - your original file is never modified.

Usage:
    python tools/metadata_viewer.py photo.jpg
    python tools/metadata_viewer.py photo.jpg --strip photo_clean.jpg
"""
import argparse
import sys

from PIL import ExifTags, Image

GPS_IFD = 0x8825


def read_metadata(path):
    """Return {tag name: value} for the EXIF data present in the image."""
    with Image.open(path) as img:
        exif = img.getexif()
        data = {ExifTags.TAGS.get(tag, f"Tag{tag}"): value for tag, value in exif.items() if tag != GPS_IFD}
        gps = exif.get_ifd(GPS_IFD)
        if gps:
            data["GPSInfo"] = {ExifTags.GPSTAGS.get(k, str(k)): v for k, v in gps.items()}
    return data


def strip_metadata(src, dst):
    """Save a copy of the image with pixel data only (no EXIF, no GPS)."""
    with Image.open(src) as img:
        clean = Image.new(img.mode, img.size)
        clean.paste(img)  # copies pixels only - EXIF/GPS are not carried over
        clean.save(dst)


def main():
    parser = argparse.ArgumentParser(description="View or remove photo metadata locally")
    parser.add_argument("image")
    parser.add_argument("--strip", metavar="OUTPUT", help="write a metadata-free copy to OUTPUT")
    args = parser.parse_args()
    meta = read_metadata(args.image)
    if not meta:
        print("No EXIF metadata found in this file.")
    for key, value in meta.items():
        print(f"{key}: {value}")
    if "GPSInfo" in meta:
        print("\nPRIVACY NOTE: this photo contains GPS coordinates. Anyone who receives the original file could read them.")
    if args.strip:
        strip_metadata(args.image, args.strip)
        print(f"\nClean copy written to {args.strip} (original untouched).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
