# Выпускная проектная работа на тему: Современная платформа данных построенная по архитектуре Lakehouse

Эта проектная работа представляет собой реализацию современной аналитической платформы данных по архитектуре Lakehouse. Основная цель — на практике освоить полный цикл работы с данными, от их генерации до подготовки аналитических витрин, используя стек технологий: Spark, Trino, Iceberg, dbt, Airflow и MinIO.

---

### Цели проекта
*   Показать на практике работу ключевых инструментов современного стека данных.
*   Реализовать Lakehouse архитектуру, где единое S3-хранилище используется и как Data Lake, и как основа для структурированного хранилища.
*   Освоить Apache Iceberg как табличный формат, обеспечивающий ACID-транзакции, эволюцию схемы и time-travel поверх S3.
*   Построить полноценные ELT-пайплайны с помощью dbt для трансформации данных.
*   Настроить оркестрацию потоков данных с помощью Apache Airflow.
*   Смоделировать многослойное хранилище (ODS, DDS, DM) по классическим принципам.

### Концепция
Архитектура эмулирует реальную корпоративную среду, где четко разделены зоны ответственности между хранением, генерацией, обработкой и потреблением данных. Система состоит из четырех взаимосвязанных контуров:

1.  **Контур хранения данных (Data Storage System):** Единый фундамент Lakehouse. Обеспечивает физическое хранение (S3) и логическое управление метаданными (Iceberg Catalog) для всех остальных контуров.
2.  **Продуктовый контур (Product System):** Эмулирует работу бизнес-приложения. PySpark генерирует данные и публикует их в свою изолированную область хранилища.
3.  **Аналитический контур (Data Platform):** Отвечает за трансформацию данных. Инструменты платформы (dbt, Trino) забирают "сырые" данные, очищают их и формируют слои хранилища (ODS, DDS, DM) в аналитической области.
4.  **Корпоративная система отчетности (BI Platform):** Предоставляет бизнес-пользователям доступ к результатам. Superset использует данные из готовых витрин для построения дашбордов.

### Стек технологий
| Категория | Инструмент | Роль в проекте |
| :--- | :--- | :--- |
| Хранение (Storage) | MinIO | S3-совместимое озеро данных для всех слоев. |
| Табличный формат | Apache Iceberg | Обеспечивает структуру и ACID-транзакции для таблиц поверх S3. |
| Обработка (Batch) | PySpark | Эмуляция работы продуктового сервиса и публикация данных. |
| Трансформация (ELT)| dbt | Управление SQL-моделями для построения слоев ODS, DDS, DM. |
| Движок запросов | Trino | Выполняет SQL-запросы от dbt и BI-систем к Iceberg-таблицам. |
| Оркестрация | Apache Airflow | Управление расписанием и зависимостями всех пайплайнов. |
| Визуализация (BI) | Apache Superset | Потребление данных из витрин (DM) для построения дашбордов. |

### Архитектура
Архитектура проекта основана в нотации C4 и четко разделяет систему на функциональные контуры.

![system_architecture.drawio.svg](docs/images/system_architecture.drawio.svg)

#### 1. Контур хранения данных (Data Storage System)

Это фундаментальный слой платформы, реализующий концепцию Lakehouse. Он отвечает за
надёжное хранение данных и предоставляет единый интерфейс доступа к ним для всех
остальных контуров.

Архитектура хранения построена на базе **единого сервера каталога (Lakekeeper)**,
который управляет двумя независимыми **Хранилищами (Warehouses)**. Эти хранилища
функционируют как две отдельные базы данных: они имеют разное физическое расположение
(разные S3-бакеты) и логическую изоляцию, но обслуживаются одним инстансом каталога.
При первом запуске сервис **lakekeeper-bootstrap** автоматически инициализирует каталог
и создаёт оба Warehouse с привязкой к соответствующим S3-бакетам.

