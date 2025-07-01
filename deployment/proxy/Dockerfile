FROM nginx:1.29-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY htpasswd /etc/nginx/htpasswd

ENV upstream="https://placeholder.com"

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"] 