.PHONY: venv import api app clean

VENV := .venv
PYTHON := $(VENV)/bin/python
FASTAPI := $(VENV)/bin/fastapi
STREAMLIT := $(VENV)/bin/streamlit

$(VENV)/bin/pip:
	python3 -m venv $(VENV)

venv: $(VENV)/bin/pip
	$(VENV)/bin/pip install --quiet -r requirements.txt

import: venv
	rm -rf images
	$(PYTHON) download_images.py

api: venv
	$(FASTAPI) run api.py

app: venv
	$(STREAMLIT) run app.py

clean:
	rm -rf images $(VENV)
