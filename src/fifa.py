def to_pst(utc_str):
    dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%I:%M %p UTC")

def get_local_time(m):
    status = m.get("status", {})
    utc = status.get("utcTime")
    if not utc:
        return None
    try:
        dt = datetime.fromisoformat(utc.replace("Z", "+00:00"))
        return dt.astimezone(ZoneInfo("America/Los_Angeles"))
    except:
        return None

#####
def match_bucket(m):
    status = m.get("status", {})
    reason = status.get("reason", {}).get("short")
    if reason == "FT":
        return "FT"
    if status.get("started"):
        return "LIVE"
    return "NS"

def is_world_cup(m):
    # note: the return doesn't do anything at the moment 
    if m["league"]["name"] == "World Cup":
        return(1)    
    
#     return league_id in WORLD_CUP_LEAGUES

def safe_match(m):
    return isinstance(m, dict)

def safe_team(t):
    if isinstance(t, dict):
        return {
            "name": t.get("name") or "Unknown",
            "score": t.get("score"),
        }
    if isinstance(t, str):
        return {
            "name": t,
            "score": None,
        }
    return {
        "name": "Unknown",
        "score": None,
    }

def safe_get(d, *keys):
    """
    Safely traverse nested dictionaries.
    Returns None if any level is missing.
    """
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d

def should_include(m):
    return isinstance(m, dict)

def normalize_match(m):
    kickoff = datetime.fromisoformat(m["fixture"]["date"])
    # Convert UTC to your desired timezone
    kickoff = kickoff.astimezone(ZoneInfo("America/Los_Angeles"))
    return {
        "home": m["teams"]["home"]["name"],
        "away": m["teams"]["away"]["name"],
        "home_score": m["goals"]["home"],
        "away_score": m["goals"]["away"],
        "status": m["fixture"]["status"]["short"],
        "kickoff": kickoff,
        "date": kickoff.strftime("%Y-%m-%d"),
        "time": kickoff.strftime("%I:%M %p"),
        "timezone": kickoff.tzname(),    # PDT or PST depending on daylight savings
        "league": m["league"]["name"] # ,
        # "country": m["league"]["country"],
    }

def clean_team(x):
    if not x:
        return "Unknown"
    # -------------------------
    # CASE 1: already structured dict
    # -------------------------
    if isinstance(x, dict):
        return x.get("name") or "Unknown"
    # -------------------------
    # CASE 2: string that might actually be a dict
    # -------------------------
    if isinstance(x, str):
        # try to detect JSON-like string
        if x.strip().startswith("{") and x.strip().endswith("}"):
            try:
                obj = json.loads(x.replace("'", '"'))
                if isinstance(obj, dict):
                    return obj.get("name") or x
            except:
                pass
        # otherwise assume it's already clean
        return x.strip()
    return "Unknown"

def to_view_model(m):
    # print('to_view_model:',m)
    # to_view_model: {'home': 'Uzbekistan', 'away': 'Colombia', 'home_score': 1, 'away_score': 3, 'status': 'FT', 
    # 'kickoff': datetime.datetime(2026, 6, 17, 19, 0, tzinfo=zoneinfo.ZoneInfo(key='America/Los_Angeles')),
    #                 'date': '2026-06-17', 'time': '07:00 PM', 'timezone': 'PDT', 'league': 'World Cup'}
    def team(x):
        if isinstance(x, dict):
            return x.get("name") or "Unknown"
        if isinstance(x, str):
            return x
        return "Unknown"
    def score(x):
        return x if x is not None else "-"

    return {
        "home": m.get("home"),
        "away": m.get("away"),
        "home_score": score(m.get("home_score")),
        "away_score": score(m.get("away_score")),
        "status": m.get("status") or "NS",
        "kickoff": m.get("kickoff"),  # already datetime or None
    }

def extract_kickoff_parts(dt):
    return {
        "date": dt.strftime("%Y-%m-%d"),
        "time": dt.strftime("%I:%M %p"),
        "timezone": dt.tzinfo.key if dt.tzinfo else "Unknown"
    }

def extract_kickoff(m):
    status = m.get("status", {})
    utc = status.get("utcTime")
    if not utc:
        return None
    try:
        dt = datetime.fromisoformat(utc.replace("Z", "+00:00"))
        return dt.astimezone(ZoneInfo("America/Los_Angeles"))
    except:
        return None

def render(m):
    m = to_view_model(m)
    kickoff = m.get("kickoff")
    my_d = extract_kickoff_parts(kickoff)
    date = my_d["date"] 
    time = my_d["time"]
    timezone = my_d["timezone"]
    return (
        f"{date} {timezone}: {time}: "
        f"{m['status']}: "
        f"{m['home']} {m['home_score']} vs {m['away_score']} {m['away']}"  
    )

