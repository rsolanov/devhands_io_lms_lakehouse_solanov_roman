# 00-storage — Общее хранилище

Контур содержит MinIO (S3-совместимое хранилище) и Lakekeeper (Apache Iceberg REST Catalog).  
Является фундаментом всей платформы — все остальные контуры подключаются к нему через общую docker-сеть `lakehouse-shared`.

---

## Запуск и управление

### Запуск сервисов
```bash
docker compose up -d
```

### Просмотр логов
```bash
docker compose logs -f
```

### Запуск тестов:
```bash
docker compose --profile test down
docker compose --profile test up test-runner
```

### Удаление всех сервисов, volumes и сетей
```bash
docker compose down -v
docker network rm lakehouse-shared
```

## Первоначальная настройка

### Добавить minio в hosts (Windows, PowerShell от Администратора)
```powershell
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "`n127.0.0.1 minio"
```
### Проверить
```powershell
Get-Content C:\Windows\System32\drivers\etc\hosts | Select-String "minio"
```

### Создание хранилища (warehouse)
- Перейти на страницу http://localhost:8181/ui/warehouse
- Нажать "ADD WAREHOUSE"
- В появившемся окне заполнить параметры нового хранилища

#### Параметры для создания хранилища:
- Name: main_dwh
- Storage Profile: создать S3-профиль с параметрами:
  - Endpoint: http://minio:9000
  - Bucket: product-bucket
  - Region: us-east-1
  - Access Key: minioadmin
  - Secret Key: minioadmin
  - Path Style Access: true
  - Remote signing URL style: path
  - Remote Signing Enabled: false
  - Enable STS: false

# Настройка Merge-on-Read (MOR) для Iceberg таблиц
По умолчанию Iceberg использует стратегию Copy-on-Write (COW): при каждом UPDATE/DELETE
весь data-файл перезаписывается целиком. Это дорого для больших таблиц.
Merge-on-Read (MOR) — enterprise-подход: вместо перезаписи файла создаются небольшие
delete-файлы, которые мержатся с данными на лету при чтении. UPDATE/DELETE становятся быстрее.
## Способ 1 — через curl (терминал)
```bash
curl -s -X POST \
  "http://localhost:8181/catalog/v1/{warehouse_id}/namespaces/ods/tables/customers" \
  -H "Content-Type: application/json" \
  -d '{
        "identifier": {"namespace": ["ods"], "name": "customers"},
        "requirements": [],
        "updates": [
          {
              "action": "set-properties",
              "updates": {
                "write.delete.mode": "merge-on-read",
                "write.update.mode": "merge-on-read",
                "write.merge.mode": "merge-on-read"
              }
          }]
  }'
```
Успешный ответ содержит:
```json
{
  "properties": {
    "write.delete.mode": "merge-on-read",
    "write.update.mode": "merge-on-read",
    "write.merge.mode": "merge-on-read",
    "write.format.default": "PARQUET"
    }
}
```

## Способ 2 — через Swagger UI (браузер)

* Открыть http://localhost:8181/swagger-ui/
* В верхнем правом углу нажать на dropdown и выбрать **Apache Iceberg REST Catalog API**  
(URL переключится на `...?urls.primaryName=%2Fapi-docs%2Fcatalog%2Fv1%2Fopenapi.json`)
* В блоке Servers выбрать второй вариант:  
`{scheme}://{host}:{port}/{basePath} - Generic base server URL`  
и заполнить переменные:  

| Переменная | 	Значение          |
|:-----------|:-------------------|
| scheme     | 	http              |
| host       | 	localhost         |
| port       | 	8181              |
| basePath   | 	(оставить пустым) |

* Найти endpoint:

`POST /catalog/v1/{prefix}/namespaces/{namespace}/tables/{table} — Commit updates to a table`

* Нажать Try it out
* Заполнить path-параметры:

| Параметр  | 	Значение                             |
|:----------|:--------------------------------------|
| prefix    | 	a0410ba0-0abb-11f1-a663-b374b4bf9cbf |
| namespace | 	ods                                  |
| table     | 	customers                            |                        

* В поле Request body вставить:
```json
{
  "identifier": {
    "namespace": ["ods"],
    "name": "ods_customers"
  },
  "requirements": [],
  "updates": [
    {
      "action": "set-properties",
      "updates": {
        "write.delete.mode": "merge-on-read",
        "write.update.mode": "merge-on-read",
        "write.merge.mode": "merge-on-read"
      }
    }
  ]
}
```

* Нажать Execute
* Убедиться что пришёл ответ 200 и в `properties` указаны значения `merge-on-read`

## Проверка что MOR работает
```sql
-- 1. Посмотреть запись до изменения
SELECT * FROM iceberg_platform.ods.customers WHERE customer_id = 1;

-- 2. Выполнить UPDATE
UPDATE iceberg_platform.ods.customers
SET email = 'mor_test@example.com'
WHERE customer_id = 1;

-- 3. Убедиться что данные обновились корректно
SELECT * FROM iceberg_platform.ods.customers WHERE customer_id = 1;
```

Проверить наличие delete-файлов через REST API:
```bash
curl -s "http://localhost:8181/catalog/v1/{warehouse_id}/namespaces/ods/tables/customers" \
| python3 -m json.tool | grep -A 3 "delete\|position\|equality"
```
В ответе должны появиться:
```
"added-position-delete-files": "1"
"total-delete-files": "1"
"total-position-deletes": "1"
```

Это подтверждает что UPDATE прошёл в режиме MOR — оригинальный файл не перезаписан, а создан отдельный delete-файл.

---

## Запуск тестов

```bash
docker compose --profile test down
docker compose --profile test up test-runner
```

## Применение MOR для всех таблиц (batch)
```bash
WAREHOUSE_ID="a0410ba0-0abb-11f1-a663-b374b4bf9cbf"

for namespace in ods dds dm; do
  tables=$(curl -s "http://localhost:8181/catalog/v1/${WAREHOUSE_ID}/namespaces/${namespace}/tables" \\
    | python3 -c "import sys,json; [print(t['name']) for t in json.load(sys.stdin)['identifiers']]")
  for table in $tables; do
    echo "Setting MOR for ${namespace}.${table}..."
    curl -s -X POST \\
      "http://localhost:8181/catalog/v1/${WAREHOUSE_ID}/namespaces/${namespace}/tables/${table}" \\
      -H "Content-Type: application/json" \\
      -d "{
        \\"identifier\\": {\\"namespace\\": [\\"${namespace}\\"], \\"name\\": \\"${table}\\"},
        \\"requirements\\": [],
        \\"updates\\": [{\\"action\\": \\"set-properties\\", \\"updates\\": {
          \\"write.delete.mode\\": \\"merge-on-read\\",
          \\"write.update.mode\\": \\"merge-on-read\\",
          \\"write.merge.mode\\": \\"merge-on-read\\"
        }}]
      }" | python3 -m json.tool | grep -A 5 '"properties": {' | head -6
    echo "---"
  done
done
```