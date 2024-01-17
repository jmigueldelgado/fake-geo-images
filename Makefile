SRC := .

test:
	black .
	python -m pytest --pylint --pylint-rcfile=../../pylintrc --mypy --mypy-ignore-missing-imports --cov=fake_geo_images/ --durations=3
	coverage-badge -f -o coverage.svg

package:
	python setup.py sdist bdist_wheel
	twine check dist/*

upload:
	twine upload --skip-existing -u __token__ -p $(TWINE_PASSWORD) dist/*

