# Aplicación para venta de entradas y registro en congresos

Esta aplicación ofrece una forma sencilla para montar un formulario de
venta de entradas para eventos y congresos, con cobro a través de un TPV.


## Despliegue con docker-compose

Hacer una copia del fichero .env.example y crearse el fichero .env:

```
cp .env.example .env
```

Crear network desde docker:

```
docker network create traefik_congressus
```

Contruir imágenes y levantar contenedores:

```
docker-compose build
docker-compose up -d
```

La primera vez que ejecute el entorno, necesitará entrar en el contenedor web para realizar
la primera migración, crear un usuario administrador, generar los ficheros estáticos y crear
la tabla de caché:

```
docker exec -ti congressus_web bash
./manage.py migrate
./manage.py createsuperuser
./manage.py collectstatic
./manage.py createcachetable
```


## Generar traducciones

Al ser una aplicación django, podemos ver toda la información de traducciones en el siguiente enlace:

 https://docs.djangoproject.com/en/1.10/topics/i18n/translation/

```
./manage.py makemessages -a # Update .po files
./manage.py compilemessages # Compile .po files
```


## Generar UML de modelos django

Instalar django-extensions y pygraphviz.

```
sudo apt-get install graphviz-dev
pip install django-extensions pygraphviz
```

Añadir django_extensions en INSTALLED_APPS:

```
    'django_extensions',
```

Generar png:

```
# Normal
./manage.py graph_models -a -o testg.png
# Agrupado por app
./manage.py graph_models -a -g -o testg.png
```

Si obtenemos el error "CommandError: Neither pygraphviz nor pydot could be found to generate the image"

```
pip uninstall pygraphviz
pip install pygraphviz --install-option="--include-path=/usr/include/graphviz" --install-option="--library-path=/usr/lib/graphviz/"
```

## Problema al añadir maintenance-mode

Si nos da error de que no existen las relaciones, es porque hay que añadir algunas tablas:

```
./manage.py migrate
./manage.py migrate --run-syncdb
```
