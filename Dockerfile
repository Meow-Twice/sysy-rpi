FROM python:3.8-alpine
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY app.py index.html /
WORKDIR /
ENTRYPOINT [ "python", "-u", "app.py" ]
