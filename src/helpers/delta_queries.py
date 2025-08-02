from deltalake import DeltaTable

# Paths to Delta tables
BRONZE_PATH = "data/delta/bronze"
SILVER_PATH = "data/delta/silver"
GOLD_PATH = "data/delta/gold"


def get_delta_table_as_df(table_path):
    """Read a Delta table and return as pandas DataFrame."""
    dt = DeltaTable(table_path)
    return dt.to_pandas()


def query_bronze_table():
    """Query the bronze table - raw scraped data."""
    df = get_delta_table_as_df(BRONZE_PATH)
    print(f"Bronze table has {len(df)} records")
    print("Columns:", df.columns.tolist())
    print("\nSample data:")
    print(df.head())
    return df


def query_silver_table():
    """Query the silver table - cleaned data."""
    df = get_delta_table_as_df(SILVER_PATH)
    print(f"Silver table has {len(df)} records")
    print("Columns:", df.columns.tolist())
    print("\nSample data:")
    print(df.head())
    return df


def query_gold_table():
    """Query the gold table - deduplicated data."""
    df = get_delta_table_as_df(GOLD_PATH)
    print(f"Gold table has {len(df)} records")
    print("Columns:", df.columns.tolist())
    print("\nSample data:")
    print(df.head())
    return df


def analyze_content_lengths():
    """Analyze content lengths across all tables."""
    bronze_df = get_delta_table_as_df(BRONZE_PATH)
    silver_df = get_delta_table_as_df(SILVER_PATH)
    gold_df = get_delta_table_as_df(GOLD_PATH)

    print("Content length analysis:")
    print(f"Bronze: {bronze_df['content'].str.len().mean():.1f} chars avg")
    print(f"Silver: {silver_df['content'].str.len().mean():.1f} chars avg")
    print(f"Gold: {gold_df['content'].str.len().mean():.1f} chars avg")


def find_duplicates():
    """Find potential duplicates in bronze table."""
    df = get_delta_table_as_df(BRONZE_PATH)
    duplicates = df[df.duplicated(subset=["content"], keep=False)]
    print(f"Found {len(duplicates)} duplicate records in bronze table")
    return duplicates


if __name__ == "__main__":
    print("=== Delta Table Queries ===\n")

    print("1. Bronze Table (Raw Data):")
    query_bronze_table()

    print("\n2. Silver Table (Cleaned):")
    query_silver_table()

    print("\n3. Gold Table (Deduplicated):")
    query_gold_table()

    print("\n4. Content Analysis:")
    analyze_content_lengths()

    print("\n5. Duplicate Analysis:")
    find_duplicates()
