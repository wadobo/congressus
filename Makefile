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
	django-admin makemessages -a

i18n_build:
	django-admin compilemessages
