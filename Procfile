release: sh -c 'cd congressus && python manage.py migrate'
ws: sh -c 'cd congressus && python manage.py websocket'
web: sh -c 'cd congressus && gunicorn congressus.wsgi --log-file -'
