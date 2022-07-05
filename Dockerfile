FROM python:3.8-alpine
RUN pip install flask -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY app.py index.html /
WORKDIR /
ENTRYPOINT [ "flask", "run", "-p", "8000" ]
