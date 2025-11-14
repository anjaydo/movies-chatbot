#!/usr/bin/env python3

import os
import sys
import psycopg2
import requests
import time
from psycopg2 import extras, sql
from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === Configuration ===
# --- Update with your PostgreSQL connection details ---
# For security, it's best to set these as environment variables
# The script will try to read them from the environment first.
DB_HOST = os.environ.get("PG_HOST")
DB_PORT = os.environ.get("PG_PORT")
DB_USER = os.environ.get("PG_USER")
DB_NAME = os.environ.get("PG_DB")
DB_PASSWORD = os.environ.get("PG_PASSWORD")


# --- TMDB API Configuration ---
# !!! IMPORTANT: You MUST set your TMDB API Key here !!!
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "YOUR_API_KEY_HERE")
if TMDB_API_KEY == "YOUR_API_KEY_HERE":
    print("Error: TMDB_API_KEY is not set.", file=sys.stderr)
    print("Please edit the script or set the TMDB_API_KEY environment variable.", file=sys.stderr)
    sys.exit(1)

# --- Table settings ---
FINAL_TABLE = "movies"

# --- Crawl settings ---
CONSECUTIVE_ERRORS_TO_STOP = 5
INSERT_BATCH_SIZE = 100
API_REQUEST_DELAY_SECONDS = 0.1 # Delay between each API request

# --- Helper Functions for API Parsing ---

def format_list(items, key_name, max_items=20):
    """Formats a list of dicts (like 'genres' or 'cast') into a comma-separated string."""
    if not items:
        return None
    return ", ".join([item[key_name] for item in items[:max_items]])

def find_crew(crew_list, job_title):
    """Finds the first crew member with a specific job."""
    for member in crew_list:
        if member.get('job') == job_title:
            return member.get('name')
    return None

def find_multiple_crew(crew_list, job_title, max_items=5):
    """Finds multiple crew members with a specific job (like 'Writer')."""
    members = [m.get('name') for m in crew_list if m.get('job') == job_title]
    if not members:
        return None
    return ", ".join(members[:max_items])

def get_latest_movie_id(cur):
    """Fetches the highest TMDB movie ID from the database."""
    try:
        # Ensure 'id' is treated as a number for correct MAX calculation
        query = sql.SQL("SELECT MAX(id) FROM {}").format(sql.Identifier(FINAL_TABLE))
        cur.execute(query)
        result = cur.fetchone()[0]
        # Handle case where table is empty (result is None)
        return int(result) if result is not None else 0
    except (Exception, psycopg2.Error) as e:
        print(f"Error fetching max movie ID: {e}", file=sys.stderr)
        return 0

def get_movie_details(movie_id):
    """
    Fetches full details for a single movie ID.
    Returns a tuple: (status_code, data)
    'status_code' can be 'ok', 'not_found', or 'error'
    'data' is the JSON response on 'ok', or error message otherwise
    """
    api_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {
        # 'api_key': TMDB_API_KEY,
        'append_to_response': 'credits'
    }
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }
    try:
        response = requests.get(api_url, params=params, headers=headers)
        
        if response.status_code == 200:
            return "ok", response.json()
            
        if response.status_code == 404:
            return "not_found", None
            
        # Other client/server errors
        response.raise_for_status() 
        
    except requests.RequestException as e:
        # This catches 4xx/5xx errors (after raise_for_status) and connection errors
        return "error", str(e)
    
    return "error", "Unknown error"

def parse_movie_details(movie_data):
    """
    Parses the detailed JSON response from TMDB and formats it
    into a tuple that matches the FINAL_TABLE schema.
    Returns None if essential data (like 'id') is missing.
    """
    if not movie_data or 'id' not in movie_data:
        return None
    
    try:
        # Get credits data
        credits = movie_data.get('credits', {})
        cast_list = credits.get('cast', [])
        crew_list = credits.get('crew', [])
        
        # Note: TMDB API does not provide IMDB votes or ratings.
        # These will be inserted as NULL.
        
        return (
            movie_data.get('id'),
            movie_data.get('title'),
            movie_data.get('vote_average'),
            movie_data.get('vote_count'),
            movie_data.get('status'),
            movie_data.get('release_date') or None, # Ensure empty string becomes None
            movie_data.get('revenue'),
            movie_data.get('runtime'),
            movie_data.get('budget'),
            movie_data.get('imdb_id'),
            movie_data.get('original_language'),
            movie_data.get('original_title'),
            movie_data.get('overview'),
            movie_data.get('popularity'),
            movie_data.get('tagline') or None,
            format_list(movie_data.get('genres', []), 'name'),
            format_list(movie_data.get('production_companies', []), 'name'),
            format_list(movie_data.get('production_countries', []), 'name'),
            format_list(movie_data.get('spoken_languages', []), 'english_name'),
            format_list(cast_list, 'name', max_items=30),
            find_crew(crew_list, 'Director'),
            find_crew(crew_list, 'Director of Photography'),
            find_multiple_crew(crew_list, 'Writer'),
            find_multiple_crew(crew_list, 'Producer'),
            find_crew(crew_list, 'Original Music Composer'),
            None, # imdb_rating (not available from TMDB)
            None, # imdb_votes (not available from TMDB)
            movie_data.get('poster_path')
        )
    except Exception as e:
        print(f"Error parsing data for movie ID {movie_data.get('id')}: {e}", file=sys.stderr)
        return None

