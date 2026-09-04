import os

from psycopg import sql

from tests.database_support import DATABASE_TEST_MARK, connect_as

pytestmark = DATABASE_TEST_MARK

EXPECTED_TABLES = (
    "customers",
    "employees",
    "inventory",
    "product_categories",
    "product_returns",
    "products",
    "purchase_order_items",
    "purchase_orders",
    "sales_order_items",
    "sales_orders",
    "suppliers",
    "warehouses",
)

EXPECTED_COLUMN_COUNTS = {
    "customers": 12,
    "employees": 12,
    "inventory": 6,
    "product_categories": 6,
    "product_returns": 10,
    "products": 11,
    "purchase_order_items": 8,
    "purchase_orders": 12,
    "sales_order_items": 9,
    "sales_orders": 12,
    "suppliers": 12,
    "warehouses": 9,
}

EXPECTED_PRIMARY_KEYS = {
    "customers": ("customer_id",),
    "employees": ("employee_id",),
    "inventory": ("product_id", "warehouse_id"),
    "product_categories": ("category_id",),
    "product_returns": ("return_id",),
    "products": ("product_id",),
    "purchase_order_items": ("purchase_order_item_id",),
    "purchase_orders": ("purchase_order_id",),
    "sales_order_items": ("sales_order_item_id",),
    "sales_orders": ("sales_order_id",),
    "suppliers": ("supplier_id",),
    "warehouses": ("warehouse_id",),
}

EXPECTED_FOREIGN_KEYS = {
    ("fk_employees_manager", "employees", "employees"),
    ("fk_employees_warehouse", "employees", "warehouses"),
    ("fk_inventory_product", "inventory", "products"),
    ("fk_inventory_warehouse", "inventory", "warehouses"),
    ("fk_product_categories_parent", "product_categories", "product_categories"),
    ("fk_product_returns_employee", "product_returns", "employees"),
    ("fk_product_returns_order_item", "product_returns", "sales_order_items"),
    ("fk_products_category", "products", "product_categories"),
    ("fk_products_supplier", "products", "suppliers"),
    ("fk_purchase_order_items_order", "purchase_order_items", "purchase_orders"),
    ("fk_purchase_order_items_product", "purchase_order_items", "products"),
    ("fk_purchase_orders_buyer", "purchase_orders", "employees"),
    ("fk_purchase_orders_supplier", "purchase_orders", "suppliers"),
    ("fk_purchase_orders_warehouse", "purchase_orders", "warehouses"),
    ("fk_sales_order_items_order", "sales_order_items", "sales_orders"),
    ("fk_sales_order_items_product", "sales_order_items", "products"),
    ("fk_sales_order_items_warehouse", "sales_order_items", "warehouses"),
    ("fk_sales_orders_customer", "sales_orders", "customers"),
    ("fk_sales_orders_sales_rep", "sales_orders", "employees"),
}

EXPECTED_INDEXES = {
    "idx_employees_manager",
    "idx_employees_warehouse",
    "idx_inventory_warehouse",
    "idx_product_categories_parent",
    "idx_product_returns_date_status",
    "idx_product_returns_employee",
    "idx_product_returns_order_item",
    "idx_products_category",
    "idx_products_supplier",
    "idx_purchase_order_items_product",
    "idx_purchase_orders_buyer_date",
    "idx_purchase_orders_status_expected_date",
    "idx_purchase_orders_supplier_date",
    "idx_purchase_orders_warehouse_date",
    "idx_sales_order_items_product",
    "idx_sales_order_items_warehouse",
    "idx_sales_orders_customer_date",
    "idx_sales_orders_sales_rep_date",
    "idx_sales_orders_status_date",
}


def _bootstrap_username() -> str:
    return os.getenv("POSTGRES_USER", "queryguard_bootstrap")


def test_expected_tables_are_owned_and_documented() -> None:
    with connect_as(_bootstrap_username(), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT table_class.relname,
                   pg_catalog.pg_get_userbyid(table_class.relowner),
                   pg_catalog.obj_description(table_class.oid, 'pg_class')
            FROM pg_catalog.pg_class AS table_class
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = table_class.relnamespace
            WHERE namespace.nspname = 'erp'
              AND table_class.relkind = 'r'
            ORDER BY table_class.relname
            """
        ).fetchall()

    assert tuple(row[0] for row in rows) == EXPECTED_TABLES
    assert all(row[1] == "queryguard_owner" for row in rows)
    assert all(row[2] for row in rows)


def test_table_column_counts_match_the_design() -> None:
    with connect_as(_bootstrap_username(), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT table_name, count(*)
            FROM information_schema.columns
            WHERE table_schema = 'erp'
            GROUP BY table_name
            ORDER BY table_name
            """
        ).fetchall()

    assert dict(rows) == EXPECTED_COLUMN_COUNTS


