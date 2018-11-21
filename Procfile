release: python congressus/manage.py migrate
ws: python congressus/manage.py websocket
web: sh -c 'cd congressus && gunicorn congressus.wsgi --log-file -'
