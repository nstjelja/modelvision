# ModelVision

Downloads images from a [Wiktenauer](https://wiktenauer.com/wiki/Paulus_Hector_Mair) wiki page, serves them through a FastAPI backend, and lets you browse and chat about them via a Streamlit UI using a local [Ollama](https://ollama.com/) vision model (`moondream`).

## Requirements

- Python 3
- [Ollama](https://ollama.com/) running locally with the `moondream` model pulled:
  ```
  ollama pull moondream
  ```

## Setup

```
make venv
```

Creates a `.venv` and installs dependencies from `requirements.txt`.

## Usage

Run each of these in its own terminal.

```
make import   # (re)download all images from the Wiktenauer page into images/, wiping any previous import
make api      # run the FastAPI backend at http://127.0.0.1:8000
make app      # run the Streamlit frontend at http://localhost:8501
```

```
make clean    # remove images/ and .venv
```

## API

- `GET /images/list` — lists downloaded images as `{"id": "images/<file>", "url": "http://<host>/images/<file>"}`.
- `GET /images/<file>` — serves the raw image file.
- `POST /chat` — chat about an image using `moondream`. Body:
  ```json
  {
    "image": "images/<file>",
    "context": "<prior conversation, optional>",
    "query": "<question>"
  }
  ```
  Returns `{"result": "<model response>"}`.

## Frontend

The Streamlit app shows a paginated grid of images (same size, 12 per page). Selecting an image opens a chat sidebar for that image; switching to a different image clears the chat. Each chat message is sent to the API along with the accumulated conversation as context.
