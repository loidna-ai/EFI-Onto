.PHONY: install test build status backlog reason lint review graph export clean calibrate cause-audit readers refute domestic silmu babrauskas iso iso-freeze run-case run-all missing-audit

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

backlog:
	@$(PY) scripts/backlog.py --check

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

refute:
	python scripts/refute_audit.py

domestic:
	python scripts/domestic.py

silmu:
	python scripts/silmu.py

babrauskas:
	python scripts/babrauskas.py

run-case:
	@$(PY) scripts/run_case.py $(CASE)

run-all:
	@$(PY) scripts/run_case.py --all

missing-audit:
	@$(PY) scripts/missing_audit.py

iso:
	@$(PY) scripts/isomorphic.py

iso-freeze:
	@$(PY) scripts/isomorphic.py --freeze
