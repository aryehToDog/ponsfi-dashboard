# Pons / StonkFun 监控看板 —— Docker 镜像
# 构建：docker build -t pons-dashboard .
# 运行：docker run -d -p 8080:80 --name pons-dashboard pons-dashboard

FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY index.html /usr/share/nginx/html/index.html
COPY nginx-container.conf /etc/nginx/conf.d/dashboard.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -q --spider http://127.0.0.1/ || exit 1
