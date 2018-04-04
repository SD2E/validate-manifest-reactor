.PHONY: tests data-representation
.SILENT: tests data-representation

data-representation:
	rm -rf data-representation && \
	git clone https://gitlab.sd2e.org/sd2program/data-representation && \
	cd data-representation && git checkout master

clean:
	rm -rf .hypothesis .pytest_cache __pycache__ */__pycache__

tests: clean
	abaco deploy -R && \
	export LOCALONLY=1 ; bash tests/run_container_tests.sh pytest tests -s
