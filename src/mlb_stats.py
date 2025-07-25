import sys
import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime, timedelta
import utilities as u
import os
import keyboard

SCHEDULE_URL_PREFIX = "https://statsapi.mlb.com/api/v1/schedule?"
SCHEDULE_URL_SUFFIX = ",game(content(media(epg)),editorial(preview,recap)),linescore,team,probablePitcher(note)"

DBACKS = "Arizona Diamondbacks"
IN_MARKET = "Local (In Market)"
EXCLUSIVE = "Exclusive"
NATIONAL = "National"
MEDIA_ON = "Media On"
OUT_OF_MARKET = "Local (Out of Market)"

IN_PROGESS = "In Progress"

def get_date(days_ago=None):
    date = datetime.now()

    if days_ago:
        date = (date - timedelta(days=days_ago))

    return date

def get_games_on_date(date=None, days_ago=None):
    if not date:
        date = get_date(days_ago=days_ago)

    if isinstance(date, datetime):
        date = date.strftime("%Y-%m-%d")

    assert isinstance(date, str), "date must be a string or datetime object"

    if date.isdigit() and len(date) == 10:
        date = f"{date[:4]}-{date[5:7]}-{date[8:10]}"

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
    except (IndexError, AssertionError) as err:
        print(f"No games found on {date}. Response: {r.text}\n{err}")
        return []
        

    return games

def process_status(game):
    """
    Process the game status string to a more readable format.
    """
    status = game["status"]["detailedState"]
    if status == IN_PROGESS:
        inning = game["linescore"]["currentInningOrdinal"]
        half = game["linescore"]["inningHalf"][:3]
        status = f"{inning} {half}"
    elif ':' in status:
        status = status.split(':')[0]

    return status

def prompt_games(date=None, days_ago=0):
    
    AT = " at "
    COL = " | "

    choices = []
    lengths = {
        "home": 20, #min
        "away": 20, #min
        "status": 6, #min
        "time": 8, #static
        "number": 1, #static
        "at": len(AT), #static 
        "columns": len(COL) * 3 #static
    }

    if not date:
        date = get_date(days_ago=days_ago)
    
    games = get_games_on_date(date=date)
    for game in games:

        status = process_status(game)
        lengths["status"] = max(lengths["status"], len(status))

        time = u.pretty_print_time_in_timezone(game["gameDate"])

        home = {}
        home["team"] = game["teams"]["home"]["team"]["name"]
        home["wins"] = game["teams"]["home"]["leagueRecord"]["wins"]
        home["losses"] = game["teams"]["home"]["leagueRecord"]["losses"]
        home_str = f"{home['team']} ({home['wins']}/{home['losses']})"
        lengths["home"] = max(lengths["home"], len(home_str))
        
        away = {}
        away["team"] = game["teams"]["away"]["team"]["name"]
        away["wins"] = game["teams"]["away"]["leagueRecord"]["wins"]
        away["losses"] = game["teams"]["away"]["leagueRecord"]["losses"]
        away_str = f"({away['wins']}/{away['losses']}) {away['team']}"
        lengths["away"] = max(lengths["away"], len(away_str))       

        choices.append({
            "home": home_str,
            "away": away_str,
            "time": time,
            "status": status,
            "game" : game
        })

    u.clear_terminal()
    dash_width = sum(list(lengths.values()))
    match_width = lengths["home"] + lengths["at"] + lengths["away"]
    d = u.pretty_print_date(date)
    print("-" * dash_width)
    print(f"{'#':>{lengths['number']}}{COL}{d:^{match_width}}{COL}{u.pretty_print_timezone():^{lengths['time']}}{COL}{'State':<{lengths['status']}}")
    print("-" * dash_width)

    if not choices:
        print(f"{'':>{lengths['number'] + len(COL)}}{'No games':^{match_width}}")
    for i, c in enumerate(choices):
        print(f"{u.pesudo_hex(i):>{lengths['number']}}{COL}{c['away']:>{lengths['away']}}{AT}{c['home']:<{lengths['home']}}{COL}{c['time']}{COL}{c['status']}")

    print("-" * dash_width)
    
    hex_chars = ''.join(str(u.pesudo_hex(i)) for i in range(len(choices)))

    if not hex_chars:
        hc = ""
    elif len(hex_chars) == 1:
        hc = f"inspect game: {hex_chars},"
    else:
        hc = f"inspect game: [{hex_chars[0]}-{hex_chars[-1]}],"

    print(f"previous: z, quit: q, {hc} next: x")
    while True:
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN:
            choice = event.name.lower()

            if choice in hex_chars:
                return choices[u.pesudo_hex(choice)]["game"]
            
            match choice:
                case 'q':
                    print("Exiting...")
                    sys.exit()
                case 'z':
                    return prompt_games(days_ago=days_ago + 1)
                case 'x':
                    return prompt_games(days_ago=days_ago - 1)

