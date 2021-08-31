lint:
	prospector

mypy:
	mypy .

test:
	pytest -svv

cov:
	coverage run --source=. -m pytest
	coverage report
	coverage html

i18n_extract:
	cd congressus; ./manage.py makemessages -a

i18n_build:
	cd congressus; ./manage.py compilemessages
