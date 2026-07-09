# env var loading, constants
# Secrets are validated at first USE, not at import — so tests can import
# app/tools/ui modules without any keys set. Non-secret constants stay
# eager and importable as before.

import os
from functools import lru_cache

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Non-secret constants — safe at import time, import these freely anywhere
# ---------------------------------------------------------------------------

DOC_REPO_ID = "mkam0904/digital-twin-docs1"

APIFOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
SOCCER_URL = f"{APIFOOTBALL_BASE_URL}/fixtures"
WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2026
LOCAL_TZ_NAME = "America/Los_Angeles"

# ---------------------------------------------------------------------------
# Secrets — validated lazily, on first access
# ---------------------------------------------------------------------------


def _require_env(name: str) -> str:
    """Fetch an env var, raising a clear error only when it's needed."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"ERROR: {name} is missing from environment. "
            f"Set it in .env (local), repo secrets (CI), or Space secrets (HF)."
        )
    return value


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """OpenAI client, created once on first use."""
    return OpenAI(api_key=_require_env("OPENAI_API_KEY"))


@lru_cache(maxsize=1)
def get_openai_api_key() -> str:
    return _require_env("OPENAI_API_KEY")


@lru_cache(maxsize=1)
def get_apifootball_api_key() -> str:
    return _require_env("APIFOOTBALL_API_KEY")


@lru_cache(maxsize=1)
def get_hf_token() -> str:
    return _require_env("HF_TOKEN")


@lru_cache(maxsize=1)
def get_pushover_user() -> str:
    return _require_env("PUSHOVER_USER")


@lru_cache(maxsize=1)
def get_pushover_token() -> str:
    return _require_env("PUSHOVER_TOKEN")


# ---------------------------------------------------------------------------
# Backward compatibility (PEP 562 module-level __getattr__):
# `config.client`, `config.PUSHOVER_USER`, etc. still work — but resolve
# (and validate) lazily at access time.
#
# NOTE: `from config import client` at the top of a module binds the value
# the moment that line runs — which triggers validation at import of THAT
# module. In modules that tests import (app.py, tools, notifier, fifa),
# use `import config` + `config.client` at call sites, or call get_*()
# inside __init__ methods, to keep imports secret-free.
# ---------------------------------------------------------------------------

_LAZY_ATTRS = {
    "client": get_client,
    "OPENAI_API_KEY": get_openai_api_key,
    "APIFOOTBALL_API_KEY": get_apifootball_api_key,
    "HF_TOKEN": get_hf_token,
    "PUSHOVER_USER": get_pushover_user,
    "PUSHOVER_TOKEN": get_pushover_token,
}


def __getattr__(name: str):
    if name in _LAZY_ATTRS:
        return _LAZY_ATTRS[name]()
    raise AttributeError(f"module 'config' has no attribute '{name}'")