.PHONY: test test-ui test-unit

test-unit:
	pytest -k 'not ui_smoke'

test-ui:
	pytest -k ui_smoke

test: test-unit test-ui
