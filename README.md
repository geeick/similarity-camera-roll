# Similarity Camera Roll 📸

## 📱 Native iPhone app (SwiftUI)

The native on-device iPhone prototype is in **[ios/](ios/)**. It uses PhotoKit + Vision for similarity, with Similar Groups, Continuous Roll, and Find Similar. It currently scans in batches of 100 up to 600 items per session. See **[iPhone installation instructions](ios/README.md)** for setting up Xcode and running it on a physical iPhone.

The Python prototype below remains available for desktop experiments.



A local-first photo gallery that organizes images by **what they look like**, not by dates, filenames, or metadata.

## Features (v0.1)

- **Similar Groups:** cluster visually related photos into collections.
- **Continuous Roll:** browse every indexed photo in a similarity-based order.
- **Find Similar:** choose any photo and see its nearest visual matches.
- Read JPG, PNG, HEIC/HEIF, TIFF, BMP and WebP.
- Local SQLite cache of CLIP image embeddings to speed up rescans.
- Original photos are never moved, deleted, edited, or uploaded.

**Prototype limitations:** max 500 images per scan. Does not yet index videos or robustly recognize heavily cropped screenshots. These are planned improvements.

## Quick start (macOS)

Use Python 3.11 or 3.12:

~~~bash
git clone https://github.com/geeick/similarity-camera-roll.git
cd similarity-camera-roll
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
~~~

Open the local Streamlit app, enter an exported photos folder, and click **Scan photos**. Start with 50–150 images. The first scan downloads pretrained model weights; subsequent inference is local.

Run the quick tests:

~~~bash
python -m unittest discover -s tests -v
~~~

## How it works

A pretrained CLIP model represents images as embeddings. Cosine similarity powers grouping, nearest-neighbor ordering, and Find Similar. The prototype uses greedy grouping and ordering, suitable for small photo collections. Metadata is used only to detect whether a cached file needs reprocessing, not to measure similarity.

A screenshot containing a small crop of an existing picture and a re-encoded video need additional matching algorithms beyond CLIP; see [ROADMAP.md](ROADMAP.md).

## Privacy

The app works with your local files. It saves an SQLite cache under `.cache/` containing absolute file paths and feature vectors; the cache is excluded from Git. Do not commit photos, personal data, or secrets to this repository.

## Structure

- `app.py` — Streamlit browser interface
- `similarity_gallery/index.py` — photo discovery, CLIP embeddings and caching
- `similarity_gallery/similarity.py` — grouping, ordering, Find Similar
- `tests/` — local unit tests
- `ROADMAP.md` — planned milestones

This is an experimental prototype, not a duplicate-deletion utility.