def prompt_streams(game):
    """
    Prompt the user to select a stream for the given game.
    Returns a media_id
    """
    game_info = {
        "gamePk": game["gamePk"],
        "datetime": u.pretty_print_datetime_in_timezone(game["gameDate"]),
        "status": process_status(game),
        "venue": game["venue"]["name"],
        "teams":{
            "home": {
                "name": game["teams"]["home"]["team"]["name"],
                "abbr": game["teams"]["home"]["team"]["abbreviation"],
                "location": game["teams"]["home"]["team"]["locationName"],
                "record": f"{game['teams']['home']['leagueRecord']['wins']}/{game['teams']['home']['leagueRecord']['losses']}",
                "pitcher": game["teams"]["home"]["probablePitcher"]["fullName"] if "probablePitcher" in game["teams"]["home"] else "TBD"
            },
            "away": {
                "name": game["teams"]["away"]["team"]["name"],
                "abbr": game["teams"]["away"]["team"]["abbreviation"],
                "location": game["teams"]["away"]["team"]["locationName"],
                "record": f"{game['teams']['away']['leagueRecord']['wins']}/{game['teams']['away']['leagueRecord']['losses']}",
                "pitcher": game["teams"]["away"]["probablePitcher"]["fullName"] if "probablePitcher" in game["teams"]["away"] else "TBD"
            }
        }
    }

    NAME = "Name"
    MEDIA_ID = "MediaID"
    TYPE = "Type"
    AVAILABILE = "Availability"
    FREE = "Free"
    STREAMING = "Streaming"
    STATE = "State"
    LANGUAGE = "Language"
    TEAM = "Team"

    languages = {
        "en": "English",
        "es": "Spanish"
    }

    broadcasts = []
    ml = { # max lengths
        NAME: len(NAME), #initial min lengths
        MEDIA_ID: len(MEDIA_ID),
        TYPE: len(TYPE),
        AVAILABILE: len(AVAILABILE),
        FREE: len(FREE),
        STREAMING: len(STREAMING),
        STATE: len(STATE),
        LANGUAGE: len(LANGUAGE),
        TEAM: len(TEAM)
    }
    for broadcast in game["broadcasts"]:
        entry ={
            NAME: broadcast["name"],
            MEDIA_ID: broadcast["mediaId"],
            TYPE: broadcast["type"],
            AVAILABILE: broadcast["availability"]["availabilityText"],
            FREE: broadcast["freeGame"],
            STREAMING: broadcast["availableForStreaming"],
            STATE: broadcast["mediaState"]["mediaStateText"],
            LANGUAGE: languages[broadcast["language"]],
            TEAM: game_info["teams"][broadcast["homeAway"]],
        }

        broadcasts.append(entry)

        for key, value in entry.items():
            value_length = len(str(value))
            ml[key] = max(ml.get(key, 0), value_length)

    match_str = f"{game_info['teams']['away']['name']} @ {game_info['teams']['home']['name']}"
    dash_width = sum(ml.values()) + len(ml) * 3

    u.clear_terminal()

    print(f"{match_str}")
    print(f"{game_info['datetime']}")
    print("-" * dash_width)
    print(f"{NAME:<{ml[NAME]}} | {MEDIA_ID:<{ml[MEDIA_ID]}} | {TYPE:<{ml[TYPE]}} | {AVAILABILE:<{ml[AVAILABILE]}} | {FREE:<{ml[FREE]}} | {STREAMING:<{ml[STREAMING]}} | {STATE:<{ml[STATE]}} | {LANGUAGE:<{ml[LANGUAGE]}} | {TEAM:<{ml[TEAM]}}")
    for b in broadcasts:
        print(f"{b[NAME]:<{ml[NAME]}} | {b[MEDIA_ID]:<{ml[MEDIA_ID]}} | {b[TYPE]:<{ml[TYPE]}} | {b[AVAILABILE]:<{ml[AVAILABILE]}} | {b[FREE]:<{ml[FREE]}} | {b[STREAMING]:<{ml[STREAMING]}} | {b[STATE]:<{ml[STATE]}} | {b[LANGUAGE]:<{ml[LANGUAGE]}} | {b[TEAM]:<{ml[TEAM]}}")
        

def get_team_game_from_games(games, team_name=DBACKS):
    for game in games:
        gamepk = game["gamePk"]
        home_team = game["teams"]["home"]["team"]["name"]
        away_team = game["teams"]["away"]["team"]["name"]

        if team_name in [home_team, away_team]:
            print(f"found game: {away_team} at {home_team}")
            print(f"    {u.pretty_print_datetime_in_timezone(game['gameDate'])}")
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
        free = ("true" in str(broadcast["freeGame"]).lower())
        streaming = ("true" in str(broadcast["availableForStreaming"]).lower())
        #media_on = (broadcast["mediaState"]["mediaStateText"] == MEDIA_ON)
        english = (broadcast["language"] == "en")
        our_side = (home_away in broadcast["homeAway"])

        if tv and (availabile or free) and streaming and english and (our_side or special):
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