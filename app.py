import html
import os

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
IMAGES_PER_PAGE = 12
COLUMNS = 4
THUMB_SIZE = 160
PREVIEW_SIZE = 320
TILE_BORDER_WIDTH = 3
TILE_PADDING = 4
SELECTED_BORDER = f"{TILE_BORDER_WIDTH}px solid #1E90FF"
TILE_UNSELECTED_BORDER = f"{TILE_BORDER_WIDTH}px solid transparent"
PREVIEW_BORDER = "1px solid #ddd"
TILE_WIDTH = THUMB_SIZE + 2 * TILE_PADDING + 2 * TILE_BORDER_WIDTH
GRID_GAP = 16
GRID_WIDTH = COLUMNS * TILE_WIDTH + (COLUMNS - 1) * GRID_GAP
NAV_BUTTON_WIDTH = 110

st.set_page_config(page_title="ModelVision", layout="wide")

st.markdown(
    f"""
    <style>
    .stButton > button {{
        background-color: #1E90FF;
        color: white;
        border-color: #1E90FF;
    }}
    .stButton > button:hover {{
        background-color: #1876D1;
        border-color: #1876D1;
        color: white;
    }}
    .img-box {{
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        background-color: #f0f0f0;
        box-sizing: border-box;
    }}
    .img-box img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }}
    div[class*="st-key-tile"] button {{
        padding: {TILE_PADDING}px;
        background-color: #f0f0f0;
        border: {TILE_UNSELECTED_BORDER};
    }}
    div[class*="st-key-tile"] button img {{
        width: {THUMB_SIZE}px !important;
        height: {THUMB_SIZE}px !important;
        max-width: {THUMB_SIZE}px !important;
        max-height: {THUMB_SIZE}px !important;
        object-fit: contain !important;
        display: block !important;
    }}
    div[class*="st-key-tile-selected_"] button {{
        background-color: #f0f0f0;
        border: {SELECTED_BORDER};
    }}
    div[class*="st-key-gallery_grid"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: {GRID_GAP}px;
        width: {GRID_WIDTH}px;
    }}
    div[class*="st-key-gallery_grid"] > div[data-testid="stElementContainer"] {{
        flex: 0 0 auto !important;
        width: {TILE_WIDTH}px !important;
    }}
    div[class*="st-key-nav_row"] {{
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between;
        align-items: center;
        width: {GRID_WIDTH}px;
    }}
    div[class*="st-key-nav_row"] > div[data-testid="stElementContainer"] {{
        flex: 0 0 auto !important;
        width: auto !important;
    }}
    div[class*="st-key-nav_prev"] button, div[class*="st-key-nav_next"] button {{
        width: {NAV_BUTTON_WIDTH}px;
    }}
    .page-label {{
        width: {GRID_WIDTH}px;
        text-align: center;
        margin-top: 0.5rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_fixed_image(url: str, size: int, border: str = PREVIEW_BORDER):
    st.markdown(
        f"""
        <div class="img-box" style="width:{size}px;height:{size}px;border:{border};">
            <img src="{html.escape(url, quote=True)}">
        </div>
        """,
        unsafe_allow_html=True,
    )

if "page" not in st.session_state:
    st.session_state.page = 0
if "selected_image" not in st.session_state:
    st.session_state.selected_image = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def select_image(image_id: str):
    if st.session_state.selected_image != image_id:
        st.session_state.selected_image = image_id
        st.session_state.chat_history = []


@st.cache_data(ttl=60)
def fetch_images():
    resp = requests.get(f"{API_URL}/images/list", timeout=30)
    resp.raise_for_status()
    return resp.json()


st.title("Image Gallery")

try:
    images = fetch_images()
except requests.RequestException as exc:
    st.error(f"Could not reach API at {API_URL}: {exc}")
    st.stop()

if not images:
    st.info("No images found.")
    st.stop()

total_pages = max(1, (len(images) - 1) // IMAGES_PER_PAGE + 1)
st.session_state.page = min(st.session_state.page, total_pages - 1)

with st.container(key="nav_row"):
    if st.button("Previous", key="nav_prev", disabled=st.session_state.page <= 0):
        st.session_state.page -= 1
        st.rerun()
    if st.button("Next", key="nav_next", disabled=st.session_state.page >= total_pages - 1):
        st.session_state.page += 1
        st.rerun()

start = st.session_state.page * IMAGES_PER_PAGE
page_images = images[start:start + IMAGES_PER_PAGE]

with st.container(key="gallery_grid"):
    for image in page_images:
        is_selected = st.session_state.selected_image == image["id"]
        key_prefix = "tile-selected" if is_selected else "tile"
        st.button(
            f"![{image['id']}]({image['url']})",
            key=f"{key_prefix}_{image['id']}",
            on_click=select_image,
            args=(image["id"],),
        )

st.markdown(
    f"<div class='page-label'>Page {st.session_state.page + 1} of {total_pages}</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Chat")
    if not st.session_state.selected_image:
        st.info("Select an image to start chatting.")
    else:
        selected = next(
            (img for img in images if img["id"] == st.session_state.selected_image),
            None,
        )
        st.subheader(st.session_state.selected_image)
        if selected:
            render_fixed_image(selected["url"], PREVIEW_SIZE)

        for turn in st.session_state.chat_history:
            with st.chat_message(turn["role"]):
                st.write(turn["content"])

        query = st.chat_input("Ask about this image")
        if query:
            context = "\n".join(
                f"{turn['role']}: {turn['content']}"
                for turn in st.session_state.chat_history
            )
            st.session_state.chat_history.append({"role": "user", "content": query})

            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "image": st.session_state.selected_image,
                            "context": context,
                            "query": query,
                        },
                        timeout=120,
                    )
                    resp.raise_for_status()
                    answer = resp.json()["result"]
                except requests.RequestException as exc:
                    answer = f"Error calling chat API: {exc}"

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()
