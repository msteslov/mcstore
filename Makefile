.PHONY: install lint test run proto

install:
	python -m pip install -e '.[dev,bot]'

lint:
	ruff check .

test:
	pytest --cov

run:
	uvicorn mcstore.api:app --reload

proto:
	python scripts/generate_proto.py
