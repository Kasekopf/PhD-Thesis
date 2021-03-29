ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

figures:
	( \
		export PYTHONPATH="${PYTHONPATH}:${ROOT_DIR}/src"; \
		. venv/bin/activate; \
		python3 src/3/gen.py; \
		python3 src/4/gen.py; \
		python3 src/5/gen.py; \
		python3 src/6/gen.py; \
	)

clean:
	find . -maxdepth 10 -type f -name "*.db" -delete
