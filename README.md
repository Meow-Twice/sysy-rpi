# SysY 树莓派服务程序

与 [评测机](https://github.com/Meow-Twice/sysy-test) 对接的树莓派服务程序。 API 说明详见 `index.html` 。

## Requirements

- Raspberry Pi 4B
- Python 3
- SysY library at `/usr/share/sylib/`
  - `sylib.c` and `sylib.h`
  - static library binary `sylib.a`

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
ln -s /opt/sysy-rpi/sysy-rpi.service /etc/systemd/system/sysy-rpi.service
systemctl daemon-reload
# create data directory and let non-root user access it
mkdir data
chmod 777 data
# start the service
systemctl start sysy-rpi
systemctl enable sysy-rpi # start on boot
```