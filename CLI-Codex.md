# 2. Chuẩn bị Ubuntu Server 24.04

## cài codex

```bash
sudo apt update
sudo apt install -y nodejs npm curl


node -v
npm -v

sudo npm install -g @openai/codex@latest

codex --version

codex login --device-auth
# làm theo hướng dẫn
```

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  git file binutils jq curl

python3 -m venv ~/vol3-env

source ~/vol3-env/bin/activate

python -m pip install -U pip volatility3

sudo apt update
sudo apt install -y nodejs npm curl
```