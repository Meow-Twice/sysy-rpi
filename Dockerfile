FROM python:3.8-alpine
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask gevent
COPY app.py index.html /
WORKDIR /
ENTRYPOINT [ "python", "-u", "app.py" ]
