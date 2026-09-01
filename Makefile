.PHONY: install test build status reason lint review graph export clean

PY := python
export PYTHONIOENCODING := utf-8

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

status:
	@$(PY) scripts/status.py

reason:
	@$(PY) scripts/consistency.py

lint:
	@$(PY) scripts/lint.py

review: | build-dir
	$(PY) scripts/extract.py > build/graph.json
	$(PY) scripts/extract_onto.py
	$(PY) scripts/review.py

graph: | build-dir
	$(PY) scripts/extract.py > build/graph.json
	$(PY) scripts/graph.py

build-dir:
	@$(PY) -c "import os; os.makedirs('build', exist_ok=True)"

clean:
	rm -rf build/* .pytest_cache **/__pycache__

calibrate:
	python scripts/calibrate.py

cause-audit:
	python scripts/cause_audit.py

readers:
	python scripts/reader_compare.py