| Компонент | Технология | Роль |
| :--- | :--- | :--- |
| **Data Lake Storage** | MinIO (S3 API) | Физическая инфраструктура хранения. Данные жёстко разделены: файлы продуктового контура хранятся в `product-bucket`, платформенного — в `platform-bucket`. |
| **Iceberg REST Catalog** | Lakekeeper | Единый сервис каталога. Выступает центральной точкой входа для движков (Spark, Trino). Управляет транзакциями и метаданными для всех подключённых хранилищ (Warehouses), маршрутизирует запросы к физическим S3-бакетам. |
| **Metadata Store** | PostgreSQL | База данных, используемая Lakekeeper для хранения состояния каталога и ссылок на снапшоты таблиц. |
| **Product Data Warehouse** | Iceberg Warehouse (`product_dw`) | Отдельная база данных (Warehouse) для «сырых» данных. Сконфигурирована в каталоге с привязкой к `product-bucket`. |
| **Platform Data Warehouse** | Iceberg Warehouse (`dwh_dw`) | Отдельная база данных (Warehouse) для аналитики (слои ODS, DDS, DM). Сконфигурирована в каталоге с привязкой к `platform-bucket`. |

---

#### 2. Продуктовый контур (Product System)

Этот контур эмулирует работу реального бизнес-приложения: генерирует синтетические
операционные данные и публикует их в озеро как структурированные Iceberg-таблицы.
Взаимодействие с хранилищем осуществляется исключительно через Iceberg REST API —
прямой доступ к S3 из бизнес-логики контура отсутствует.

Оркестратор **Airflow** по расписанию запускает **PySpark**-приложение через
DockerOperator. Приложение формирует пакет новых бизнес-событий и фиксирует их в
**Product Data Warehouse** через **Lakekeeper**. Контур имеет собственную
изолированную базу метаданных (PostgreSQL) и взаимодействует с другими контурами
исключительно через общий слой хранения.

| Компонент | Технология | Роль |
| :--- | :--- | :--- |
| **Orchestrator** | Apache Airflow | Управление расписанием запуска PySpark-приложения через DockerOperator и мониторинг статуса выполнения пайплайна. |
| **Data Generator** | PySpark (Apache Spark) | Генерация синтетических бизнес-данных и их публикация в Product Data Warehouse через Iceberg REST API. |
| **Airflow Metadata DB** | PostgreSQL | Изолированная база данных для хранения состояния Airflow: DAG-ов, задач и журналов выполнения. |

---

#### 3. Аналитический контур (Data Platform)

Этот контур отвечает за трансформацию «сырых» данных продуктового контура в
структурированные аналитические слои (ODS → DDS → DM). Все вычисления делегируются
распределённому SQL-движку **Trino**, который взаимодействует с обоими Warehouse через
единый каталог **Lakekeeper**.

Оркестратор **Airflow** запускает **dbt** через DockerOperator: dbt на основе
SQL-моделей формирует и отправляет SQL-запросы в **Trino**. Trino читает данные из
*Product Data Warehouse* и записывает результаты трансформаций в *Platform Data
Warehouse*. Физическое хранение данных каждого слоя (ODS, DDS, DM) осуществляется в
`platform-bucket` в формате Iceberg с поддержкой ACID-транзакций и режима
Merge-on-Read (MOR). Контур имеет собственную изолированную базу метаданных
(PostgreSQL).

| Компонент | Технология | Роль |
| :--- | :--- | :--- |
| **Orchestrator** | Apache Airflow | Управление расписанием запуска dbt-пайплайнов через DockerOperator и контроль зависимостей между задачами трансформации. |
| **ELT Engine** | dbt (адаптер dbt-trino) | Формирование и отправка SQL-запросов в Trino на основе описанных моделей. Обеспечивает построение слоёв ODS, DDS, DM и тестирование качества данных. |
| **Query Engine** | Trino | Выполнение распределённых SQL-запросов: чтение из *Product Data Warehouse*, запись в *Platform Data Warehouse*. Взаимодействует с Lakekeeper по Iceberg REST API, с MinIO — по протоколу S3. |
| **Airflow Metadata DB** | PostgreSQL | Изолированная база данных для хранения состояния Airflow аналитического контура. |

---

#### 4. Корпоративная система отчётности (BI Platform)

