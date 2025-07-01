FROM nginx:1.29-alpine

COPY htpasswd /etc/nginx/htpasswd
COPY nginx.conf.template /etc/nginx/nginx.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV UPSTREAM="https://example.com"

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"] 