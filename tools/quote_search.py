# tools/quote_search.py
from langchain.tools import tool
from config import collection_quotes, embedding_fn, SessionLocal
from sqlalchemy import text

@tool
def find_movie_by_quote(quote: str) -> str:
    """Tìm phim theo câu thoại bằng semantic search trong ChromaDB."""
    try:
        results = collection_quotes.query(
            query_texts=[quote],
            n_results=3,  # Lấy 3 → chọn phim tốt nhất
            include=["metadatas", "distances"]
        )
        
        if not results["ids"][0]:
            return "Không tìm thấy phim nào với câu thoại này."
        
        # Chọn kết quả gần nhất
        best = min(zip(results["metadatas"][0], results["distances"][0]), key=lambda x: x[1])
        movie_id = best[0]["movie_id"]
        
        db = SessionLocal()
        movie = db.execute(
            text("SELECT title, release_date FROM movies WHERE id = :mid"),
            {"mid": int(movie_id)}
        ).fetchone()
        db.close()
        
        if movie:
            title, date = movie
            year = date.strftime("%Y") if date else "N/A"
            return f"**{title}** ({year})"
        else:
            return "Tìm thấy quote nhưng không có thông tin phim."
    except Exception as e:
        return f"Lỗi tìm kiếm: {str(e)}"