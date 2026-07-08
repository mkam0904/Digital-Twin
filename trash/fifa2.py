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
        cache: Per-date cache of fetched matches, keyed by "%Y-%m-%d" string.
    """

    api_key: str
    base_url: str = "https://v3.football.api-sports.io"
    league_id: int = 1
    season: int = 2026
    tz_name: str = "America/Los_Angeles"
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

    def get_matches(self, date: str) -> list[dict]:
        """Fetch (or return cached) normalized World Cup matches for a date.

        Args:
            date: Date string in "%Y-%m-%d" format, interpreted in self.tz_name
                (passed to the API so day-bucketing matches local calendar days).

        Returns:
            List of normalized match dicts. Empty list on API error.
        """
        if date in self.cache:
            return self.cache[date]

        r = requests.get(
            self.fixtures_url,
            headers=self.headers,
            params={
                "date": date,
                "league": self.league_id,
                "season": self.season,
                "timezone": self.tz_name,
            },
        )
        if r.status_code != 200:
            print("FifaClient API error:", r.status_code, r.text)
            return []

        raw_matches = r.json().get("response", {})
        cleaned = [
            self.normalize_match(m)
            for m in raw_matches
            if isinstance(m, dict) and self.is_world_cup(m)
        ]
        self.cache[date] = cleaned
        return cleaned

    def today_cards(self) -> str:
        """Render World Cup matches grouped into TODAY / COMING UP / PAST, column-aligned."""
        today, tomorrow, yesterday = self._dates()
        sections = [("TODAY", today), ("COMING UP", tomorrow), ("PAST", yesterday)]

        section_rows = []
        for label, date in sections:
            matches = self.get_matches(date)
            if matches:
                rows = [self._row(self.to_view_model(m)) for m in matches]
                section_rows.append((label, rows))

        if not section_rows:
            return "⚠️ No FIFA matches found or API failed"

        widths = self._column_widths([row for _, rows in section_rows for row in rows])

        lines = []
        for label, rows in section_rows:
            lines.append(f"{label}:")
            lines.extend(self._format_row(row, widths) for row in rows)
            lines.append("")  # blank line between sections

        body = "\n".join(lines).rstrip()
        return f"```\n{body}\n```"

    # ---- stateless helpers (pure data transforms) ----

    @staticmethod
    def is_world_cup(m: dict) -> bool:
        return m.get("league", {}).get("name") == "World Cup"

    def normalize_match(self, m: dict) -> dict:
        """Extract and localize the fields we display, in this client's timezone."""
        kickoff = datetime.fromisoformat(m["fixture"]["date"]).astimezone(self.tz)
        return {
            "home": m["teams"]["home"]["name"],
            "away": m["teams"]["away"]["name"],
            "home_score": m["goals"]["home"],
            "away_score": m["goals"]["away"],
            "status": m["fixture"]["status"]["short"],
            "kickoff": kickoff,
            "league": m["league"]["name"],
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
            "status": m.get("status") or "NS",
            "kickoff": m.get("kickoff"),
        }

    @staticmethod
    def _row(m: dict) -> tuple[str, str, str, str, str, str, str, str]:
        """Build the raw display fields for one match: date, time, tz, status, teams, scores."""
        dt = m["kickoff"]
        date_str = f"{dt.strftime('%b').upper()} {dt.day}"
        hour12 = dt.hour % 12 or 12
        ampm = "am" if dt.hour < 12 else "pm"
        time_str = f"{hour12} {ampm}" if dt.minute == 0 else f"{hour12}:{dt.minute:02d} {ampm}"
        tz_abbr = dt.tzname() or ""
        return (
            date_str, time_str, tz_abbr, m["status"],
            m["home"], str(m["home_score"]), str(m["away_score"]), m["away"],
        )

    @staticmethod
    def _column_widths(rows: list[tuple]) -> tuple[int, ...]:
        """Max width per column across all rows, so every row can be padded to match."""
        return tuple(max(len(v) for v in col) for col in zip(*rows))

    @staticmethod
    def _format_row(row: tuple, widths: tuple[int, ...]) -> str:
        (date_str, time_str, tz_abbr, status, home, hs, as_, away,
         home_win, away_win, pen_suffix) = row
        w = widths

        home_marked = (home.upper() if home_win else home).ljust(w[4])
        away_marked = away.upper() if away_win else away

        return (
            f"{date_str.ljust(w[0])}  {time_str.ljust(w[1])} {tz_abbr.ljust(w[2])} "
            f"{status.ljust(w[3])} {home_marked} {hs.rjust(w[5])} vs "
            f"{as_.ljust(w[6])} {away_marked}{pen_suffix}"
        )