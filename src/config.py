import os 
import inspect
from openai import OpenAI
from dotenv import load_dotenv
from IPython.display import Markdown, display 
import gradio as gr
import json
import requests
import random
from pprint import pprint
import re
import uuid
from huggingface_hub import hf_hub_download
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import pytz
from zoneinfo import ZoneInfo

import sys
print(sys.executable)

import logging

logging.basicConfig(
    filename="gradio_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

CACHE = {}
load_dotenv()
use_freeapilive = 0 

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFOOTBALL_API_KEY = os.getenv("APIFOOTBALL_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")

APIFOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
SOCCER_URL = f"{APIFOOTBALL_BASE_URL}/fixtures"
WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2026
LOCAL_TZ_NAME = "America/Los_Angeles"

# Load API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFOOTBALL_API_KEY = os.getenv("APIFOOTBALL_API_KEY")

e_l = ['OPENAI_API_KEY', 'APIFOOTBALL_API_KEY')
for e in e_l:
    if globals()[e] is None: 
        raise Exception(f"ERROR: {e} is None")
    else:
        print(f"{e}: {globals()[e][:4]}")

# Create client 
client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------
# Setup
# -----------------------
HF_TOKEN = os.getenv("HF_TOKEN")
DOC_REPO_ID = "mkam0904/digital-twin-docs"
print("DOC_REPO_ID:", DOC_REPO_ID)
doc_files = {
    "Overview Doc": "document_overview.txt",
    "Education Doc": "document_education.txt",
    "Professional Experience Doc": "document_professional_experience.txt",
}
documents = []
for source_name, filename in doc_files.items():
    path = hf_hub_download(
        repo_id=DOC_REPO_ID,
        filename=filename,
        repo_type="dataset",
        token=HF_TOKEN,
    )
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    documents.append({
        "text": text,
        "source": source_name
    })
    print(f"Loaded: {source_name}")