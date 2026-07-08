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

    def today_cards(self) -> str:
        """Render TODAY / COMING UP (through the Final) / PAST, aligned, winners bolded."""
        today, tomorrow, yesterday = self._dates()

        matches_today = self.get_matches(today)
        matches_upcoming = sorted(
            self.get_matches_range(tomorrow, self.tournament_end),
            key=lambda m: m["kickoff"],
        )
        matches_past = self.get_matches(yesterday)

        sections = [
            ("PAST", matches_past),
            ("TODAY", matches_today),
            ("COMING UP", matches_upcoming)
        ]

        section_rows = [
            (label, [self._row(self.to_view_model(m)) for m in matches])
            for label, matches in sections
            if matches
        ]

        if not section_rows:
            return "⚠️ No FIFA matches found or API failed"

        widths = self._column_widths([row for _, rows in section_rows for row in rows])

        blocks = []
        for label, rows in section_rows:
            body = "\n".join(self._format_row(row, widths) for row in rows)
            blocks.append(f"**{label}:**\n<pre>\n{body}\n</pre>")

        return "\n\n".join(blocks)

        ''' 

        lines = []
        for label, rows in section_rows:
            lines.append(f"{label}:")
            lines.extend(self._format_row(row, widths) for row in rows)
            lines.append("")

        body = "\n".join(lines).rstrip()
        return f"<pre>\n{body}\n</pre>"

        '''

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
            "penalty_home": m.get("penalty_home"),
            "penalty_away": m.get("penalty_away"),
            "status": m.get("status") or "NS",
            "kickoff": m.get("kickoff"),
        }

    @staticmethod
    def _row(m: dict) -> tuple:
        """Build display fields for one match, including winner flags and any penalty score."""
        dt = m["kickoff"]
        date_str = f"{dt.strftime('%b').upper()} {dt.day}"
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

    @staticmethod
    def _column_widths(rows: list[tuple]) -> tuple[int, ...]:
        """Max width per fixed-width column (date/time/tz/status/home/hs/as/away)."""
        text_cols = [row[:8] for row in rows]
        return tuple(max(len(v) for v in col) for col in zip(*text_cols))

    '''
    @staticmethod
    def _format_row(row: tuple, widths: tuple[int, ...]) -> str:
        (date_str, time_str, tz_abbr, status, home, hs, as_, away,
         home_win, away_win, pen_suffix) = row
        w = widths

        home_padded = home.ljust(w[4])
        if home_win:
            home_padded = home_padded.replace(home, f"<b>{home.upper()}</b>", 1)

        away_padded = f"<b>{away.upper()}</b>" if away_win else away

        return (
            f"{date_str.ljust(w[0])}  {time_str.ljust(w[1])} {tz_abbr.ljust(w[2])} "
            f"{status.ljust(w[3])} {home_padded} {hs.rjust(w[5])} vs "
            f"{as_.ljust(w[6])} {away_padded}{pen_suffix}"
        )
    ''' 

    @staticmethod
    def _format_row(row: tuple, widths: tuple[int, ...]) -> str:
        (date_str, time_str, tz_abbr, status, home, hs, as_, away,
         home_win, away_win, pen_suffix) = row
        w = widths

        home_padded = home.ljust(w[4])
        if home_win:
            home_padded = home_padded.replace(home, f"<b>{home.upper()}</b>", 1)

        away_padded = f"<b>{away.upper()}</b>" if away_win else away

        return (
            f"{date_str.ljust(w[0])}  {time_str.ljust(w[1])} {tz_abbr.ljust(w[2])} "
            f"{status.ljust(w[3])} {home_padded} {hs.rjust(w[5])} vs "
            f"{as_.ljust(w[6])} {away_padded}{pen_suffix}"
        )

    def __repr__(self) -> str:
        return (
            f"FifaClient(league_id={self.league_id}, season={self.season}, "
            f"cached={list(self.cache)})"
        )