Этот контур замыкает цепочку обработки данных, предоставляя бизнес-пользователям
доступ к готовым аналитическим витринам через визуальный интерфейс. Контур является
потребителем данных и не выполняет никаких трансформаций.

**Apache Superset** выступает единственным компонентом контура и делегирует все
запросы SQL-движку **Trino**, который входит в состав аналитического контура. Superset
не хранит аналитические данные самостоятельно: при построении дашборда или выполнении
запроса в SQL Lab формируется SQL-запрос, передаваемый в Trino, который считывает
файлы витрин (DM) из `platform-bucket` через каталог **Lakekeeper**. Метаданные
самого Superset (определения дашбордов, подключения, пользователи) хранятся в
изолированной базе данных **PostgreSQL** данного контура.

| Компонент | Технология | Роль |
| :--- | :--- | :--- |
| **BI Tool** | Apache Superset | Предоставление интерфейса для построения дашбордов и работы с SQL Lab. Делегирует выполнение всех запросов в Trino и не хранит аналитические данные самостоятельно. |
| **BI Metadata DB** | PostgreSQL | Изолированная база данных для хранения метаданных Superset: определений дашбордов, подключений к источникам данных, пользователей и настроек. |
##### Подключение Superset к Trino

Подключение к Trino настраивается в интерфейсе Superset после первого входа.

1. Выполняется вход в Superset по адресу **http://localhost:8088** (логин: `admin`, пароль: `admin`).
2. В меню выбирается **Settings → Database Connections → + Database**.
3. В списке баз данных выбирается **Trino**.
4. В поле **SQLAlchemy URI** указывается строка подключения:
   ```
   trino://admin@trino-coordinator:8080/iceberg_platform
   ```
5. Подключение проверяется кнопкой **Test Connection** и сохраняется кнопкой **Connect**.

После сохранения подключения в **SQL Lab** доступны каталог `iceberg_platform` и все
схемы аналитического хранилища (`ods`, `dds`, `dm`).

> Для доступа к продуктовым таблицам (только чтение) указывается отдельное подключение
> с URI `trino://admin@trino-coordinator:8080/iceberg_product`.
---

## Развёртывание и эксплуатация

### Требования

| Параметр | Минимум |
| :--- | :--- |
| Docker | 20.10+ |
| Docker Compose | 2.0+ (плагин `docker compose`) |
| RAM | 16 GB |
| Дисковое пространство | 50 GB |

### Порядок развёртывания

#### Шаг 1. Клонирование репозитория

```bash
git clone <repository-url>
cd data-lakehouse-platform
```

#### Шаг 2. Инициализация сети
Перед первым запуском необходимо создать общую Docker-сеть, которую используют все контуры платформы:

```bash
chmod +x scripts/*.sh
./scripts/setup-network.sh
```

#### Шаг 3. Запуск платформы
```bash
./scripts/start-all.sh
```
Скрипт последовательно поднимает все четыре контура в правильном порядке и ожидает готовности каждого из них перед переходом к следующему.

#### Шаг 4. Проверка состояния
```bash
./scripts/status.sh
```

---

### Автономное развёртывание в изолированной сети

При наличии сетевых ограничений (корпоративный прокси, нестабильное соединение, полностью изолированная среда) все необходимые Docker-образы можно загрузить вручную, минуя Docker Hub и реестры пакетов.

Образы разделены на две группы: **базовые** (публичные образы без модификаций) и **кастомные** (собранные в рамках проекта).

#### Базовые образы

Загрузите архивы и выполните команду `docker load -i` для каждого из них:

