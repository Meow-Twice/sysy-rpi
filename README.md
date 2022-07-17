# SysY RPi

通过 POST API 上传 elf 文件和 in 文件，在树莓派上执行 elf 并通过 GET API 取回 stdout 和 stderr 结果。

API 说明详见 `index.html` 。

## Requirements

- Raspberry Pi 4B
- Python 3
- SysY library at `/usr/share/sylib/`
  - `sylib.c` and `sylib.h`
  - static library binary `sylib.a`
  - static library from cross compiler (if needed), e.g. `arm-linux-gnueabihf-sylib.a`

## Installation

Run following commands with *root shell*: (you can use `sudo -i` to enter root shell)

```shell
# copy files
cp scripts/sysy-elf.sh /usr/bin/
mkdir /opt/sysy-rpi/
cp -t /opt/sysy-rpi/ app.py index.html sysy-rpi.service
cd /opt/sysy-rpi/
# setup python virtual environment
python3 -m virtualenv .venv
source .venv/bin/activate
pip install flask uwsgi -i https://pypi.tuna.tsinghua.edu.cn/simple
# setup system service
ln -s sysy-rpi.service /etc/systemd/system/sysy-rpi.service
systemctl daemon-reload
# create data directory and let non-root user access it
mkdir data
chmod 777 data
# start the service
systemctl start sysy-rpi
systemctl enable sysy-rpi # start on boot
```