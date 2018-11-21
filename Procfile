release: python congressus/manage.py migrate
statics: python congressus/manage.py collectstatic
ws: python congressus/manage.py websocket
web: sh -c 'cd congressus && gunicorn congressus.wsgi --log-file -'
