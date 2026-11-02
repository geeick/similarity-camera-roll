"""Run using: streamlit run app.py"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import numpy as np
import streamlit as st
from PIL import Image, ImageOps
from similarity_gallery.index import scan, register_heic
from similarity_gallery.similarity import continuous_order, find_similar, similarity_groups

st.set_page_config(page_title="Similarity Camera Roll", page_icon="📸", layout="wide")
st.title("📸 Similarity Camera Roll")
st.caption("Explore local photos by what they look like, not by date or metadata.")

@st.cache_data(show_spinner=False, max_entries=1000)
def thumbnail(path: str, modified_ns: int) -> bytes:
    register_heic()
    with Image.open(path) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        image.thumbnail((400, 400))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=78)
        return buffer.getvalue()

def _go_to_similar(index: int) -> None:
    st.session_state["view_mode"] = "Find Similar"
    st.session_state["selected_photo"] = index

def show_tile(photo, index=None, score=None):
    try:
        st.image(thumbnail(str(photo.path), photo.path.stat().st_mtime_ns), use_container_width=True)
        label = photo.path.name
        if score is not None:
            label += f" · {score:.3f}"
        st.caption(label)
        if index is not None:
            st.button("Find similar", key=f"similar-{st.session_state.get('view_mode', 'gallery')}-{index}",
                      on_click=_go_to_similar, args=(index,))
    except Exception as exc:
        st.warning(f"Cannot display {photo.path.name}: {exc}")

def show_gallery(photos, indices, scores=None):
    cols = st.columns(4)
    for position, index in enumerate(indices):
        with cols[position % len(cols)]:
            show_tile(photos[index], index, None if scores is None else scores.get(index))

with st.sidebar:
    st.header("Library")
    folder_input = st.text_input("Local photo folder", value=str(Path.home() / "Pictures"))
    limit = st.slider("Maximum photos (prototype)", 25, 500, 150, 25)
    st.caption("Works with JPG, PNG, HEIC, TIFF, and WebP. Videos are not indexed yet.")
    start = st.button("Scan photos", type="primary", use_container_width=True)
    st.caption("Originals are never moved, modified, or uploaded. Model weights download once.")

if start:
    bar = st.progress(0, text="Scanning your photos...")
    def update(done, total):
        bar.progress(min(1.0, done / max(total, 1)), text=f"Indexed {done} / {total}")
    try:
        with st.spinner("Loading AI model and computing visual fingerprints..."):
            st.session_state["photos"], st.session_state["errors"] = scan(
                Path(folder_input), limit=limit, progress=update
            )
        st.session_state["folder"] = folder_input
        bar.empty()
    except Exception as exc:
        st.error(f"Scan failed: {exc}")

photos = st.session_state.get("photos", [])
if not photos:
    st.info("Choose a folder in the sidebar and click **Scan photos**. Start with 50–150 images.")
    st.stop()

st.success(f"Indexed {len(photos)} photos from {st.session_state.get('folder', '')}.")
if st.session_state.get("errors"):
    with st.expander(f"{len(st.session_state['errors'])} files skipped"):
        st.code("\n".join(st.session_state["errors"][:30]))

vectors = np.stack([photo.vector for photo in photos])
mode = st.radio("View", ["Similar Groups", "Continuous Roll", "Find Similar"], horizontal=True, key="view_mode")

if mode == "Similar Groups":
    threshold = st.slider("Similarity needed to group photos", 0.55, 0.95, 0.82, 0.01)
    groups = similarity_groups(vectors, threshold)
    st.caption(f"{len(groups)} groups. Includes single photos; nothing is hidden.")
    for i, indices in enumerate(groups):
        with st.expander(f"Group {i + 1} · {len(indices)} photo{'s' if len(indices) != 1 else ''}", expanded=i < 2):
            show_gallery(photos, indices)
elif mode == "Continuous Roll":
    seed = st.selectbox("Choose the first photo", range(len(photos)),
                        format_func=lambda i: f"{i + 1}. {photos[i].path.name}")
    ordered = continuous_order(vectors, seed)
    st.caption("A greedy nearest-neighbor path through every indexed photo. Not chronological.")
    show_gallery(photos, ordered)
else:
    selected = st.selectbox("Find photos similar to...", range(len(photos)),
                            format_func=lambda i: f"{i + 1}. {photos[i].path.name}", key="selected_photo")
    show_tile(photos[selected], selected)
    n = st.slider("Number of matches", 1, 24, 12)
    matches = find_similar(vectors, selected, limit=n)
    st.caption("Scores are cosine similarity, not a probability. Higher means more visually related.")
    show_gallery(photos, [index for index, _ in matches], {index: score for index, score in matches})
