import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime, timedelta
import utilities as u

SCHEDULE_URL_PREFIX = "https://statsapi.mlb.com/api/v1/schedule?"
SCHEDULE_URL_SUFFIX = ",game(content(media(epg)),editorial(preview,recap)),linescore,team,probablePitcher(note)"

DBACKS = "Arizona Diamondbacks"
IN_MARKET = "Local (In Market)"
EXCLUSIVE = "Exclusive"
NATIONAL = "National"
MEDIA_ON = "Media On"
OUT_OF_MARKET = "Local (Out of Market)"


def get_games_on_date(date=None, days_ago=None):
    if not date:
        date = datetime.now()

        if days_ago:
            date = (date - timedelta(days=days_ago))

    if not type(date) == str:
        date = date.strftime("%Y-%m-%d")

    schedule_url_options = [
        "sportId=1",
        f"startDate={date}",
        f"endDate={date}",
        "hydrate=broadcasts(all)"
    ]

    schedule_url = SCHEDULE_URL_PREFIX + "&".join(schedule_url_options) + SCHEDULE_URL_SUFFIX

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Connection": "close"}

    r = requests.get(schedule_url, headers=headers, verify=False)
    if not r.ok:
        raise Exception(f"Failed to fetch schedule for {date}: {r.status_code} {r.reason}")
    
    try:
        games = r.json()["dates"][0]["games"]
        assert len(games) > 0
        print(f"found {len(games)} games on date {date}")
    except (KeyError, IndexError, AssertionError):
        raise Exception(f"No games found on {date}. Response: {r.text}")

    return r.json()

def get_team_game_from_games(games, team_name=DBACKS):
    for game in games["dates"][0]["games"]:
        gamepk = game["gamePk"]
        home_team = game["teams"]["home"]["team"]["name"]
        away_team = game["teams"]["away"]["team"]["name"]

        if team_name in [home_team, away_team]:
            print(f"found game: {away_team} @ {home_team}")
            print(f"    {u.pretty_print_in_timezone(game['gameDate'])}")
            print(f"    game PK: {gamepk}")
            return game
        
    raise Exception(f"No game found for {team_name} on {games['dates'][0]['date']}")

def get_stream_from_game(game, team_name=DBACKS):
    home_team = game["teams"]["home"]["team"]["name"]
    away_team = game["teams"]["away"]["team"]["name"]

    if team_name == home_team:
        home_away = "home"
    elif team_name == away_team:
        home_away = "away"
    else:
        raise Exception(f"Team {team_name} not found in gamepk {game['gamePk']} between {away_team} and {home_team}")

    for broadcast in game["broadcasts"]:
        tv = ("TV" in broadcast["type"])
        availabile = (broadcast["availability"]["availabilityText"]  in [IN_MARKET, NATIONAL, EXCLUSIVE])
        special = (broadcast["availability"]["availabilityText"]  in [NATIONAL, EXCLUSIVE])
        streaming = ("true" in str(broadcast["availableForStreaming"]).lower())
        #media_on = (broadcast["mediaState"]["mediaStateText"] == MEDIA_ON)
        english = (broadcast["language"] == "en")
        our_side = (home_away in broadcast["homeAway"])

        if tv and availabile and streaming  and english and (our_side or special):
            media_id = broadcast["mediaId"]
            print(f"found broadcast: {broadcast['name']}")
            print(f"    media ID: {media_id}")
            return media_id

        
    raise Exception(f"No valid broadcast found for {team_name} in gamepk {game['gamePk']} between {away_team} and {home_team}")

def get_game_info_for_team_on_date(team_name=DBACKS, date=None, days_ago=None):
    games = get_games_on_date(date, days_ago)
    game = get_team_game_from_games(games, team_name)

    gamepk = game["gamePk"]
    home_team = game["teams"]["home"]["team"]["name"]
    away_team = game["teams"]["away"]["team"]["name"]

    stream_id = get_stream_from_game(game, team_name)

    return {
        "gamepk": gamepk,
        "home_team": home_team,
        "away_team": away_team,
        "stream_id": stream_id
    }