FROM python:3.11-bullseye

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
COPY theme/requirements.txt requirements-theme.txt

RUN pip install gunicorn uvicorn
RUN pip install -r requirements.txt
RUN pip install -r requirements-theme.txt
RUN mkdir -p /app/congressus/congressus
RUN ln -s /theme /app/congressus/congressus/theme

WORKDIR /app/congressus

CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "-k uvicorn.workers.UvicornWorker", \
    "--workers", "4", \
    "--timeout", "30", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "congressus.asgi:application"]
