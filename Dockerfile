FROM python:3.9-buster

COPY requirements.txt .
COPY requirements-dev.txt .

RUN pip install -r requirements-dev.txt
# THEME extra
RUN pip install django-simple-captcha==0.5.9
RUN mkdir -p /app/congressus/congressus
RUN ln -s /theme /app/congressus/congressus/theme

WORKDIR /app/congressus

CMD python manage.py runserver 0.0.0.0:8000

#CMD ["gunicorn", \
#    "--bind", "0.0.0.0:8000", \
#    "--workers", "4", \
#    "--timeout", "500", \
#    "--worker-class", "gevent", \
#    "--log-level", "info", \
#    "--log-file", "-", \
#    "seabiscuit.wsgi:application"]
