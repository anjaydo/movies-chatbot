# chatbot.py
import os
from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from config import SYSTEM_PROMPT
from tools.quote_search import find_movie_by_quote
from tools.recommend import recommend_movie_from_likes
from tools.trending import get_trending_movies

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY không được tìm thấy trong .env")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.5, google_api_key=google_api_key)
tools = [find_movie_by_quote, recommend_movie_from_likes, get_trending_movies]

# PROMPT ĐẦY ĐỦ {tools} + {tool_names}
prompt = PromptTemplate.from_template(
    """Bạn là trợ lý điện ảnh thông minh. Trả lời bằng tiếng Việt.

    Bạn có các công cụ sau: {tool_names}
    Mô tả công cụ:
    {tools}

    Sử dụng định dạng sau:

    Question: câu hỏi cần trả lời

    Thought: bạn nên luôn suy nghĩ trước khi hành động
    Action: tên công cụ cần dùng
    Action Input: tham số đầu vào

    Observation: kết quả từ công cụ
    ... (lặp lại Thought/Action/Observation nếu cần)

    Thought: Tôi đã có đủ thông tin để trả lời
    Final Answer: [câu trả lời cuối cùng]

    Bắt đầu!

    Question: {input}
    {agent_scratchpad}"""
)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def chat_with_bot(query: str) -> str:
    try:
        return agent_executor.invoke({"input": query})["output"]
    except Exception as e:
        return f"Lỗi: {str(e)}"