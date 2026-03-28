import sys
import requests
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError, TableAlreadyExistsError
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType, IntegerType, DateType
import pyarrow as pa
from datetime import date


def print_section(title):
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)


def check_services():
    print_section("  Pre-flight checks")

    response = requests.get("http://lakekeeper-catalog:8181/health", timeout=5)
    print(f"✅ Lakekeeper health: {response.status_code}")

    response = requests.get("http://minio:9000/minio/health/live", timeout=5)
    print(f"✅ MinIO health: {response.status_code}")


def get_catalog(warehouse_name):
    return load_catalog(
        "lakekeeper",
        **{
            "type": "rest",
            "uri": "http://lakekeeper-catalog:8181/catalog",
            "warehouse": warehouse_name,
            "s3.endpoint": "http://minio:9000",
            "s3.access-key-id": "minioadmin",
            "s3.secret-access-key": "minioadmin",
            "s3.path-style-access": "true",
            "s3.region": "us-east-1",
            "py-io-impl": "pyiceberg.io.fsspec.FsspecFileIO",
            "s3.signer-enabled": False,
        }
    )


def create_test_schema():
    return Schema(
        NestedField(1, "id", IntegerType(), required=True),
        NestedField(2, "name", StringType(), required=True),
        NestedField(3, "department", StringType(), required=True),
        NestedField(4, "salary", IntegerType(), required=True),
        NestedField(5, "hire_date", DateType(), required=True),
    )


def create_test_data():
    pa_schema = pa.schema([
        pa.field("id", pa.int32(), nullable=False),
        pa.field("name", pa.string(), nullable=False),
        pa.field("department", pa.string(), nullable=False),
        pa.field("salary", pa.int32(), nullable=False),
        pa.field("hire_date", pa.date32(), nullable=False),
    ])

    return pa.table({
        "id": pa.array([1, 2, 3, 4, 5], type=pa.int32()),
        "name": pa.array([
            "Алексей Иванов",
            "Мария Петрова",
            "Дмитрий Сидоров",
            "Елена Козлова",
            "Игорь Новиков"
        ], type=pa.string()),
        "department": pa.array([
            "Data Engineering",
            "Analytics",
            "ML Engineering",
            "Data Science",
            "Platform"
        ], type=pa.string()),
        "salary": pa.array([150000, 120000, 180000, 160000, 140000], type=pa.int32()),
        "hire_date": pa.array([
            date(2023, 1, 15),
            date(2023, 3, 20),
            date(2022, 11, 10),
            date(2023, 2, 5),
            date(2023, 4, 1)
        ], type=pa.date32()),
    }, schema=pa_schema)


def test_warehouse(warehouse_name, namespace_name, table_name):
    print_section(f"  Testing Warehouse: {warehouse_name}")

    print(f"\n  Connecting to catalog (warehouse={warehouse_name})...")
    catalog = get_catalog(warehouse_name)
    print(f"✅ Connected to warehouse: {warehouse_name}")

    print(f"\n  Creating namespace '{namespace_name}'...")
    try:
        catalog.create_namespace(namespace_name)
        print(f"✅ Namespace '{namespace_name}' created")
    except NamespaceAlreadyExistsError:
        print(f"ℹ️  Namespace '{namespace_name}' already exists")

    print(f"\n  Listing namespaces in {warehouse_name}:")
    namespaces = catalog.list_namespaces()
    for ns in namespaces:
        print(f"     {'.'.join(ns)}")

    print(f"\n  Creating table '{namespace_name}.{table_name}'...")
    schema = create_test_schema()
    full_table_name = f"{namespace_name}.{table_name}"

    try:
        table = catalog.create_table(full_table_name, schema=schema)
        print(f"✅ Table '{full_table_name}' created")
    except TableAlreadyExistsError:
        print(f"ℹ️  Table already exists, loading...")
        table = catalog.load_table(full_table_name)

    print(f"\n  Inserting test data into {full_table_name}...")
    data = create_test_data()
    table.append(data)
    print(f"✅ {len(data)} records inserted")

    print(f"\n  Reading data from {full_table_name}...")
    scan = table.scan()
    result = scan.to_arrow()
    df = result.to_pandas()

    print(f"\nTable content ({warehouse_name}):")
    print(df.to_string(index=False))
    print(f"\n✅ Total records: {len(df)}")

    print(f"\n  Analytics - Salary by department ({warehouse_name}):")
    analytics = df.groupby('department').agg({
        'salary': ['count', 'mean', 'min', 'max']
    }).round(0)
    analytics.columns = ['count', 'avg_salary', 'min_salary', 'max_salary']
    analytics = analytics.sort_values('avg_salary', ascending=False)
    print(analytics.to_string())

    print(f"\n  Table metadata ({warehouse_name}):")
    print(f"   Location: {table.location()}")
    print(f"   Schema fields: {len(table.schema().fields)}")

    if table.current_snapshot():
        print(f"   Current snapshot: {table.current_snapshot().snapshot_id}")

    metadata = table.metadata
    print(f"   Format version: {metadata.format_version}")
    print(f"   Table UUID: {metadata.table_uuid}")

    print(f"\n✅ Warehouse '{warehouse_name}' test completed successfully!")
    return True


def main():
    print("=" * 80)
    print("  LAKEHOUSE MULTI-WAREHOUSE TEST")
    print("=" * 80)
    print("\nThis test validates the isolated Warehouse architecture:")
    print("  1. product_dw  -> product-bucket (Product Domain)")
    print("  2. dwh_dw      -> platform-bucket (Analytics Platform)")

    try:
        check_services()

        warehouses_to_test = [
            ("product_dw", "product", "employees"),
            ("dwh_dw", "analytics", "employees"),
        ]

        results = {}
        for warehouse, namespace, table in warehouses_to_test:
            try:
                success = test_warehouse(warehouse, namespace, table)
                results[warehouse] = success
            except Exception as e:
                print(f"\n❌ Error testing warehouse '{warehouse}': {e}")
                import traceback
                traceback.print_exc()
                results[warehouse] = False

        print_section("  FINAL TEST RESULTS")
        all_passed = True
        for warehouse, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {warehouse:20} {status}")
            if not success:
                all_passed = False

        if all_passed:
            print_section("  ALL TESTS PASSED SUCCESSFULLY!")
            print("\n  Your Lakehouse multi-warehouse architecture is fully functional!")
            return 0
        else:
            print_section("❌ SOME TESTS FAILED")
            return 1

    except Exception as e:
        print_section("❌ CRITICAL ERROR!")
        print(f"\n{str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())