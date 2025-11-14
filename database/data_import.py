#!/usr/bin/env python3

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === Configuration ===
# --- Update with your PostgreSQL connection details ---
# For security, it's best to set these as environment variables
# The script will try to read them from the environment first.
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_USER = os.environ.get("DB_USER")
DB_NAME = os.environ.get("DB_NAME")
DB_PASSWORD = os.environ.get("DB_PASS")

# --- File and Table settings ---
CSV_FILE = "TMDB_all_movies.csv" # The path to your CSV file
STAGING_TABLE = "movies_staging"
FINAL_TABLE = "movies"

# Check if password is set
if DB_PASSWORD is None:
    print("Error: PGPASSWORD environment variable is not set.", file=sys.stderr)
    print("Please set it before running the script:", file=sys.stderr)
    print("  export PGPASSWORD=\"your_password\"", file=sys.stderr)
    sys.exit(1)

# Check if CSV file exists
if not os.path.isfile(CSV_FILE):
    print(f"Error: CSV file not found at {CSV_FILE}", file=sys.stderr)
    sys.exit(1)

# === SQL Definitions ===

# Step 1: Create Staging Table (all columns as TEXT)
CREATE_STAGING_SQL = sql.SQL("""
DROP TABLE IF EXISTS {staging_table};
CREATE TABLE {staging_table} (
    "id" TEXT,
    "title" TEXT,
    "vote_average" TEXT,
    "vote_count" TEXT,
    "status" TEXT,
    "release_date" TEXT,
    "revenue" TEXT,
    "runtime" TEXT,
    "budget" TEXT,
    "imdb_id" TEXT,
    "original_language" TEXT,
    "original_title" TEXT,
    "overview" TEXT,
    "popularity" TEXT,
    "tagline" TEXT,
    "genres" TEXT,
    "production_companies" TEXT,
    "production_countries" TEXT,
    "spoken_languages" TEXT,
    "cast" TEXT,
    "director" TEXT,
    "director_of_photography" TEXT,
    "writers" TEXT,
    "producers" TEXT,
    "music_composer" TEXT,
    "imdb_rating" TEXT,
    "imdb_votes" TEXT,
    "poster_path" TEXT
);
""").format(staging_table=sql.Identifier(STAGING_TABLE))

# Step 3: Create Final, Properly-Typed Table
CREATE_FINAL_TABLE_SQL = sql.SQL("""
DROP TABLE IF EXISTS {final_table};
CREATE TABLE {final_table} (
    "id" BIGINT PRIMARY KEY,
    "title" TEXT,
    "vote_average" FLOAT,
    "vote_count" FLOAT,
    "status" VARCHAR(100),
    "release_date" DATE,
    "revenue" NUMERIC(18, 2),
    "runtime" FLOAT,
    "budget" NUMERIC(18, 2),
    "imdb_id" VARCHAR(20),
    "original_language" VARCHAR(10),
    "original_title" TEXT,
    "overview" TEXT,
    "popularity" FLOAT,
    "tagline" TEXT,
    "genres" TEXT,
    "production_companies" TEXT,
    "production_countries" TEXT,
    "spoken_languages" TEXT,
    "cast" TEXT,
    "director" TEXT,
    "director_of_photography" TEXT,
    "writers" TEXT,
    "producers" TEXT,
    "music_composer" TEXT,
    "imdb_rating" FLOAT,
    "imdb_votes" BIGINT,
    "poster_path" TEXT
);
""").format(final_table=sql.Identifier(FINAL_TABLE))

# Step 4: Insert and Cast data from Staging to Final Table
INSERT_FINAL_SQL = sql.SQL("""
INSERT INTO {final_table} (
    "id", "title", "vote_average", "vote_count", "status", "release_date", "revenue", "runtime", "budget",
    "imdb_id", "original_language", "original_title", "overview", "popularity", "tagline", "genres",
    "production_companies", "production_countries", "spoken_languages", "cast", "director",
    "director_of_photography", "writers", "producers", "music_composer", "imdb_rating", "imdb_votes", "poster_path"
)
SELECT
    NULLIF("id", '')::BIGINT,
    "title",
    NULLIF("vote_average", '')::FLOAT,
    NULLIF("vote_count", '')::FLOAT,
    "status",
    NULLIF("release_date", '')::DATE,
    NULLIF("revenue", '')::NUMERIC(18, 2),
    NULLIF("runtime", '')::FLOAT,
    NULLIF("budget", '')::NUMERIC(18, 2),
    "imdb_id",
    "original_language",
    "original_title",
    "overview",
    NULLIF("popularity", '')::FLOAT,
    "tagline",
    "genres",
    "production_companies",
    "production_countries",
    "spoken_languages",
    "cast",
    "director",
    "director_of_photography",
    "writers",
    "producers",
    "music_composer",
    NULLIF("imdb_rating", '')::FLOAT,
    NULLIF("imdb_votes", '')::FLOAT,
    "poster_path"
FROM {staging_table};
""").format(final_table=sql.Identifier(FINAL_TABLE), staging_table=sql.Identifier(STAGING_TABLE))

# Step 5: Clean up
CLEANUP_SQL = sql.SQL("DROP TABLE {staging_table};").format(staging_table=sql.Identifier(STAGING_TABLE))

def main():
    """
    Main function to run the import process.
    """
    conn = None
    cur = None
    try:
        # === Connect to PostgreSQL ===
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        conn.autocommit = True  # We'll run each step as its own transaction
        cur = conn.cursor()

        # === Step 1: Create Staging Table ===
        print(f"1. Creating staging table '{STAGING_TABLE}'...")
        cur.execute(CREATE_STAGING_SQL)

        # === Step 2: Copy CSV data to Staging Table ===
        print(f"2. Copying data from '{CSV_FILE}' to staging table...")
        # We use copy_expert to run a server-side COPY FROM STDIN
        # This is the most efficient way to bulk-load data with psycopg2
        copy_sql = sql.SQL("COPY {staging_table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE, QUOTE '\"', ESCAPE '\"')").format(staging_table=sql.Identifier(STAGING_TABLE))
        
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            cur.copy_expert(sql=copy_sql, file=f)

        # === Step 3: Create Final, Properly-Typed Table ===
        print(f"3. Creating final table '{FINAL_TABLE}' with correct data types...")
        cur.execute(CREATE_FINAL_TABLE_SQL)

        # === Step 4: Insert and Cast data ===
        print("4. Casting and inserting data into final table...")
        cur.execute(INSERT_FINAL_SQL)

        # === Step 5: Clean up ===
        print("5. Cleaning up staging table...")
        cur.execute(CLEANUP_SQL)

        print(f"\n✅ Import complete! Data is now in the '{FINAL_TABLE}' table.")

    except (Exception, psycopg2.Error) as error:
        print(f"\n❌ An error occurred: {error}", file=sys.stderr)
        # Note: With autocommit=True, we can't roll back,
        # but the script will have stopped at the point of failure.

    finally:
        # Close connection and cursor
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting movie import process...")
    main()