import psycopg2
from faker import Faker
import random
from datetime import datetime

# --- Config ---
DB_NAME = "bigdata_project"
DB_USER = "truongphan"
DB_PASS = "abcd1234"
DB_HOST = "localhost"
DB_PORT = "5432"

# --- Kết nối DB ---
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
)
cur = conn.cursor()

fake = Faker()

# --- Danh sách mẫu ---
GENRES = [
    "Action", "Comedy", "Drama", "Fantasy", "Horror", "Mystery", "Romance", "Sci-Fi",
    "Thriller", "Adventure", "Animation", "Crime", "Documentary", "Family", "War"
]

DIRECTORS = [
    "Christopher Nolan", "Quentin Tarantino", "James Cameron", "Steven Spielberg",
    "Martin Scorsese", "Ridley Scott", "Denis Villeneuve", "David Fincher",
    "Peter Jackson", "Guillermo del Toro"
]

CAST_NAMES = [
    "Leonardo DiCaprio", "Brad Pitt", "Tom Hanks", "Natalie Portman", "Matt Damon",
    "Scarlett Johansson", "Morgan Freeman", "Robert Downey Jr.", "Anne Hathaway",
    "Jennifer Lawrence", "Christian Bale", "Emma Stone", "Ryan Gosling", "Denzel Washington"
]

# --- Tạo dữ liệu ---
records = []
for _ in range(120):  # 120 phim
    title = fake.catch_phrase() + " " + random.choice(["I", "II", "III", "Reboot", "Legacy", "Origins"])
    genres = random.sample(GENRES, k=random.randint(1, 3))
    cast = random.sample(CAST_NAMES, k=random.randint(2, 4))
    director = random.choice(DIRECTORS)
    release_date = fake.date_between(start_date="-30y", end_date="today")
    overview = fake.paragraph(nb_sentences=4)
    tagline = fake.sentence(nb_words=6)
    vote_average = round(random.uniform(5.0, 9.8), 1)
    vote_count = random.randint(100, 50000)
    records.append((title, genres, cast, director, release_date, overview, tagline, vote_average, vote_count))

# --- Insert vào DB ---
cur.executemany("""
    INSERT INTO movies_metadata
    (title, genres, "cast", director, release_date, overview, tagline, vote_average, vote_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", records)

conn.commit()
print(f"✅ Đã chèn {len(records)} phim vào PostgreSQL!")

cur.close()
conn.close()
