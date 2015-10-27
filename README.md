# Aplicación para registro en congresos

## Despliegue

Es una aplicación django, por lo que el despliegue se puede hacer siguiendo
las instrucciones del framework:

 https://docs.djangoproject.com/en/1.8/howto/deployment/

Las dependencias django están en el fichero requirements.txt.

## Entorno de desarrollo

Creación de la base de datos:

```
python manage.py migrate
```

Servidor de pruebas:

```
python manage.py runserver
```
