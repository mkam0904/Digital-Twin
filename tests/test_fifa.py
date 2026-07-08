"""Tests for FifaClient: winner logic, formatting, and caching (no network)."""

from datetime import datetime
from zoneinfo import ZoneInfo

import fifa
from fifa import FifaClient

PT = ZoneInfo("America/Los_Angeles")


def vm(status="FT", hs=2, as_=1, ph=None, pa=None, home="Spain", away="Belgium",
       hour=13, minute=0, time_tbd=False):
    """Build a view-model dict like to_view_model produces."""
    return {
        "home": home,
        "away": away,
        "home_score": hs,
        "away_score": as_,
        "penalty_home": ph,
        "penalty_away": pa,
        "status": status,
        "kickoff": datetime(2026, 7, 10, hour, minute, tzinfo=PT),
        "time_tbd": time_tbd,
    }


# ---- winner logic (_row) ----

def test_ft_home_winner_flagged():
    row = FifaClient._row(vm(status="FT", hs=3, as_=1))
    *_, home_win, away_win, pen = row
    assert home_win and not away_win and pen == ""


def test_ft_away_winner_flagged():
    row = FifaClient._row(vm(status="FT", hs=0, as_=2))
    *_, home_win, away_win, pen = row
    assert away_win and not home_win


def test_draw_flags_nobody():
    row = FifaClient._row(vm(status="FT", hs=1, as_=1))
    *_, home_win, away_win, pen = row
    assert not home_win and not away_win


def test_pen_winner_and_suffix():
    row = FifaClient._row(vm(status="PEN", hs=0, as_=0, ph=3, pa=4))
    *_, home_win, away_win, pen = row
    assert away_win and not home_win
    assert pen == " (PEN 3-4)"


def test_not_started_match_shows_dash_scores():
    m = FifaClient.to_view_model({
        "home": "France", "away": "Morocco",
        "home_score": None, "away_score": None,
        "status": "NS",
        "kickoff": datetime(2026, 7, 9, 13, 0, tzinfo=PT),
    })
    row = FifaClient._row(m)
    _, _, _, status, _, hs, as_, *_ = row
    assert status == "NS" and hs == "-" and as_ == "-"


def test_time_tbd_renders_tbd():
    row = FifaClient._row(vm(time_tbd=True))
    _, time_str, tz_abbr, *_ = row
    assert time_str == "TBD" and tz_abbr == ""


# ---- formatting ----

def test_format_row_bolds_winner_only():
    rows = [FifaClient._row(vm(status="FT", hs=3, as_=1))]
    widths = FifaClient._column_widths(rows)
    line = FifaClient._format_row(rows[0], widths)
    assert "<b>Spain</b>" in line
    assert "<b>Belgium</b>" not in line


def test_column_widths_match_longest_value():
    rows = [
        FifaClient._row(vm(home="A", away="B")),
        FifaClient._row(vm(home="Longestname", away="C")),
    ]
    widths = FifaClient._column_widths(rows)
    assert widths[4] == len("Longestname")


# ---- caching (network mocked) ----

class FakeResponse:
    status_code = 200

    def json(self):
        return {"response": []}


def test_get_matches_caches_by_date(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None):
        calls.append(params)
        return FakeResponse()

    monkeypatch.setattr(fifa.requests, "get", fake_get)
    client = FifaClient(api_key="test-key")

    client.get_matches("2026-07-10")
    client.get_matches("2026-07-10")  # second call must hit cache

    assert len(calls) == 1
    assert calls[0]["timezone"] == client.tz_name


def test_api_error_returns_empty_and_does_not_cache(monkeypatch):
    class ErrorResponse:
        status_code = 500
        text = "boom"

        def json(self):
            return {}

    attempts = []

    def fake_get(url, headers=None, params=None):
        attempts.append(1)
        return ErrorResponse()

    monkeypatch.setattr(fifa.requests, "get", fake_get)
    client = FifaClient(api_key="test-key")

    assert client.get_matches("2026-07-10") == []
    client.get_matches("2026-07-10")
    assert len(attempts) == 2, "errors must not be cached"