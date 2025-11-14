# tools/recommend.py
from langchain.tools import tool
from config import collection, embedding_fn
from sqlalchemy import text
import numpy as np

@tool
def recommend_movie_from_likes(liked_titles: str) -> str:
    """Gợi ý phim dựa trên các phim người dùng thích."""
    titles = [t.strip() for t in liked_titles.split(",") if t.strip()]
    if not titles:
        return "Vui lòng cung cấp ít nhất 1 tên phim bạn thích."

    liked_ids = []
    from config import SessionLocal
    db = SessionLocal()
    try:
        for title in titles:
            result = db.execute(
                text("SELECT id FROM movies WHERE title ILIKE :t"),
                {"t": f"%{title}%"}
            ).fetchone()
            if result:
                liked_ids.append(str(result[0]))
    finally:
        db.close()
    
    if not liked_ids:
        return "Không tìm thấy phim nào bạn thích trong hệ thống."

    # Lấy vector trung bình từ Chroma
    vectors = []
    for mid in liked_ids:
        res = collection.get(ids=[f"overview_{mid}"], include=["embeddings"])
        if res["embeddings"]:
            vectors.append(res["embeddings"][0])
    
    if not vectors:
        return "Không có dữ liệu mô tả (overview) cho phim bạn thích."

    centroid = np.mean(vectors, axis=0).tolist()
    
    # Tìm phim tương tự (loại trừ phim đã thích)
    results = collection.query(
        query_embeddings=[centroid],
        n_results=6,
        where={"movie_id": {"$nin": liked_ids}}
    )
    
    if not results["metadatas"]:
        return "Không tìm thấy gợi ý tương tự."

    recs = []
    db = SessionLocal()
    try:
        for meta in results["metadatas"][:3]:
            mid = meta["movie_id"]
            movie = db.execute(
                text("SELECT title, release_date FROM movies WHERE id = :mid"),
                {"mid": int(mid)}
            ).fetchone()
            if movie:
                title, date = movie
                year = date.strftime("%Y") if date else "N/A"
                recs.append(f"- **{title}** ({year})")
    finally:
        db.close()
    
    return "Gợi ý cho bạn:\n" + "\n".join(recs)