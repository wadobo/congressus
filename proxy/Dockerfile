FROM nginx:1.19.6-alpine

ARG DOMAIN
ARG SCHEMA

RUN apk add certbot certbot-nginx

COPY etc/nginx/conf.d/*.conf /etc/nginx/conf.d/
COPY etc/nginx/nginx.conf /etc/nginx/nginx.conf

RUN sed -i "s/#_${SCHEMA}_://g; s/_DOMAIN_/${DOMAIN}/g" /etc/nginx/conf.d/*.conf

RUN rm /etc/nginx/conf.d/default.conf
