
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

k6 для нагрузочного тестирования


# !!! Доделать ограничения для полей во всех модулях !!!
# Доделать документацию по нормальному
# Доделать аннотации категорий

https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/