def get_fifa_worldcup_matches(date=None):
    print("get_fifa_worldcup_matches", date)

    if date in CACHE:
        print("CACHE HIT")
        return CACHE[date]
    else: 
        print("CACHE MISS: checking url:", SOCCER_URL)
        r = requests.get(SOCCER_URL, 
                         headers=HEADERS, 
                         params={"date": date,
                                 "league": WORLD_CUP_LEAGUE_ID,
                                 "season": WORLD_CUP_SEASON
                                 }
                        )
        data = r.json()
        print("STATUS CODE:", r.status_code)
        print("RESPONSE TEXT:", r.text)
        print('data:',data)
        if r.status_code != 200:
            print("API ERROR:", r.status_code)
            return []

        # next line is raw_matches = data["response"]["matches"]
        raw_matches = data.get("response", {})
        
        print("RAW MATCHES COUNT:", len(raw_matches))
        cleaned = []
        for m in raw_matches:
            if not isinstance(m, dict):    
                continue
            if not is_world_cup(m):
                continue
            print(json.dumps(m, indent=4))
            cleaned.append(normalize_match(m))
        CACHE[date] = cleaned
        return cleaned


def fifa_today_cards():
    print('fifa_today_cards')
    output = []
    print('TODAY_DATE:', today_date)
    print('TOMM_DATE:', tomorrow_date)
    print('YEST_DATE:', yesterday_date)
    for i, date in enumerate([today_date , tomorrow_date, yesterday_date ]):
        print(i, 'fifa_today_cards: date:',date)
        matches = get_fifa_worldcup_matches(date)
        # print('matches:', matches)
        if not matches:
            return "⚠️ No FIFA matches found or API failed"
        for m in matches:
            # print('fifa_today_cards: match:', m)
            m = to_view_model(m)
            output.append(render(m))
    return "\n".join(output)

# all: {
#   'id': 5162006, 
#   'leagueId': 226, 
#   'time': '17.06.2026 18:00', 
#   'home': {'id': 624924, 'score': 0, 'name': 'Riga FC', 'longName': 'Riga FC'}, 
#   'away': {'id': 248871, 'score': 0, 'name': 'RFS', 'longName': 'RFS'}, 
#   'eliminatedTeamId': None, 
#   'statusId': 1, 
#   'tournamentStage': '18', 
#   'status': {'utcTime': '2026-06-17T16:00:00.000Z', 
#             'halfs': {'firstHalfStarted': '17.06.2026 18:00:00'}, 
#             'periodLength': 45, 'started': False, 
#             'cancelled': False, 'finished': False
#           }, 
#   'timeTS': 1781712000000
# }


""" 


"""

APIFOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
BASE_URL = APIFOOTBALL_BASE_URL
FOOTBALL_API_KEY = APIFOOTBALL_API_KEY
SOCCER_URL = f"{BASE_URL}/fixtures"
WORLD_CUP_LEAGUE_ID = 1
WORLD_CUP_SEASON = 2026

print('FIFA_WORLDCUP_TODAY: BASE_URL:',BASE_URL)
HEADERS = {
    "x-apisports-key": FOOTBALL_API_KEY
}
world_cup_2026_countries = [
    "Argentina", "Algeria", "Australia", "Austria",
    "Belgium", "Bosnia and Herzegovina", "Brazil",
    "Cabo Verde", "Cameroon", "Canada", "Colombia", "Congo DR", "Croatia", "Curaçao", "Czechia",
    "Denmark",
    "Ecuador", "Egypt", "England",
    "France",
    "Germany", "Ghana",
    "Haiti",
    "Iran", "Iraq", "Ivory Coast",
    "Japan", "Jordan",
    "Mexico", "Morocco",
    "Netherlands", "New Zealand", "Norway",
    "Panama", "Paraguay", "Portugal",
    "Qatar",
    "Saudi Arabia", "Scotland", "Senegal", "South Africa", "South Korea", "Spain", "Sweden", "Switzerland",
    "Tunisia", "Türkiye",
    "United States", "Uruguay", "Uzbekistan"
]

# time handling 
pst = ZoneInfo("America/Los_Angeles")
now_pst = datetime.now(timezone.utc).astimezone(pst)
####
today_pst = now_pst
tomorrow_pst = today_pst + timedelta(days=1)
yesterday_pst = today_pst - timedelta(days=1)
# 
today_date = today_pst.strftime("%Y-%m-%d")
tomorrow_date = tomorrow_pst.strftime("%Y-%m-%d")
yesterday_date = yesterday_pst.strftime("%Y-%m-%d")
