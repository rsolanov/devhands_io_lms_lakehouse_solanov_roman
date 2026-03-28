import os
from faker import Faker
import pandas as pd
from pyspark.sql import SparkSession
import random
from datetime import datetime, timedelta

def get_spark_session():
    """
    Инициализирует и возвращает Spark сессию, используя конфигурацию,
    в точности копирующую рабочий пример из Jupyter ноутбука.
    """
    print("Инициализация Spark сессии...")

    catalog_name = "lakehouse"
    warehouse_name = os.getenv("ICEBERG_WAREHOUSE_NAME", "product_dw")  # ← ДОБАВЛЕНО
    s3_endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
    iceberg_catalog_uri = os.getenv("ICEBERG_CATALOG_URI", "http://lakekeeper:8181")
    s3_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    s3_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

    print(f"Конфигурация каталога:")
    print(f"  Catalog: {catalog_name}")
    print(f"  Warehouse: {warehouse_name}")  # ← ДОБАВЛЕНО для отладки
    print(f"  URI: {iceberg_catalog_uri}")

    spark = (
        SparkSession.builder.appName("ProductDataGenerator")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config(f"spark.sql.catalog.{catalog_name}", "org.apache.iceberg.spark.SparkCatalog")
        .config(f"spark.sql.catalog.{catalog_name}.catalog-impl", "org.apache.iceberg.rest.RESTCatalog")
        .config(f"spark.sql.catalog.{catalog_name}.uri", f"{iceberg_catalog_uri}/catalog")
        .config(f"spark.sql.catalog.{catalog_name}.warehouse", warehouse_name)  # ← ИСПРАВЛЕНО
        .config(f"spark.sql.catalog.{catalog_name}.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config(f"spark.sql.catalog.{catalog_name}.s3.endpoint", s3_endpoint)
        .config(f"spark.sql.catalog.{catalog_name}.s3.access-key-id", s3_access_key)
        .config(f"spark.sql.catalog.{catalog_name}.s3.secret-access-key", s3_secret_key)
        .config(f"spark.sql.catalog.{catalog_name}.s3.path-style-access", "true")
        .config("spark.sql.legacy.parquet.nanosAsLong", "true")
        .config("spark.sql.defaultCatalog", catalog_name)
        .getOrCreate()
    )

    # Добавляем уровень логирования, как вы просили
    spark.sparkContext.setLogLevel("WARN")

    print("Spark сессия успешно инициализирована.")
    return spark

def generate_customers(num_records):
    print(f"Генерация {num_records} записей клиентов...")
    fake = Faker()
    return pd.DataFrame([{'customer_id': i, 'first_name': fake.first_name(), 'last_name': fake.last_name(), 'email': fake.email(), 'registration_date': fake.date_between(start_date='-2y', end_date='today')} for i in range(num_records)])

def generate_products(num_records):
    print(f"Генерация {num_records} записей продуктов...")
    fake = Faker()
    return pd.DataFrame([{'product_id': i, 'product_name': fake.catch_phrase(), 'category': random.choice(['Electronics', 'Books', 'Home Goods', 'Clothing']), 'price': round(random.uniform(5.5, 250.99), 2)} for i in range(num_records)])

def generate_orders(num_records, customer_ids, product_ids):
    print(f"Генерация {num_records} записей заказов...")
    return pd.DataFrame([{'order_id': i, 'customer_id': random.choice(customer_ids), 'product_id': random.choice(product_ids), 'quantity': random.randint(1, 5), 'order_date': datetime.now() - timedelta(days=random.randint(0, 365))} for i in range(num_records)])

def publish_to_iceberg(spark, df, table_name, namespace, catalog_name):
    full_table_name = f"{catalog_name}.{namespace}.{table_name}"
    print(f"Сохранение данных в таблицу: {full_table_name} (режим: createOrReplace)...")
    try:
        spark_df = spark.createDataFrame(df)
        spark_df.writeTo(full_table_name).createOrReplace()
        print(f"Таблица {full_table_name} успешно сохранена.")
    except Exception as e:
        print(f"Ошибка при сохранении таблицы {full_table_name}: {e}")
        raise

def main():
    print("Запуск генератора продуктовых данных...")
    spark = None
    try:
        spark = get_spark_session()
        CATALOG_NAME = "lakehouse"
        NAMESPACE = "product"
        print(f"Проверка/создание неймспейса '{NAMESPACE}' в каталоге '{CATALOG_NAME}'...")
        spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {CATALOG_NAME}.{NAMESPACE}")

        customers_pd = generate_customers(1000)
        products_pd = generate_products(200)
        orders_pd = generate_orders(5000, customers_pd['customer_id'].tolist(), products_pd['product_id'].tolist())

        publish_to_iceberg(spark, customers_pd, 'customers', NAMESPACE, CATALOG_NAME)
        publish_to_iceberg(spark, products_pd, 'products', NAMESPACE, CATALOG_NAME)
        publish_to_iceberg(spark, orders_pd, 'orders', NAMESPACE, CATALOG_NAME)

        print("Генерация и публикация данных успешно завершены.")

    except Exception as e:
        print(f"Произошла фатальная ошибка во время выполнения: {e}")
        raise
    finally:
        if spark:
            print("Остановка Spark сессии...")
            spark.stop()

if __name__ == "__main__":
    main()