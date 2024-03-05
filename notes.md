
# Изменения

```shell
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo docker run hello-world
```


```shell
sudo docker run --name some-postgres -e POSTGRES_PASSWORD=postgres --restart always -p  5432:5432 -d postgres
```


```shell
sudo docker run --name some-redis -d --restart always -p  6379:6379 redis redis-server --save  60  1 --loglevel warning
```

```shell
useradd -s /bin/true -c Pseudo_user_for_ssh_rtunnel -m -r rtunnel
sudo -u rtunnel -H ssh-keygen
scp ~rtunnel/.ssh/id_rsa.pub central-server:/tmp/

# ~rtunnel/.ssh/config

Host rtunnel
      Hostname publuc-server.example.org
      User rtunnel
      RemoteForward 0.0.0.0:9000 127.0.0.1:8000
      RemoteForward 2222 127.0.0.1:22
      ServerAliveInterval 30
      ServerAliveCountMax 5
      ExitOnForwardFailure yes

useradd -s /bin/true -c Pseudo_user_for_ssh_rtunnel -m -r rtunnel
mkdir ~rtunnel/.ssh
cat /tmp/id_rsa.pub >> ~rtunnel/.ssh/authorized_keys
chown -R rtunnel ~rtunnel

# nat
sudo -u rtunnel -H ssh -N rtunnel

# pub
netstat -ntlp | grep 2222
ssh -p2222 127.0.0.1

# systemctl daemon-reload

```


```shell
root@lenovo:/etc/systemd/system# cat rtunnel.service
[Unit]
Description=SSH Tunnel to local over tunnel to remote
After=network-online.target
Wants=network-online.target

[Service]
User=rtunnel
Type=simple
ExecStart=/usr/bin/ssh -N rtunnel
Restart=always
RestartSec=30s

[Install]
WantedBy=multi-user.target
```

```shell
root@lenovo:/etc/systemd/system# cat danone.service
[Unit]
Description=DanoneBeckend
After=network-online.target
Wants=network-online.target

[Service]
User=yunikeil
Type=simple
ExecStart=/bin/bash -c '/home/yunikeil/python/BackendDanone/Venv/bin/python /home/yunikeil/python/BackendDanone/src/main.py'
Restart=always
RestartSec=15s

[Install]
WantedBy=multi-user.target
```


k6 для нагрузочного тестирования


# !!! Доделать ограничения для полей во всех модулях !!!
# Доделать документацию по нормальному
# Доделать аннотации категорий

https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/


