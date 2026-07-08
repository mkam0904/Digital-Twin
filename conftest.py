"""Pytest configuration: make src/ importable from the repo root."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))