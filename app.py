from http import client
import stat
from flask import Flask, request
import socket
import os
import subprocess
import time

app = Flask("rpi-run")

DATA_PATH = "data"
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH, mode=0o755)

ELF_FILE = os.path.join(DATA_PATH, "run.elf")
INPUT_FILE = os.path.join(DATA_PATH, "input.txt")
OUTPUT_FILE = os.path.join(DATA_PATH, "output.txt")
PERF_FILE = os.path.join(DATA_PATH, "perf.txt")

# 显示欢迎页
@app.route("/")
def hello():
    with open("index.html", "r") as fp:
        h = fp.read()
    return h.format(hostname=socket.gethostname())

# 上传 ELF 文件
@app.route("/elf", methods=['POST'])
def upload_elf():
    if 'file' not in request.files:
        return "file not exist", client.BAD_REQUEST
    file = request.files['file']
    file.save(ELF_FILE)
    os.chmod(ELF_FILE, os.stat(ELF_FILE).st_mode | stat.S_IEXEC)
    return "ok, elf received {0} bytes".format(os.path.getsize(ELF_FILE)), client.OK

# 上传 in 文件
@app.route("/input", methods=['POST'])
def upload_input():
    if 'file' not in request.files:
        # use body as content
        with open(INPUT_FILE, "w") as fp:
            fp.write(request.data.decode('utf-8'))
    else:
        file = request.files['file']
        file.save(INPUT_FILE)
    start_time = time.time()
    p = subprocess.run([ELF_FILE], stdin=open(INPUT_FILE, "r"), stdout=open(OUTPUT_FILE, "w"), stderr=open(PERF_FILE, "w"))
    end_time = time.time()
    # 向 stdout.txt 后追加返回值
    with open(OUTPUT_FILE, "r") as fp:
        stdout = fp.read()
    append_nl = stdout[-1] != '\n'
    with open(OUTPUT_FILE, "a") as fp:
        if append_nl:
            fp.write('\n')
        fp.write(str(p.returncode))
    elapsed_time = (end_time - start_time)
    return "ok, elapsed {0:.2f} secs".format(elapsed_time), client.OK

# 下载 out 文件
@app.route("/output", methods=['GET'])
def get_output():
    with open(OUTPUT_FILE, "r") as fp:
        body = fp.read()
    return body

# 下载 perf 文件
@app.route("/perf", methods=['GET'])
def get_perf():
    with open(PERF_FILE, "r") as fp:
        body = fp.read()
    return body

if __name__ == '__main__':
    from gevent import pywsgi
    pywsgi.WSGIServer(('0.0.0.0', 8000), application=app).serve_forever()
    pass