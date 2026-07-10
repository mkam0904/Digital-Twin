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


# ---- formatting (stacked mobile layout) ----

def test_format_match_two_line_structure():
    lines = FifaClient._format_match(vm(status="FT", hs=3, as_=1)).split("\n")
    assert len(lines) == 2, "expected date/time line + teams line"
    assert "JUL 10" in lines[0] and "PDT" in lines[0]
    assert "Spain" in lines[1] and "Belgium" in lines[1]


def test_format_match_bolds_winner_only():
    out = FifaClient._format_match(vm(status="FT", hs=3, as_=1))
    assert "<b>Spain</b>" in out
    assert "<b>Belgium</b>" not in out


def test_format_match_finished_shows_scores():
    out = FifaClient._format_match(vm(status="FT", hs=3, as_=1))
    assert "3 - 1" in out


def test_format_match_not_started_shows_vs_without_scores():
    m = FifaClient.to_view_model({
        "home": "France", "away": "Morocco",
        "home_score": None, "away_score": None,
        "status": "NS",
        "kickoff": datetime(2026, 7, 9, 13, 0, tzinfo=PT),
    })
    out = FifaClient._format_match(m)
    teams_line = out.split("\n")[1]
    assert teams_line == "France vs Morocco", (
        "NS matches should show 'A vs B' with no dash scores"
    )


def test_format_match_tbd_time():
    out = FifaClient._format_match(vm(time_tbd=True))
    when_line = out.split("\n")[0]
    assert "TBD" in when_line
    assert "PDT" not in when_line, "no tz abbreviation when time is TBD"


def test_format_match_pen_suffix():
    out = FifaClient._format_match(vm(status="PEN", hs=0, as_=0, ph=3, pa=4))
    assert "(PEN 3-4)" in out
    assert "<b>Belgium</b>" in out, "penalty winner should be bolded"


def test_format_match_no_pre_or_padding():
    """Guards the mobile fix: no fixed-width padding artifacts in output."""
    out = FifaClient._format_match(vm(status="FT", hs=3, as_=1))
    assert "  " not in out, "double spaces suggest column padding crept back in"


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