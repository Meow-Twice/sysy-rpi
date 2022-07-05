FROM python:3.8-alpine
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask uwsgi
COPY app.py index.html /
WORKDIR /
ENTRYPOINT [ "uwsgi", "--master", "-p", "4", "--http", "0.0.0.0:8000", "-w", "app:app" ]
