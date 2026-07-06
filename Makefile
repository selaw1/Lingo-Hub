SETUP_ENV = . venv/bin/activate && DJANGO_SETTINGS_MODULE=core.settings

all: install migrate lint server

server:
	$(SETUP_ENV) python manage.py runserver 8000

debug:
	$(SETUP_ENV) python -m debugpy --listen 0.0.0.0:6969 --wait-for-client manage.py runserver 8000

clean:
	rm -rf venv/

install:
	python3 -m venv venv
	$(SETUP_ENV) && pip install -r requirements.txt

migrate:
	$(SETUP_ENV) python manage.py migrate

revert_migrate:
	$(SETUP_ENV) python manage.py migrate ${app} ${migration}

migrations:
	$(SETUP_ENV) python manage.py makemigrations

empty-migrations:
	$(SETUP_ENV) python manage.py makemigrations --empty ${app}

superuser:
	$(SETUP_ENV) python manage.py createsuperuser

startapp:
	$(SETUP_ENV) python manage.py startapp ${app_name}

check:
	$(SETUP_ENV) && ruff check --exclude="*/migrations/*" .

format:
	@echo "Formatting Python..."
	$(SETUP_ENV) && ruff format --exclude="*/migrations/*" .

lint:
	$(SETUP_ENV) && ruff check --exclude="*/migrations/*" .

test:
	$(SETUP_ENV) coverage run --source='.' manage.py test

coverage:
	$(SETUP_ENV) coverage report

test_app:
	$(SETUP_ENV) coverage run --source='.' manage.py test ${app} --pattern="test_*.py"

shell:
	$(SETUP_ENV) python manage.py shell

collect_static:
	$(SETUP_ENV) python manage.py collectstatic --noinput

runcommand:
	$(SETUP_ENV) python manage.py $(command) $(extra_arg)

html_coverage:
	$(SETUP_ENV) && coverage html --skip-covered

.PHONY: all server debug clean install migrate revert_migrate migrations empty-migrations superuser startapp check format lint test coverage test_app shell collect_static runcommand html_coverage
