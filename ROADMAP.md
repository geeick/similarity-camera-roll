# Roadmap

## v0.1 — Local photo similarity gallery
- [x] Folder scanning independent of filename and metadata
- [x] HEIC, JPG, PNG, WebP and TIFF support
- [x] Local CLIP embeddings and SQLite cache
- [x] Similar Groups gallery
- [x] Continuous Roll
- [x] Find Similar
- [x] Read-only handling of originals

## v0.2 — More reliable matching
- [ ] Perceptual hashing for resized / compressed exact copies
- [ ] Local feature matching for screenshots and cropped photos
- [ ] Separate duplicate matches from broadly similar subject matches
- [ ] Visual labels and natural-language queries

## v0.3 — Video and scale
- [ ] Multi-frame video fingerprints (including re-encoded copies)
- [ ] Approximate nearest-neighbor indexing
- [ ] Resumable background scans
- [ ] Improve continuous-roll ordering

## v0.4 — iPhone
- [ ] SwiftUI / PhotoKit library interface with authorization
- [ ] Privacy-first on-device inference
- [ ] Preserve original iOS Photos library organization
