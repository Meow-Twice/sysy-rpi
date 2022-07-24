from http import client
import stat
from flask import Flask, request
import socket
import os
import subprocess
import time
from io import FileIO
from typing import IO

app = Flask("sysy-rpi")
app.config['CHUNK_SIZE'] = 8192

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

def receive_post_body(stream: IO[bytes], file_size: int, file_fp: FileIO) -> float:
    chunk_size = app.config['CHUNK_SIZE']
    recv_size = 0
    while True:
        chunk = stream.read(chunk_size)
        if len(chunk) == 0:
            break
        file_fp.write(chunk)
        recv_size += len(chunk)
        print('received {0}/{1} ...'.format(recv_size, file_size), flush=True)

# Welcome and usage page.
@app.route("/")
def hello():
    with open("index.html", "r") as fp:
        h = fp.read()
    return h.format(hostname=socket.gethostname())

# Upload assembly file, then link it to ELF with gcc
@app.route("/asm", methods=['POST'])
def upload_asm():
    file_size = request.headers['Content-Length']
    start_time = time.time()
    try:
        with open(ASM_FILE, "wb") as fp:
            receive_post_body(request.stream, file_size, fp)
    except OSError as e:
        return str(e), client.INTERNAL_SERVER_ERROR
    try:
        ret, _, stderr = start_process_with_timeout(["/bin/bash", "/usr/bin/sysy-elf.sh", ASM_FILE], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=TIMEOUT_SECS)
    except subprocess.TimeoutExpired:
        return "gcc timeout!", client.INTERNAL_SERVER_ERROR
    resp = stderr.read().decode('utf-8')
    if resp != "" and not resp.endswith('\n'):
        resp += "\n"
    end_time = time.time()
    resp += "ok, gcc exited with code {0}, elapsed {1:.2f} secs".format(ret, (end_time - start_time))
    return resp, client.OK if ret == 0 else client.INTERNAL_SERVER_ERROR

# Upload ELF file, attention the size of payload may be huge (>100MB, even >1GB)
@app.route("/elf", methods=['POST'])
def upload_elf():
    file_size = request.headers['Content-Length']
    start_time = time.time()
    try:
        with open(ELF_FILE, "wb") as fp:
            receive_post_body(request.stream, file_size, fp)
    except OSError as e:
        return str(e), client.INTERNAL_SERVER_ERROR
    try:
        os.chmod(ELF_FILE, os.stat(ELF_FILE).st_mode | stat.S_IEXEC)
    except Exception as e:
        return str(e), client.INTERNAL_SERVER_ERROR
    end_time = time.time()
    return "ok, elf received {0} bytes, elapsed {1:.2f} secs".format(os.path.getsize(ELF_FILE), (end_time - start_time)), client.OK

# Send standard input file, then execute the ELF file uploaded previously.
@app.route("/input", methods=['POST'])
def upload_input():
    file_size = request.headers['Content-Length']
    start_time = time.time()
    try:
        with open(INPUT_FILE, "wb") as fp:
            receive_post_body(request.stream, file_size, fp)
    except OSError as e:
        return str(e), client.INTERNAL_SERVER_ERROR
    try:
        ret, _, _ = start_process_with_timeout([ELF_FILE], stdin=open(INPUT_FILE, "r"), stdout=open(OUTPUT_FILE, "w"), stderr=open(PERF_FILE, "w"), timeout=TIMEOUT_SECS)
    except subprocess.TimeoutExpired:
        return "elf run timeout!", client.INTERNAL_SERVER_ERROR
    end_time = time.time()
    # append return code to output file with a new line.
    with open(OUTPUT_FILE, "r") as fp:
        stdout = fp.read()
    append_nl = len(stdout) != 0 and stdout[-1] != '\n'
    with open(OUTPUT_FILE, "a") as fp:
        if append_nl:
            fp.write('\n')
        fp.write(str(ret))
    elapsed_time = (end_time - start_time)
    return "ok, elapsed {0:.2f} secs".format(elapsed_time), client.OK

# get output (stdout + return code)
@app.route("/output", methods=['GET'])
def get_output():
    with open(OUTPUT_FILE, "r") as fp:
        body = fp.read()
    return body

# get perf (stderr)
@app.route("/perf", methods=['GET'])
def get_perf():
    with open(PERF_FILE, "r") as fp:
        body = fp.read()
    return body
