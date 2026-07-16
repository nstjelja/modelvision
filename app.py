import os

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
IMAGES_PER_PAGE = 12
COLUMNS = 4
THUMB_SIZE = 160

st.set_page_config(page_title="ModelVision", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = 0
if "selected_image" not in st.session_state:
    st.session_state.selected_image = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


@st.cache_data(ttl=60)
def fetch_images():
    resp = requests.get(f"{API_URL}/images/list", timeout=30)
    resp.raise_for_status()
    return resp.json()


def select_image(image_id: str):
    if st.session_state.selected_image != image_id:
        st.session_state.selected_image = image_id
        st.session_state.chat_history = []


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

nav_prev, nav_label, nav_next = st.columns([1, 2, 1])
with nav_prev:
    if st.button("Previous", disabled=st.session_state.page <= 0):
        st.session_state.page -= 1
        st.rerun()
with nav_label:
    st.markdown(
        f"<div style='text-align:center'>Page {st.session_state.page + 1} of {total_pages}</div>",
        unsafe_allow_html=True,
    )
with nav_next:
    if st.button("Next", disabled=st.session_state.page >= total_pages - 1):
        st.session_state.page += 1
        st.rerun()

start = st.session_state.page * IMAGES_PER_PAGE
page_images = images[start:start + IMAGES_PER_PAGE]

cols = st.columns(COLUMNS)
for i, image in enumerate(page_images):
    with cols[i % COLUMNS]:
        st.image(image["url"], width=THUMB_SIZE)
        is_selected = st.session_state.selected_image == image["id"]
        st.button(
            "Selected" if is_selected else "Select",
            key=f"select_{image['id']}",
            disabled=is_selected,
            on_click=select_image,
            args=(image["id"],),
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
            st.image(selected["url"], width="stretch")

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
