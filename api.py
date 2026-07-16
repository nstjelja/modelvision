import os

import ollama
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

IMAGES_DIR = "images"
IMAGES_DIR_ABS = os.path.abspath(IMAGES_DIR)
CHAT_MODEL = "moondream"

os.makedirs(IMAGES_DIR, exist_ok=True)

app = FastAPI()


class ChatRequest(BaseModel):
    image: str
    context: str = ""
    query: str


@app.get("/images/list")
def list_images(request: Request):
    base_url = str(request.base_url).rstrip("/")
    files = sorted(
        f for f in os.listdir(IMAGES_DIR)
        if os.path.isfile(os.path.join(IMAGES_DIR, f))
    )
    return [
        {"id": f"{IMAGES_DIR}/{f}", "url": f"{base_url}/images/{f}"}
        for f in files
    ]


@app.post("/chat")
def chat(request: ChatRequest):
    resolved = os.path.abspath(request.image)
    if os.path.commonpath([IMAGES_DIR_ABS, resolved]) != IMAGES_DIR_ABS:
        raise HTTPException(status_code=400, detail="Invalid image path")
    if not os.path.isfile(resolved):
        raise HTTPException(status_code=404, detail="Image not found")

    with open(resolved, "rb") as f:
        image_bytes = f.read()

    prompt = f"{request.context}\n\n{request.query}" if request.context else request.query

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_bytes],
            }
        ],
    )
    return {"result": response["message"]["content"]}


app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
