# load_data.py
from config import SessionLocal, collection_overview, collection_quotes, collection_metadata, embedding_fn
from sqlalchemy import text

def load_to_chroma():
    db = SessionLocal()
    try:
        print("Đang truy vấn dữ liệu từ PostgreSQL...")
        movies = db.execute(text("""
            SELECT id, title, overview, release_date
            FROM movies
            WHERE overview IS NOT NULL 
              AND TRIM(overview) != ''
              AND vote_count > 50
            ORDER BY vote_count DESC
            LIMIT 10000
        """)).fetchall()

        if not movies:
            print("Không có phim nào trong cơ sở dữ liệu!")
            return

        print("Đang xóa dữ liệu cũ trong ChromaDB...")
        for coll in [collection_overview, collection_quotes, collection_metadata]:
            try:
                existing = coll.get(include=[])
                if existing["ids"]:
                    coll.delete(ids=existing["ids"])
                else:
                    print(f"Collection {coll.name} đã rỗng.")
            except Exception as e:
                print(f"Không thể xóa {coll.name}: {e}")

        print("Đang thêm 1000 phim vào ChromaDB...")
        success_count = 0
        for m in movies:
            mid = str(m[0])
            title = m[1]
            overview = (m[2] or "").strip()
            date = m[3]
            year = date.strftime("%Y") if date else "N/A"

            try:
                # Overview
                collection_overview.add(
                    ids=[f"overview_{mid}"],
                    documents=[overview],
                    metadatas=[{"movie_id": mid, "title": title, "year": year}],
                    embeddings=[embedding_fn(overview)]
                )
                # Quote
                quote = f"Câu thoại nổi tiếng từ {title}..."
                collection_quotes.add(
                    ids=[f"quote_{mid}"],
                    documents=[quote],
                    metadatas=[{"movie_id": mid}],
                    embeddings=[embedding_fn(quote)]
                )
                # Metadata
                meta_text = f"{title} {year}"
                collection_metadata.add(
                    ids=[f"meta_{mid}"],
                    documents=[meta_text],
                    metadatas=[{"movie_id": mid, "title": title, "year": year}],
                    embeddings=[embedding_fn(meta_text)]
                )
                success_count += 1
            except Exception as e:
                print(f"Lỗi thêm phim {mid}: {e}")

        print(f"ĐÃ THÊM THÀNH CÔNG {success_count}/1000 PHIM!")
        
    except Exception as e:
        print(f"LỖI: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_to_chroma()