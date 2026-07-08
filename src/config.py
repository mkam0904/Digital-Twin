# env var loading, constants

import os 
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY")
APIFOOTBALL_API_KEY = os.getenv("APIFOOTBALL_API_KEY")
HF_TOKEN            = os.getenv("HF_TOKEN")
PUSHOVER_USER       = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN      = os.getenv("PUSHOVER_TOKEN")

DOC_REPO_ID = "mkam0904/digital-twin-docs1"

APIFOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
SOCCER_URL = f"{APIFOOTBALL_BASE_URL}/fixtures"
WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2026
LOCAL_TZ_NAME = "America/Los_Angeles"

for name, val in [
    ("OPENAI_API_KEY", OPENAI_API_KEY),
    ("APIFOOTBALL_API_KEY", APIFOOTBALL_API_KEY),
    ("HF_TOKEN", HF_TOKEN),
    ("PUSHOVER_USER", PUSHOVER_USER),
    ("PUSHOVER_TOKEN", PUSHOVER_TOKEN),
]:
    if val is None:
        raise Exception(f"ERROR: {name} is missing from environment")

# Create client 
client = OpenAI(api_key=OPENAI_API_KEY)
