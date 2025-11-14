# tools/trending.py
from langchain.tools import tool
from config import engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)

@tool
def get_trending_movies(dummy: str = "") -> str:
    """Lấy top 5 phim đang hot theo số lượt đánh giá (vote_count)."""
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT title, release_date, vote_average, vote_count
                FROM movies
                WHERE vote_average > 8.0 AND vote_count > 1000
                ORDER BY vote_average DESC, vote_count DESC
                LIMIT 5
            """)
        ).fetchall()
        
        if not result:
            return "Không có dữ liệu phim hot."
        
        trending = []
        for title, date, vote_average, vote_count in result:
            year = date.strftime("%Y") if date else "N/A"
            trending.append(f"- **{title}** ({year}) – {vote_average} điểm đánh giá và {vote_count} lượt đánh giá")
        
        return "Top 5 phim đang hot (theo điểm đánh giá và lượt đánh giá):\n" + "\n".join(trending)
    finally:
        db.close()