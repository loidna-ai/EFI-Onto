.PHONY: install test build review graph export clean

PY := python

install:
	$(PY) -m pip install -r requirements.txt --break-system-packages

test:
	$(PY) -m pytest tests/ -v

build: | build-dir
	$(PY) scripts/extract.py > build/graph.json
	$(PY) scripts/extract_onto.py
	$(PY) scripts/build.py
	$(PY) scripts/graph.py
	$(PY) scripts/review.py
	$(PY) scripts/export.py
	@echo "→ build/ 확인"

review: | build-dir
	$(PY) scripts/extract.py > build/graph.json
	$(PY) scripts/extract_onto.py
	$(PY) scripts/review.py

graph: | build-dir
	$(PY) scripts/extract.py > build/graph.json
	$(PY) scripts/graph.py

build-dir:
	@mkdir -p build

clean:
	rm -rf build/* .pytest_cache **/__pycache__
