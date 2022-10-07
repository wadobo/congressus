FROM python:3.10-bullseye

RUN apt update
RUN apt-get install -y\
    build-essential\
    python3-dev\
    python3-pip\
    python3-setuptools\
    python3-wheel\
    python3-cffi\
    libcairo2\
    libpango-1.0-0\
    libpangocairo-1.0-0\
    libgdk-pixbuf2.0-0\
    libffi-dev\
    shared-mime-info

COPY requirements.txt .
COPY requirements-dev.txt .

RUN pip install -r requirements-dev.txt
# THEME extra
RUN pip install django-simple-captcha==0.5.9
RUN pip install gunicorn==20.1.0
RUN mkdir -p /app/congressus/congressus
RUN ln -s /theme /app/congressus/congressus/theme

WORKDIR /app/congressus

CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "2", \
    "--timeout", "30", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "congressus.wsgi:application"]
