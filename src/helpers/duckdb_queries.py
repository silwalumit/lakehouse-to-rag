import duckdb
from deltalake import DeltaTable

# Paths to Delta tables
BRONZE_PATH = "data/delta/bronze"
SILVER_PATH = "data/delta/silver"
GOLD_PATH = "data/delta/gold"


def setup_duckdb_connection():
    """Create DuckDB connection and register Delta tables."""
    con = duckdb.connect()

    # Register Delta tables as views
    bronze_df = DeltaTable(BRONZE_PATH).to_pandas()
    silver_df = DeltaTable(SILVER_PATH).to_pandas()
    gold_df = DeltaTable(GOLD_PATH).to_pandas()

    con.register("bronze", bronze_df)
    con.register("silver", silver_df)
    con.register("gold", gold_df)

    return con


def run_data_quality_queries():
    """Run data quality analysis queries."""
    con = setup_duckdb_connection()

    print("=== Data Quality Analysis ===\n")

    # 1. Record counts
    print("1. Record counts:")
    result = con.execute("""
        SELECT 
            'bronze' as table_name, COUNT(*) as record_count FROM bronze
        UNION ALL
        SELECT 'silver', COUNT(*) FROM silver
        UNION ALL
        SELECT 'gold', COUNT(*) FROM gold
    """).fetchall()

    for table_name, count in result:
        print(f"  {table_name}: {count} records")

    # 2. Content length statistics
    print("\n2. Content length statistics:")
    result = con.execute("""
        SELECT 
            'bronze' as table_name,
            AVG(LENGTH(content)) as avg_length,
            MIN(LENGTH(content)) as min_length,
            MAX(LENGTH(content)) as max_length
        FROM bronze
        UNION ALL
        SELECT 'silver', AVG(LENGTH(content)), MIN(LENGTH(content)), MAX(LENGTH(content))
        FROM silver
        UNION ALL
        SELECT 'gold', AVG(LENGTH(content)), MIN(LENGTH(content)), MAX(LENGTH(content))
        FROM gold
    """).fetchall()

    for table_name, avg_len, min_len, max_len in result:
        print(f"  {table_name}: avg={avg_len:.1f}, min={min_len}, max={max_len}")

    # 3. Missing values
    print("\n3. Missing values:")
    result = con.execute("""
        SELECT 
            'bronze' as table_name,
            COUNT(*) - COUNT(content) as missing_content,
            COUNT(*) - COUNT(title) as missing_title
        FROM bronze
        UNION ALL
        SELECT 'silver', COUNT(*) - COUNT(content), COUNT(*) - COUNT(title)
        FROM silver
        UNION ALL
        SELECT 'gold', COUNT(*) - COUNT(content), COUNT(*) - COUNT(title)
        FROM gold
    """).fetchall()

    for table_name, missing_content, missing_title in result:
        print(
            f"  {table_name}: {missing_content} missing content, {missing_title} missing title"
        )

    con.close()


def run_content_analysis():
    """Run content analysis queries."""
    con = setup_duckdb_connection()

    print("=== Content Analysis ===\n")

    # 1. Most common words in content
    print("1. Most common words in gold table:")
    result = con.execute("""
        SELECT 
            word,
            COUNT(*) as frequency
        FROM (
            SELECT UNNEST(STRING_SPLIT(LOWER(content), ' ')) as word
            FROM gold
            WHERE LENGTH(word) > 3
        )
        GROUP BY word
        ORDER BY frequency DESC
        LIMIT 10
    """).fetchall()

    for word, freq in result:
        print(f"  '{word}': {freq} times")

    # 2. Duplicate analysis
    print("\n2. Duplicate analysis:")
    result = con.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT content) as unique_content,
            COUNT(*) - COUNT(DISTINCT content) as duplicates
        FROM bronze
    """).fetchall()

    total, unique, duplicates = result[0]
    print(f"  Bronze: {total} total, {unique} unique, {duplicates} duplicates")

    con.close()


def run_custom_query(sql_query):
    """Run a custom SQL query on the Delta tables."""
    con = setup_duckdb_connection()
    result = con.execute(sql_query).fetchall()
    con.close()
    return result


if __name__ == "__main__":
    run_data_quality_queries()
    print("\n" + "=" * 50 + "\n")
    run_content_analysis()

    # Example custom query
    print("\n=== Custom Query Example ===")
    print("Top 5 sources by content length:")
    con = setup_duckdb_connection()
    result = con.execute("""
        SELECT source, AVG(LENGTH(content)) as avg_length
        FROM gold
        GROUP BY source
        ORDER BY avg_length DESC
        LIMIT 5
    """).fetchall()

    for source, avg_length in result:
        print(f"  {source}: {avg_length:.1f} chars avg")

    con.close()
