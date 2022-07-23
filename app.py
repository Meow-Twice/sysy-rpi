from http import client
import stat
from flask import Flask, request
import socket
import os
import subprocess
import time

app = Flask("sysy-rpi")

DATA_PATH = "data"
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH, mode=0o755)

TIMEOUT_SECS = 120

ASM_FILE    = os.path.join(DATA_PATH, "test.S")
ELF_FILE    = os.path.join(DATA_PATH, "test.elf")
INPUT_FILE  = os.path.join(DATA_PATH, "input.txt")
OUTPUT_FILE = os.path.join(DATA_PATH, "output.txt")
PERF_FILE   = os.path.join(DATA_PATH, "perf.txt")

def start_process_with_timeout(cmd: list, **kwargs):
    # kwargs must contains: stdin, stdout, stderr
    p = subprocess.Popen(cmd, stdin=kwargs['stdin'], stdout=kwargs['stdout'], stderr=kwargs['stderr'])
    try:
        p.wait(timeout=kwargs['timeout'])
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        p.kill()
        raise e

# 显示欢迎页
@app.route("/")
def hello():
    with open("index.html", "r") as fp:
        h = fp.read()
    return h.format(hostname=socket.gethostname())

# 上传汇编文件 在派上自动编译为 ELF
@app.route("/asm", methods=['POST'])
def upload_asm():
    try:
        if 'file' not in request.files:
            # use body as content
            with open(ASM_FILE, "w") as fp:
                fp.write(request.data.decode('utf-8'))
        else:
            file = request.files['file']
            file.save(ASM_FILE)
    except Exception as e:
        return str(e), client.INTERNAL_SERVER_ERROR
    try:
        ret, _, stderr = start_process_with_timeout(["/bin/bash", "/usr/bin/sysy-elf.sh", ASM_FILE], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=TIMEOUT_SECS)
    except subprocess.TimeoutExpired:
        return "gcc timeout!", client.INTERNAL_SERVER_ERROR
    resp = stderr.decode('utf-8')
    if resp != "" and not resp.endswith('\n'):
        resp += "\n"
    resp += "gcc exited with code {0}".format(ret)
    return resp, client.OK if ret == 0 else client.INTERNAL_SERVER_ERROR

# 上传 ELF 文件
@app.route("/elf", methods=['POST'])
def upload_elf():
    if 'file' not in request.files:
        return "file not exist", client.BAD_REQUEST
    file = request.files['file']
    try:
        file.save(ELF_FILE)
        os.chmod(ELF_FILE, os.stat(ELF_FILE).st_mode | stat.S_IEXEC)
    except Exception as e:
        return str(e), client.INTERNAL_SERVER_ERROR
    return "ok, elf received {0} bytes".format(os.path.getsize(ELF_FILE)), client.OK

# 上传 in 文件
@app.route("/input", methods=['POST'])
def upload_input():
    try:
        if 'file' not in request.files:
            # use body as content
            with open(INPUT_FILE, "w") as fp:
                fp.write(request.data.decode('utf-8'))
        else:
            file = request.files['file']
            file.save(INPUT_FILE)
    except Exception as e:
        return str(e), client.INTERNAL_SERVER_ERROR
    start_time = time.time()
    try:
        ret, _, _ = start_process_with_timeout([ELF_FILE], stdin=open(INPUT_FILE, "r"), stdout=open(OUTPUT_FILE, "w"), stderr=open(PERF_FILE, "w"), timeout=TIMEOUT_SECS)
    except subprocess.TimeoutExpired:
        return "elf run timeout!", client.INTERNAL_SERVER_ERROR
    end_time = time.time()
    # 向 stdout.txt 后追加返回值
    with open(OUTPUT_FILE, "r") as fp:
        stdout = fp.read()
    append_nl = len(stdout) != 0 and stdout[-1] != '\n'
    with open(OUTPUT_FILE, "a") as fp:
        if append_nl:
            fp.write('\n')
        fp.write(str(ret))
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
