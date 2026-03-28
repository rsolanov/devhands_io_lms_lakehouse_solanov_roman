### Пересборка всех образов
```shell
docker compose up -d --build
```

### Пересборка docker-образа spark и spark-контейнеров
```shell
docker compose up -d --build spark-master spark-worker
```

### Пересборка всех контейнеров
```shell
# 1. Остановить и удалить контейнеры
docker-compose down

# 2. Удалить старые образы
docker rmi 01-product-domain-spark-master 01-product-domain-spark-worker

# 3. Пересобрать образы с новыми именами
docker-compose build --no-cache spark-master spark-worker

# 4. Проверить, что образы созданы с правильными именами
docker images | grep product-domain

# 5. Запустить все сервисы
docker-compose up -d

# 6. Подождать ~1 минуту для healthcheck
sleep 60

# 7. Проверить статус всех контейнеров
docker-compose ps

# 8. Проверить логи Spark Master
docker-compose logs spark-master | tail -20

# 9. Проверить логи Spark Worker
docker-compose logs spark-worker | tail -20
```