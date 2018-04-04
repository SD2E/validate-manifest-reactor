.PHONY: tests data-representation
.SILENT: tests data-representation

data-representation:
	git submodule update --init

clean:
	rm -rf .hypothesis .pytest_cache __pycache__ */__pycache__

tests: clean
	bash tests/run_container_tests.sh pytest tests -s
