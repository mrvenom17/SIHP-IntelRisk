# test_imports.py
from transformers import pipeline
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.ext.asyncio import create_async_engine

print("✅ All critical imports work")