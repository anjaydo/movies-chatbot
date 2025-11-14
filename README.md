# Movie AI Chatbot (RAG + PostgreSQL + Metabase Dashboard)

Hệ thống chatbot AI thông minh về phim ảnh sử dụng RAG (Retrieval-Augmented Generation), tích hợp với dashboard Metabase để hiển thị các biểu đồ và thống kê trực quan. Ứng dụng có thể được nhúng vào Metabase thông qua iframe.

<img src="https://raw.githubusercontent.com/anjaydo/movies-chatbot/refs/heads/main/images/Dashboard.png" alt="Chatbot Dashboard">

## 🎯 Chức năng

- **Tìm phim bằng đoạn thoại (quote)**: Tìm kiếm phim dựa trên câu thoại nổi tiếng bằng semantic search
- **Gợi ý phim**: Đề xuất phim tương tự dựa trên sở thích người dùng (content-based + semantic)
- **Phim trending**: Lấy danh sách phim đang hot theo IMDB Weighted Rating (WR)
- **Chat tự nhiên**: Trả lời câu hỏi về phim bằng tiếng Việt với Gemini AI
- **Dashboard Metabase**: Tích hợp dashboard với các biểu đồ visualization về thống kê phim

## 🏗️ Kiến trúc hệ thống

Dự án sử dụng kiến trúc Big Data với các thành phần chính:

