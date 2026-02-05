"""Simple test to isolate the hanging issue"""
import sys
print("Step 1: Imports starting...", flush=True)

print("  - Importing os, json", flush=True)
import os
import json

print("  - Importing dotenv", flush=True)
from dotenv import load_dotenv

print("  - Loading .env file", flush=True)
load_dotenv()

print("  - Importing langchain_openai", flush=True)
from langchain_openai import ChatOpenAI

print("Step 2: Creating ChatOpenAI instance...", flush=True)
api_key = os.getenv("OPENAI_API_KEY")
print(f"  - API key exists: {bool(api_key)}", flush=True)
print(f"  - API key length: {len(api_key) if api_key else 0}", flush=True)

llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.1,
    openai_api_key=api_key
)

print("Step 3: ChatOpenAI created successfully!", flush=True)

print("Step 4: Making a simple test call...", flush=True)
try:
    result = llm.invoke("Say 'Hello World'")
    print(f"  - Result: {result.content}", flush=True)
    print("✅ SUCCESS: System is working!", flush=True)
except Exception as e:
    print(f"❌ ERROR: {e}", flush=True)