| Образ                                                | Ссылка для загрузки                                                                               | Назначение                                 |
|:-----------------------------------------------------|:--------------------------------------------------------------------------------------------------|:-------------------------------------------|
| `minio/minio:RELEASE.2025-09-07T16-13-09Z`           | [minio-minio-RELEASE.2025-09-07T16-13-09Z.tar](https://disk.yandex.ru/d/dkn-H8hBl_shwA)           | Установка                                  |
| `minio/mc:RELEASE.2025-08-13T08-35-41Z`              | [minio-mc-RELEASE.2025-08-13T08-35-41Z.tar](https://disk.yandex.ru/d/PYjI229fd_Cc8g)              | Установка                                  |
| `postgres:18`                                        | [postgres-18.tar](https://disk.yandex.ru/d/yCWWkjnNMbTOYQ)                                        | Установка                                  |
| `curlimages/curl:8.5.0`                              | [curlimages-curl-8.5.0.tar](https://disk.yandex.ru/d/zo0FmzVmlUju6A)                              | Установка                                  |
| `vakamo/lakekeeper:db5303c2-amd64`                   | [vakamo-lakekeeper-db5303c2-amd64.tar](https://disk.yandex.ru/d/0sJR72Oh9Miigg)                   | Установка                                  |
| `trinodb/trino:479`                                  | [trinodb-trino-479.tar](https://disk.yandex.ru/d/R3EpQyk729RUdA)                                  | Только для разработки (пересборки образов) |
| `apache/airflow:2.11.0`                              | [apache-airflow-2.11.0.tar](https://disk.yandex.ru/d/jL7dOKFVXhjecA)                              | Только для разработки (пересборки образов) |
| `apache/spark:3.5.0-scala2.12-java11-python3-ubuntu` | [apache-spark-3.5.0-scala2.12-java11-python3-ubuntu.tar](https://disk.yandex.ru/d/0hY95P4iPIFVYQ) | Только для разработки (пересборки образов) |
| `apache/superset:6.0.0`                              | [apache-superset-6.0.0.tar](https://disk.yandex.ru/d/hQop8tTVh4muWg)                              | Только для разработки (пересборки образов) |
| `python:3.12-slim`                                   | [python-3.12.12-slim.tar](https://disk.yandex.ru/d/yalOCab7sUEFGA)                                | Только для разработки (пересборки образов) |

```bash
# Загрузка всех базовых образов одной командой (из директории с архивами)
for f in *.tar; do
  echo "Loading $f..."
  docker load -i "$f"
done

```

#### Кастомные образы

Кастомные образы собираются поверх базовых и включают все зависимости проекта (pip-пакеты, конфигурацию, плагины). Они также доступны для загрузки, что позволяет полностью исключить сборку из исходников:

| Архив | Образы внутри | Ссылка для загрузки |
| :--- | :--- | :--- |
| `product-domain-airflow.tar` | `01-product-domain-airflow-webserver`<br>`01-product-domain-airflow-scheduler`<br>`01-product-domain-airflow-init` | https://disk.yandex.ru/d/Oi5wTXJmMxz3yA |
| `product-domain-spark.tar` | `product-domain/spark-master:3.5.0`<br>`product-domain/spark-worker:3.5.0` | https://disk.yandex.ru/d/GnG1Bf3TKglrUA |
| `data-platform-airflow.tar` | `02-data-platform-airflow-webserver`<br>`02-data-platform-airflow-scheduler`<br>`02-data-platform-airflow-init` | https://disk.yandex.ru/d/5sSTsxzWocz4mg |
| `data-platform-trino.tar` | `02-data-platform-trino-coordinator`<br>`02-data-platform-trino-worker-1`<br>`02-data-platform-trino-worker-2`<br>`02-data-platform-trino-worker-3` | https://disk.yandex.ru/d/UA7BLku5a00gYw |
| `data-platform-dbt.tar` | `platform-dbt:latest` | https://disk.yandex.ru/d/Jj7PPRzg_idKFA |
| `bi-superset.tar` | `03-bi-superset` | https://disk.yandex.ru/d/_27OVTiWmB62tw |

```bash
# Загрузка всех кастомных образов (из директории с архивами)
for f in *.tar; do
  echo "Loading $f..."
  docker load -i "$f"
done

```

> После загрузки кастомных образов команды `docker compose up` и `./scripts/start-all.sh` будут использовать их напрямую, **без выполнения сборки** (`docker compose build`).

> ⚠️ **Важно:** после загрузки образов через `docker load` запуск каждого контура
> выполняется с флагами `--pull never --no-build` — это исключает обращение
> к внешним реестрам и пересборку образов из исходников.
>
> **Linux / macOS / WSL / Git Bash:**
> ```bash
> COMPOSE_MODE=offline ./scripts/start-all.sh
> ```
>
> PowerShell (Windows):
> ```powershell
> cd 00-storage; docker compose up -d --pull never --no-build; cd ..
> cd 01-product-domain; docker compose up -d --pull never --no-build; cd ..
> cd 02-data-platform; docker compose up -d --pull never --no-build; cd ..
> cd 03-bi; docker compose up -d --pull never --no-build; cd ..
> ```
 
### Доступ к сервисам

| Сервис           | URL                   | Логин          | Пароль     |
|:-----------------|:----------------------|:---------------|:-----------|
| MinIO Console    | http://localhost:9001 | minioadmin     | minioadmin |
| Lakekeeper UI    | http://localhost:8181 | —              | —          |
| Spark Master UI  | http://localhost:8080 | —              | —          |
| Product Airflow  | http://localhost:8090 | admin          | admin      |
| Trino UI         | http://localhost:8085 | admin          | —          |
| Platform Airflow | http://localhost:8091 | admin          | admin      |
| Superset         | http://localhost:8088 | admin          | admin      |

### Управление платформой
Все операционные скрипты расположены в директории `scripts/`.

#### Запуск платформы `start-all.sh`

Последовательно запускает все четыре контура в строго определённом порядке. На каждом этапе скрипт блокируется и ожидает HTTP-готовности ключевых сервисов, прежде чем перейти к следующему контуру.

```text
Storage Layer → Product Domain → Data Platform → BI Layer
```

#### Остановка платформы `stop-all.sh`
Останавливает все контуры в обратном порядке (BI → Data Platform → Product Domain → Storage). Данные и тома сохраняются.

```bash
./scripts/stop-all.sh
```

#### Состояние сервисов `status.sh`
Выводит статус каждого сервиса, проверяя доступность HTTP-эндпоинтов и наличие запущенных контейнеров.

```bash
./scripts/status.sh
```

#### Просмотр логов `logs.sh`
Позволяет подключиться к потоку логов конкретного контура или отдельного сервиса.

```bash
# Все сервисы контура
./scripts/logs.sh [storage|product|platform|bi]

# Конкретный сервис
./scripts/logs.sh platform trino-coordinator
./scripts/logs.sh storage minio
./scripts/logs.sh product airflow-scheduler
```

#### Инициализация сети `setup-network.sh`
Создаёт общую Docker-сеть lakehouse-shared. Выполняется однократно перед первым запуском платформы. Повторный запуск безопасен.

```bash
./scripts/setup-network.sh
```

#### Полная очистка `clean-all.sh`
Останавливает все сервисы и удаляет все тома с данными. Используется для полного сброса окружения к начальному состоянию.

> ⚠️ Внимание: операция необратима. Все данные в MinIO, PostgreSQL и прочих томах будут уничтожены.

```bash
./scripts/clean-all.sh
```
### Сохранение кастомных образов в архив
```shell
docker save 01-product-domain-airflow-webserver 01-product-domain-airflow-scheduler 01-product-domain-airflow-init -o product-domain-airflow.tar
docker save product-domain/spark-master:3.5.0 product-domain/spark-worker:3.5.0 -o product-domain-spark.tar
docker save 02-data-platform-trino-coordinator 02-data-platform-trino-worker-1 02-data-platform-trino-worker-2 02-data-platform-trino-worker-3 -o data-platform-trino.tar
docker save 02-data-platform-airflow-webserver 02-data-platform-airflow-scheduler 02-data-platform-airflow-init -o data-platform-airflow.tar  
docker save platform-dbt:latest -o data-platform-dbt.tar
docker save 03-bi-superset -o bi-superset.tar
```

### Восстановление образов из файлов
```shell
docker load -i product-domain-airflow.tar
docker load -i product-domain-spark.tar
docker load -i data-platform-trino.tar
docker load -i data-platform-airflow.tar
docker load -i data-platform-dbt.tar
docker load -i bi-superset.tar
```