def insert_movies_into_db(conn, cur, movies_to_insert):
    """Inserts a list of movie tuples into the final table."""
    
    if not movies_to_insert:
        return 0
        
    # This query must match the column order from parse_movie_details
    insert_query = sql.SQL("""
    INSERT INTO {} (
        "id", "title", "vote_average", "vote_count", "status", "release_date", "revenue", "runtime", "budget",
        "imdb_id", "original_language", "original_title", "overview", "popularity", "tagline", "genres",
        "production_companies", "production_countries", "spoken_languages", "cast", "director",
        "director_of_photography", "writers", "producers", "music_composer", "imdb_rating", "imdb_votes", "poster_path"
    )
    VALUES %s
    ON CONFLICT ("id") DO NOTHING;
    """).format(sql.Identifier(FINAL_TABLE))
    
    try:
        psycopg2.extras.execute_values(
            cur,
            insert_query,
            movies_to_insert,
            template=None,
            page_size=INSERT_BATCH_SIZE
        )
        conn.commit()
        print(f"  ... Successfully inserted/updated {len(movies_to_insert)} movies.")
        return len(movies_to_insert)
    except (Exception, psycopg2.Error) as e:
        print(f"Error during batch insert: {e}", file=sys.stderr)
        conn.rollback()
        return 0

def main():
    """Main execution function."""
    
    if DB_PASSWORD is None:
        print("Error: PGPASSWORD environment variable is not set.", file=sys.stderr)
        sys.exit(1)

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
        cur = conn.cursor()

        # === Step 1: Get Max Movie ID from DB ===
        print("1. Getting latest movie ID from database...")
        latest_id_in_db = get_latest_movie_id(cur)
        
        if latest_id_in_db == 0:
            print("   No movies found in database. Starting from ID 1.")
            current_id = 1
        else:
            print(f"   Latest movie in DB has ID: {latest_id_in_db}")
            current_id = latest_id_in_db + 1
        
        # === Step 2: Start Incremental Crawl ===
        print(f"2. Starting crawl from movie ID {current_id}...")
        
        consecutive_errors = 0
        total_movies_found = 0
        movies_to_insert = []

        while consecutive_errors < CONSECUTIVE_ERRORS_TO_STOP:
            print(f"  Fetching ID: {current_id}")
            status, data = get_movie_details(current_id)
            
            if status == "ok":
                # Movie found, reset error count
                consecutive_errors = 0
                
                # Parse the data
                parsed_data = parse_movie_details(data)
                if parsed_data:
                    movies_to_insert.append(parsed_data)
                    total_movies_found += 1
                
                # Insert in batches
                if len(movies_to_insert) >= INSERT_BATCH_SIZE:
                    print(f"  Reached batch size, inserting {len(movies_to_insert)} movies...")
                    insert_movies_into_db(conn, cur, movies_to_insert)
                    movies_to_insert = [] # Clear the batch

            elif status == "not_found":
                # Expected gap, increment error count
                print(f"  No movie found for ID {current_id}. (Error {consecutive_errors + 1} of {CONSECUTIVE_ERRORS_TO_STOP})")
                consecutive_errors += 1

            elif status == "error":
                # Unexpected error, stop the script
                print(f"\n❌ An unexpected API error occurred: {data}", file=sys.stderr)
                print("Stopping script to avoid further issues.")
                break # Exit the while loop
            
            # Move to the next ID
            current_id += 1
            
            # Be polite to the API
            time.sleep(API_REQUEST_DELAY_SECONDS)

        # === Step 3: Final Insert ===
        print("\n3. Crawl finished. Inserting remaining movies...")
        if movies_to_insert:
            insert_movies_into_db(conn, cur, movies_to_insert)
        
        if consecutive_errors >= CONSECUTIVE_ERRORS_TO_STOP:
            print(f"Stopped after {CONSECUTIVE_ERRORS_TO_STOP} consecutive 'Not Found' errors.")
        
        print(f"\n✅ New movie fetch complete! Found {total_movies_found} new movies.")

    except (Exception, psycopg2.Error) as error:
        print(f"\n❌ An error occurred: {error}", file=sys.stderr)

    finally:
        # Close connection and cursor
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()