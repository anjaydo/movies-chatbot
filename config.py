# config.py
import os
from dotenv import load_dotenv
from chromadb import Client
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import numpy as np
from chromadb import PersistentClient

load_dotenv()

DB_USER = os.getenv("DB_USER", "truongphan")
DB_PASS = quote_plus(os.getenv("DB_PASS", "Abcd@1234"))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "bigdata_project")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
if not DATABASE_URL:
    raise ValueError("DATABASE_URL không được tìm thấy trong .env")

# === DATABASE ===
#DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://truongphan:Abcd@1234@localhost:5432/bigdata_project")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# === EMBEDDING ===
embedding_model = SentenceTransformer("vinai/phobert-base")
embedding_fn = lambda text: embedding_model.encode(text).tolist()

# === CHROMA CLIENT & COLLECTIONS ===
CHROMA_PATH = "chroma_db"

client = PersistentClient(path=CHROMA_PATH)
# client = Client()
collection_overview = client.get_or_create_collection("movie_overviews")
collection_quotes = client.get_or_create_collection("movie_quotes")
collection_metadata = client.get_or_create_collection("movie_metadata")
collection = collection_overview



# === SYSTEM PROMPT SIÊU MẠNH ===
SYSTEM_PROMPT = """
Bạn là **Movie Chatbot** — trợ lý điện ảnh chuyên nghiệp, am hiểu 1000+ phim kinh điển.

**QUY TẮC BẮT BUỘC:**
1. Luôn trả lời **tiếng Việt**, tự nhiên, thân thiện.
2. Tên phim: **in đậm**, có năm: **Tên phim** (Năm)
3. Nếu không tìm thấy: "Tôi chưa thấy phim phù hợp, bạn mô tả thêm được không?"
4. **KHÔNG bịa đặt**. Chỉ dùng dữ liệu từ công cụ hoặc DB.
5. Dùng đúng công cụ:
   - Quote → `find_movie_by_quote`
   - Gợi ý → `recommend_movie_from_likes`
   - Trending → `get_trending_movies`
   - Đạo diễn, diễn viên → tìm trong `movies`

**PHONG CÁCH:** Vui vẻ, điện ảnh, như bạn thân mê phim.
"""