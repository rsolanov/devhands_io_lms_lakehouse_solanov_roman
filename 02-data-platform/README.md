# Работа с сервисами
## Trino
### Перезапуск контейнеров при добавлении/изменении параметров окружения Trino
```bash
docker compose restart trino-coordinator trino-worker-1 trino-worker-2 trino-worker-3
```

## Airflow
### Пересоздание контейнеров при изменении переменных окружения Airflow
```bash
docker compose up -d --force-recreate airflow-webserver airflow-scheduler
```

## dbt
### Пересоздание образа dbt
```bash
docker compose build dbt
```
### Запуск команды в образе dbt
```bash
docker run --rm   --network lakehouse-shared   -e DBT_TRINO_HOST=trino-coordinator   -e DBT_TRINO_PORT=8080   -e DBT_TRINO_DATABASE=iceberg_platform   -e DBT_TRINO_SCHEMA=ods   platform-dbt:latest   dbt run --profiles-dir /root/.dbt --project-dir /usr/app/dbt 2>&1
```
# Подключение к Trino через DBeaver

## Обзор

В нашем стеке Trino выполняет роль универсального query engine над данными в MinIO (S3-совместимое хранилище) через Iceberg REST каталог (Lakekeeper).

Доступные каталоги:
| Каталог | Warehouse | Описание |
|---|---|---|
| `iceberg_product` | `product_dw` | Исходные данные (источник) |
| `iceberg_platform` | `dwh_dw` | Витрины данных (ODS → DDS → DM) |

---

## Требования

- [DBeaver Community](https://dbeaver.io/download/) версии 23.x и выше
- Доступ к хосту где запущен Docker (локально или по сети)

---

## Шаг 1: Установка драйвера Trino

DBeaver умеет скачать драйвер автоматически, но если этого не произошло — сделайте вручную.

1. Откройте **Database → Driver Manager**
2. Найдите **Trino** в списке
3. Нажмите **Edit** → вкладка **Libraries**
4. Нажмите **Download/Update** — DBeaver скачает официальный JDBC драйвер

---

## Шаг 2: Создание подключения

### 2.1 Открыть мастер подключения

**Database → New Database Connection** (или `Ctrl+Shift+N`)

### 2.2 Выбрать драйвер

В поиске введите **Trino** → выберите → нажмите **Next**

### 2.3 Заполнить параметры подключения

| Параметр | Значение |
|---|---|
| **Host** | `localhost` |
| **Port** | `8085` |
| **Database/Catalog** | `iceberg_platform` |
| **Username** | `admin` |
| **Password** | *(оставить пустым)* |

> ⚠️ Если подключаетесь не с локальной машины — замените `localhost` на IP хоста где запущен Docker.

### 2.4 Проверить подключение

Нажмите **Test Connection** — должно появиться:
```
Connected to Trino version 435

```

### 2.5 Сохранить подключение

Нажмите **Finish**

---

## Шаг 3: Выполнение запросов

Откройте SQL редактор: **SQL Editor → Open SQL Script** (или `F3`)

### Примеры запросов

#### Посмотреть все доступные схемы
```sql
SHOW SCHEMAS IN iceberg_platform;

```

#### Посмотреть таблицы в ODS
```sql
SHOW TABLES IN iceberg_platform.ods;

```

#### Запрос к витрине клиентов
```sql
SELECT *
FROM iceberg_platform.ods.customers
LIMIT 100;

```

#### Запрос к витрине заказов
```sql
SELECT *
FROM iceberg_platform.ods.orders
LIMIT 100;

```

#### Запрос к витрине продуктов
```sql
SELECT *
FROM iceberg_platform.ods.products
LIMIT 100;

```

#### Посмотреть исходные данные (продуктовый контур)
```sql
SELECT *
FROM iceberg_product.product.customers
LIMIT 10;

```