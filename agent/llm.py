import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model


load_dotenv()


api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from .env")


llm = init_chat_model(
    "groq:openai/gpt-oss-20b"
)