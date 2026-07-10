"""FIFA World Cup match data: fetch, cache, normalize, and render fixtures."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

import requests

__all__ = ["FifaClient"]


@dataclass
class FifaClient:
    """Owns the API key, request cache, and match-formatting logic for FIFA data.

    Attributes:
        api_key: API-Football key (sent as the x-apisports-key header).
        base_url: API-Football base URL.
        league_id: League ID for the World Cup.
        season: Season year to query.
        tz_name: IANA timezone name used for match display times.
        tournament_end: Last day of the tournament (the Final), "%Y-%m-%d".
        cache: Per-query cache, keyed by date string or "from:to" range string.
    """

    api_key: str
    base_url: str = "https://v3.football.api-sports.io"
    league_id: int = 1
    season: int = 2026
    tz_name: str = "America/Los_Angeles"
    tournament_end: str = "2026-07-19"
    cache: dict = field(default_factory=dict, init=False)

    @property
    def headers(self) -> dict:
        return {"x-apisports-key": self.api_key}

    @property
    def fixtures_url(self) -> str:
        return f"{self.base_url}/fixtures"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.tz_name)

    def _dates(self) -> tuple[str, str, str]:
        """Return (today, tomorrow, yesterday) date strings, computed fresh each call."""
        now = datetime.now(timezone.utc).astimezone(self.tz)
        today = now.strftime("%Y-%m-%d")
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        return today, tomorrow, yesterday

    def _fetch(self, params: dict, cache_key: str) -> list[dict]:
        """Shared request/filter/cache logic for both single-date and range queries."""
        if cache_key in self.cache:
            return self.cache[cache_key]

        r = requests.get(self.fixtures_url, headers=self.headers, params=params)
        if r.status_code != 200:
            print("FifaClient API error:", r.status_code, r.text)
            return []

        raw_matches = r.json().get("response", {})
        cleaned = [
            self.normalize_match(m)
            for m in raw_matches
            if isinstance(m, dict) and self.is_world_cup(m)
        ]
        self.cache[cache_key] = cleaned
        return cleaned

    def get_matches(self, date: str) -> list[dict]:
        """Fetch (or return cached) normalized World Cup matches for one date."""
        params = {
            "date": date,
            "league": self.league_id,
            "season": self.season,
            "timezone": self.tz_name,
        }
        return self._fetch(params, cache_key=date)

    def get_matches_range(self, date_from: str, date_to: str) -> list[dict]:
        """Fetch (or return cached) normalized World Cup matches within [date_from, date_to]."""
        params = {
            "from": date_from,
            "to": date_to,
            "league": self.league_id,
            "season": self.season,
            "timezone": self.tz_name,
        }
        return self._fetch(params, cache_key=f"{date_from}:{date_to}")

    def _bracket_placeholders(self) -> list[dict]:
        """Static placeholders for fixtures the API hasn't created yet.

        The API only creates a cup fixture once both teams are known, so late
        rounds are absent until earlier rounds finish. These fill the gap and
        are suppressed per-round as soon as the API returns real fixtures for
        that round (see today_cards). 2026-bracket-specific.
        """
        if self.season != 2026:
            return []

        def ph(y, mo, d, hour, minute, round_, home, away, time_tbd=False):
            return {
                "home": home,
                "away": away,
                "home_score": None,
                "away_score": None,
                "penalty_home": None,
                "penalty_away": None,
                "status": "NS",
                "kickoff": datetime(y, mo, d, hour, minute, tzinfo=self.tz),
                "round": round_,
                "time_tbd": time_tbd,
            }

        return [
            ph(2026, 7, 14, 12, 0, "Semi-finals",
               "Winner France-Morocco", "Winner Spain-Belgium", time_tbd=True),
            ph(2026, 7, 15, 12, 0, "Semi-finals",
               "Winner Norway-England", "Winner Argentina-Switzerland", time_tbd=True),
            ph(2026, 7, 18, 12, 0, "3rd Place Final",
               "Loser Semi-final 1", "Loser Semi-final 2", time_tbd=True),
            ph(2026, 7, 19, 12, 0, "Final",
               "Winner Semi-final 1", "Winner Semi-final 2"),
        ]

    def today_cards(self) -> str:
        """Render TODAY / COMING UP (through the Final) / PAST, stacked for mobile.

        Output is plain markdown/HTML that wraps naturally on narrow screens —
        no <pre> blocks, no fixed-width columns.
        """
        today, tomorrow, yesterday = self._dates()

        matches_today = self.get_matches(today)
        matches_upcoming = self.get_matches_range(tomorrow, self.tournament_end)
        matches_past = self.get_matches(yesterday)

        # Add bracket placeholders for rounds the API hasn't created yet.
        api_rounds = {(m.get("round") or "").strip().lower() for m in matches_upcoming}
        for placeholder in self._bracket_placeholders():
            if placeholder["round"].strip().lower() not in api_rounds:
                matches_upcoming.append(placeholder)
        matches_upcoming.sort(key=lambda m: m["kickoff"])

        sections = [
            ("PAST", matches_past),
            ("TODAY", matches_today),
            ("COMING UP", matches_upcoming),
        ]

        blocks = []
        for label, matches in sections:
            if not matches:
                continue

            body_lines = []
            current_round = object()  # sentinel: differs from any real value
            for m in matches:
                round_ = m.get("round")
                if round_ != current_round:
                    if body_lines:
                        body_lines.append("")
                    if round_:
                        body_lines.append(f"<b>{round_.upper()}</b>")
                    current_round = round_
                body_lines.append(self._format_match(self.to_view_model(m)))
                body_lines.append("")  # blank line between matches

            body = "\n".join(body_lines).rstrip()
            blocks.append(f"### {label}\n{body}")

        if not blocks:
            return "⚠️ No FIFA matches found or API failed"

        return "\n\n".join(blocks)

    # ---- stateless helpers (pure data transforms) ----

    @staticmethod
    def is_world_cup(m: dict) -> bool:
        return m.get("league", {}).get("name") == "World Cup"

    def normalize_match(self, m: dict) -> dict:
        """Extract and localize the fields we display, in this client's timezone."""
        kickoff = datetime.fromisoformat(m["fixture"]["date"]).astimezone(self.tz)
        penalty = (m.get("score") or {}).get("penalty") or {}
        return {
            "home": m["teams"]["home"]["name"],
            "away": m["teams"]["away"]["name"],
            "home_score": m["goals"]["home"],
            "away_score": m["goals"]["away"],
            "penalty_home": penalty.get("home"),
            "penalty_away": penalty.get("away"),
            "status": m["fixture"]["status"]["short"],
            "kickoff": kickoff,
            "round": m["league"].get("round"),
            "time_tbd": False,
        }

    @staticmethod
    def to_view_model(m: dict) -> dict:
        def score(x):
            return x if x is not None else "-"

        return {
            "home": m.get("home"),
            "away": m.get("away"),
            "home_score": score(m.get("home_score")),
            "away_score": score(m.get("away_score")),
            "penalty_home": m.get("penalty_home"),
            "penalty_away": m.get("penalty_away"),
            "status": m.get("status") or "NS",
            "kickoff": m.get("kickoff"),
            "time_tbd": m.get("time_tbd", False),
        }

    @staticmethod
    def _row(m: dict) -> tuple:
        """Build display fields for one match, including winner flags and any penalty score."""
        dt = m["kickoff"]
        date_str = f"{dt.strftime('%b').upper()} {dt.day}"
        if m.get("time_tbd"):
            time_str, tz_abbr = "TBD", ""
        else:
            hour12 = dt.hour % 12 or 12
            ampm = "am" if dt.hour < 12 else "pm"
            time_str = f"{hour12} {ampm}" if dt.minute == 0 else f"{hour12}:{dt.minute:02d} {ampm}"
            tz_abbr = dt.tzname() or ""

        status = m["status"]
        home, away = m["home"], m["away"]
        hs, as_ = m["home_score"], m["away_score"]
        ph, pa = m.get("penalty_home"), m.get("penalty_away")

        home_win = away_win = False
        pen_suffix = ""
        if status == "PEN" and ph is not None and pa is not None:
            pen_suffix = f" (PEN {ph}-{pa})"
            home_win, away_win = ph > pa, pa > ph
        elif status in ("FT", "AET") and isinstance(hs, int) and isinstance(as_, int):
            home_win, away_win = hs > as_, as_ > hs

        return (
            date_str, time_str, tz_abbr, status,
            home, str(hs), str(as_), away,
            home_win, away_win, pen_suffix,
        )

    @classmethod
    def _format_match(cls, m: dict) -> str:
        """Render one match as a compact two-line block that wraps on mobile.

        Finished:     🗓 JUL 10, 1 pm PDT
                      <b>Spain</b> 3 - 1 Belgium
        Not started:  🗓 JUL 11, 2 pm PDT
                      Norway vs France
        Penalties:    🗓 JUL 10, 1 pm PDT
                      Croatia 0 - 0 <b>Japan</b> (PEN 3-4)
        """
        (date_str, time_str, tz_abbr, status,
         home, hs, as_, away,
         home_win, away_win, pen_suffix) = cls._row(m)

        when = f"{date_str}, {time_str}"
        if tz_abbr:
            when = f"{when} {tz_abbr}"

        home_txt = f"<b>{home}</b>" if home_win else home
        away_txt = f"<b>{away}</b>" if away_win else away

        if status == "NS":
            teams = f"{home_txt} vs {away_txt}"
        else:
            teams = f"{home_txt} {hs} - {as_} {away_txt}{pen_suffix}"

        return f"🗓 {when}\n{teams}"

    def __repr__(self) -> str:
        return (
            f"FifaClient(league_id={self.league_id}, season={self.season}, "
            f"cached={list(self.cache)})"
        )