---
author: "Huizhi"
title:  "2023-07-19Ubuntu上安装Docker"
date: 2023-07-19T18:31:50+08:00  
lastmod: 2023-07-30
description: "按照官网教程就可以了"
tags: ["tech","redash"]
draft: false
pin: false
thumbnail: https://picsum.photos/id/301/400/250
---


# 一、设置Docker Repository

1. 升级`apt-get`到最新

```python
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
```

2. 添加Docker的官方GPG key

```python
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

3. 设置仓库

```python
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

# 二、安装Docker Engine

1. 升级apt-get到最新

```python
sudo apt-get update
```

2. 安装最新版本的Docker Engine， containerd和Docker Compose

```python
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

3. 确保安装成功

```python
sudo docker run hello-world
```

# 三、配置Docker环境

```python
#配置log文件大小
sudo sh -c 'mkdir /etc/docker && cat > /etc/docker/daemon.json << EOF
{
  "log-driver":"json-file",
  "log-opts":{ "max-size" :"50m","max-file":"3"}
}
EOF'
#将当前用户加入docker组
sudo usermod -aG docker $USER
#启动docker服务并配置自启
sudo systemctl start docker && sudo systemctl enable docker
```

# 四、参考
1. [Docker官网安装](https://docs.docker.com/engine/install/ubuntu/)