def test_primary_keys_match_the_design() -> None:
    with connect_as(_bootstrap_username(), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT table_class.relname,
                   array_agg(attribute.attname ORDER BY key_column.ordinality)
            FROM pg_catalog.pg_constraint AS constraint_definition
            JOIN pg_catalog.pg_class AS table_class
              ON table_class.oid = constraint_definition.conrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = table_class.relnamespace
            CROSS JOIN LATERAL unnest(constraint_definition.conkey)
                WITH ORDINALITY AS key_column(attnum, ordinality)
            JOIN pg_catalog.pg_attribute AS attribute
              ON attribute.attrelid = table_class.oid
             AND attribute.attnum = key_column.attnum
            WHERE namespace.nspname = 'erp'
              AND constraint_definition.contype = 'p'
            GROUP BY table_class.relname
            ORDER BY table_class.relname
            """
        ).fetchall()

    primary_keys = {table_name: tuple(columns) for table_name, columns in rows}
    assert primary_keys == EXPECTED_PRIMARY_KEYS


def test_foreign_keys_match_the_design() -> None:
    with connect_as(_bootstrap_username(), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT constraint_definition.conname,
                   source_table.relname,
                   target_table.relname
            FROM pg_catalog.pg_constraint AS constraint_definition
            JOIN pg_catalog.pg_class AS source_table
              ON source_table.oid = constraint_definition.conrelid
            JOIN pg_catalog.pg_class AS target_table
              ON target_table.oid = constraint_definition.confrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = source_table.relnamespace
            WHERE namespace.nspname = 'erp'
              AND constraint_definition.contype = 'f'
            """
        ).fetchall()

    assert set(rows) == EXPECTED_FOREIGN_KEYS


def test_check_constraints_are_named_and_validated() -> None:
    required_checks = {
        "ck_customers_segment",
        "ck_inventory_reserved_not_above_stock",
        "ck_product_returns_status",
        "ck_products_dates",
        "ck_purchase_order_items_received_quantity",
        "ck_sales_order_items_discount",
        "ck_sales_orders_status",
    }
    with connect_as(_bootstrap_username(), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT constraint_definition.conname, constraint_definition.convalidated
            FROM pg_catalog.pg_constraint AS constraint_definition
            JOIN pg_catalog.pg_class AS table_class
              ON table_class.oid = constraint_definition.conrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = table_class.relnamespace
            WHERE namespace.nspname = 'erp'
              AND constraint_definition.contype = 'c'
            """
        ).fetchall()

    check_names = {name for name, _is_validated in rows}
    assert len(rows) == 59
    assert all(name.startswith("ck_") and is_validated for name, is_validated in rows)
    assert required_checks <= check_names


def test_expected_reporting_and_foreign_key_indexes_exist() -> None:
    with connect_as(_bootstrap_username(), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT indexname
            FROM pg_catalog.pg_indexes
            WHERE schemaname = 'erp'
              AND indexname LIKE 'idx_%'
            """
        ).fetchall()

    assert {row[0] for row in rows} == EXPECTED_INDEXES


def test_runtime_has_select_only_and_audit_has_no_erp_table_access() -> None:
    with connect_as(_bootstrap_username(), "POSTGRES_PASSWORD") as conn:
        rows = conn.execute(
            """
            SELECT table_class.relname,
                   has_table_privilege('queryguard_runtime', table_class.oid, 'SELECT'),
                   has_table_privilege('queryguard_runtime', table_class.oid, 'INSERT'),
                   has_table_privilege('queryguard_runtime', table_class.oid, 'UPDATE'),
                   has_table_privilege('queryguard_runtime', table_class.oid, 'DELETE'),
                   has_table_privilege('queryguard_runtime', table_class.oid, 'TRUNCATE'),
                   has_table_privilege('queryguard_audit', table_class.oid, 'SELECT')
            FROM pg_catalog.pg_class AS table_class
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = table_class.relnamespace
            WHERE namespace.nspname = 'erp'
              AND table_class.relkind = 'r'
            ORDER BY table_class.relname
            """
        ).fetchall()

    assert tuple(row[0] for row in rows) == EXPECTED_TABLES
    assert all(row[1:] == (True, False, False, False, False, False) for row in rows)


def test_runtime_can_read_every_empty_erp_table() -> None:
    with connect_as("queryguard_runtime", "QUERYGUARD_RUNTIME_PASSWORD") as conn:
        counts = {
            table_name: conn.execute(
                sql.SQL("SELECT count(*) FROM erp.{}").format(sql.Identifier(table_name))
            ).fetchone()
            for table_name in EXPECTED_TABLES
        }

    assert all(result == (0,) for result in counts.values())