- **Data Sources**: TMDB API, [OpenSubtitles](https://drive.google.com/drive/folders/12HdMMLtxM9I7GUakRFgAS8IrULzQmGKD?usp=sharing) API, CSV files
- **Data Lakehouse**: S3/MinIO (Bronze/Silver/Gold layers)
- **Batch Processing**: Apache Spark (ETL, embeddings, WR computation)
- **Online Stores**: PostgreSQL (metadata), ChromaDB (vector embeddings)
- **Serving Layer**: FastAPI (Recommendation Engine, RAG Chatbot)
- **Consumption**: Web App/Chat UI, Metabase Dashboard (BI)

<img src="https://raw.githubusercontent.com/anjaydo/movies-chatbot/refs/heads/main/images/Architecture.png" alt="Chatbot Architecture">

## 🛠️ Công nghệ

### Backend
- **FastAPI**: Framework web API hiện đại, hỗ trợ async
- **LangChain**: Framework xây dựng ứng dụng LLM với RAG
- **Google Gemini**: LLM model cho chatbot (gemini-2.5-pro)

### Database & Storage
- **PostgreSQL**: Lưu trữ metadata phim (title, release_date, vote_average, vote_count, etc.)
- **ChromaDB**: Vector database cho semantic search (embeddings của overview, quotes, metadata)
- **Sentence Transformers**: Model embedding `vinai/phobert-base` (tiếng Việt)

### Frontend & Integration
- **HTML + JavaScript**: Giao diện chatbot đơn giản, responsive
- **Metabase**: Dashboard BI với các biểu đồ visualization
- **Iframe Embedding**: Hỗ trợ nhúng chatbot vào Metabase dashboard

### Data Processing
- **SQLAlchemy**: ORM cho PostgreSQL
- **Pandas**: Xử lý dữ liệu
- **NumPy**: Tính toán vector embeddings

## 📋 Yêu cầu hệ thống

- **Hệ điều hành**: macOS, Linux, hoặc Windows (với WSL)
- **Python**: 3.9 trở lên
- **PostgreSQL**: 12+ (cài đặt qua `brew` trên macOS hoặc package manager trên Linux)
- **Google API Key**: Để sử dụng Gemini AI

## 🚀 Cài đặt & Chạy

### 1. Cài đặt PostgreSQL

**macOS:**
```bash
brew install postgresql
brew services start postgresql
createdb bigdata_project
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb bigdata_project
```

**Windows:**
- Tải và cài đặt PostgreSQL từ [postgresql.org](https://www.postgresql.org/download/windows/)
- Tạo database `bigdata_project` qua pgAdmin hoặc psql

### 2. Tạo bảng trong PostgreSQL

Tạo các bảng cần thiết (nếu có file `create_table.sql`):
```bash
psql bigdata_project -f create_table.sql
```

Hoặc tạo bảng `movies` với schema:
```sql
CREATE TABLE movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_date DATE,
    overview TEXT,
    vote_average FLOAT,
    vote_count INTEGER,
    -- thêm các cột khác nếu cần
);
```

### 3. Cài đặt Python dependencies

```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt packages
pip install -r requirements.txt
```

### 4. Cấu hình môi trường

Tạo file `.env` trong thư mục gốc:
```bash
# Google Gemini API
GOOGLE_API_KEY=your-google-api-key-here

# PostgreSQL Configuration
DB_USER=your_db_user
DB_PASS=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bigdata_project
```

### 5. Import dữ liệu

Nếu chưa có dữ liệu trong PostgreSQL, chạy script import:
```bash
python database/data_import.py
```

### 6. Load embeddings vào ChromaDB

Sau khi có dữ liệu trong PostgreSQL, load embeddings vào ChromaDB:
```bash
python load_data.py
```

Quá trình này sẽ:
- Lấy dữ liệu từ PostgreSQL
- Tạo embeddings cho overview, quotes, metadata
- Lưu vào ChromaDB collections

### 7. Chạy ứng dụng

**Cách 1: Sử dụng script**
```bash
chmod +x run.sh  # macOS/Linux
./run.sh
```

**Cách 2: Chạy trực tiếp**
```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Ứng dụng sẽ chạy tại: `http://127.0.0.1:8000`

## 📊 Tích hợp Metabase Dashboard

### Cấu hình Metabase

1. **Cài đặt Metabase** (nếu chưa có):
   ```bash
   # Docker
   docker run -d -p 3000:3000 --name metabase metabase/metabase
   ```

2. **Kết nối Metabase với PostgreSQL**:
   - Vào Metabase UI: `http://localhost:3000`
   - Thêm data source: PostgreSQL
   - Nhập thông tin kết nối database

3. **Tạo dashboard** với các biểu đồ:
   - Top 10 trending films (bar chart)
   - Genre distribution (line chart)
   - Overall statistics (total films, average vote)

### Nhúng Chatbot vào Metabase

1. **Tạo Custom Question** trong Metabase:
   - Chọn "Custom" → "Text"
   - Thêm iframe code:
   ```html
   <iframe 
     src="http://127.0.0.1:8000" 
     width="100%" 
     height="600px" 
     frameborder="0"
     style="border: none;">
   </iframe>
   ```

2. **Hoặc sử dụng Embedding URL**:
   - Trong Metabase, tạo dashboard card
   - Thêm URL: `http://127.0.0.1:8000`
   - Metabase sẽ tự động nhúng iframe

### Cấu hình CORS & Iframe

Ứng dụng đã được cấu hình sẵn để:
- Cho phép iframe embedding (middleware `AllowIframeMiddleware`)
- Hỗ trợ CORS cho Metabase (`http://localhost:3000`)
- Tự động resize khi nhúng trong iframe

Xem giao diện dashboard tại: [`images/Dashboard.png`](images/Dashboard.png)

## 📁 Cấu trúc dự án

```
movies_chatbot/
├── app.py                 # FastAPI application, routes, middleware
├── chatbot.py             # LangChain agent, RAG chatbot logic
├── config.py              # Database config, ChromaDB setup, embeddings
├── load_data.py           # Script load data từ PostgreSQL vào ChromaDB
├── requirements.txt       # Python dependencies
├── run.sh                 # Script chạy ứng dụng
├── .env                   # Environment variables (tạo mới)
│
├── database/              # Database utilities
│   ├── data_crawling.py   # Crawl data từ API
│   ├── data_import.py     # Import data vào PostgreSQL
│   └── postgres.py        # PostgreSQL connection utilities
│
├── tools/                 # LangChain tools cho agent
│   ├── quote_search.py    # Tìm phim theo quote (semantic search)
│   ├── recommend.py       # Gợi ý phim (content-based)
│   └── trending.py        # Lấy phim trending (WR)
│
├── ui/                    # Frontend
│   └── index.html         # Giao diện chatbot
│
├── chroma_db/             # ChromaDB storage (tự động tạo)
│
└── images/                 # Tài liệu
    ├── Architecture.png   # Sơ đồ kiến trúc hệ thống
    └── Dashboard.png      # Giao diện dashboard Metabase
```

## 🔧 API Endpoints

- `GET /`: Giao diện chatbot (HTML)
- `GET /chat?q={query}`: API chat với bot (JSON response)

## 🎨 Tính năng nổi bật

- **RAG (Retrieval-Augmented Generation)**: Kết hợp vector search với LLM
- **Multi-collection ChromaDB**: Tách biệt overview, quotes, metadata
- **Vietnamese Embeddings**: Sử dụng `vinai/phobert-base` cho tiếng Việt
- **Agent-based Architecture**: LangChain ReAct agent với tools
- **Iframe-ready**: Tối ưu cho embedding vào Metabase

## 📝 Lưu ý

- Đảm bảo PostgreSQL đang chạy trước khi start app
- ChromaDB sẽ tự động tạo thư mục `chroma_db/` khi chạy lần đầu
- Cần có Google API Key hợp lệ để sử dụng Gemini
- Metabase cần được cấu hình CORS nếu chạy trên domain khác

## 📄 License

Dự án này được phát triển cho mục đích học tập và demo.
