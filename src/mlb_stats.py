import logging
import sys
import requests
requests.packages.urllib3.disable_warnings()
from datetime import datetime, timedelta
import utilities as u
import os
import keyboard

logger = logging.getLogger(__name__)

AT = " at "
COL = " | "

SCHEDULE_URL_PREFIX = "https://statsapi.mlb.com/api/v1/schedule?"
SCHEDULE_URL_SUFFIX = ",game(content(media(epg)),editorial(preview,recap)),linescore,team,probablePitcher(note)"

IN_MARKET = "Local (In Market)"
EXCLUSIVE = "Exclusive"
NATIONAL = "National"
MEDIA_ON = "Media On"
OUT_OF_MARKET = "Local (Out of Market)"

IN_PROGESS = "In Progress"

def get_date(days_ago=None):
    ''' Returns a datetime object for today or a specified number of days ago. '''
    date = datetime.now()

    if days_ago:
        date = (date - timedelta(days=days_ago))

    return date

def get_games_on_date(date=None, days_ago=None):
    ''' Fetches the MLB schedule for a given date or days ago.
        Returns a list of games for that date.'''
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
        logger.debug(f"found {len(games)} games on date {date}")
    except (IndexError, AssertionError) as err:
        logger.warning(f"No games found on {date}. Response: {r.text}\n{err}")
        return []
        
    return games

def process_status(game):
    '''Process the game status string to a more readable format.
       Returns a string representing the game status.'''

    status = game["status"]["detailedState"]
    if status == IN_PROGESS:
        inning = game["linescore"]["currentInningOrdinal"]
        half = game["linescore"]["inningHalf"][:3]
        status = f"{inning} {half}"
    elif ':' in status:
        status = status.split(':')[0]

    return status

def prompt_games2(date=None, days_ago=0):

    if not date:
        date = get_date(days_ago=days_ago)
    
    NUM = "#"
    MATCH = u.pretty_print_date(date)
    TZ = u.pretty_print_timezone()
    STATE = "State"
    AWAY = 0
    HOME = 1

    ml = { # max lengths
        MATCH: len(MATCH),
        NUM: len(NUM), #initial min lengths
        AT: len(AT),
        TZ: len(TZ),
        STATE: len(STATE)
    }

    games = []
    json = get_games_on_date(date=date)
    for i, game in enumerate(json):

        hn = game["teams"]["home"]["team"]["name"]
        hw = game["teams"]["home"]["leagueRecord"]["wins"]
        hl = game["teams"]["home"]["leagueRecord"]["losses"]
        an = game["teams"]["away"]["team"]["name"]
        aw = game["teams"]["away"]["leagueRecord"]["wins"]
        al = game["teams"]["away"]["leagueRecord"]["losses"]

        entry ={
            NUM: u.pesudo_hex(i),
            AWAY: f"({aw}/{al}) {an}",
            HOME: f"{hn} ({hw}/{hl})",
            TZ: u.pretty_print_time_in_timezone(game["gameDate"]),
            STATE: process_status(game)
        }

        for key, value in entry.items():
            value_length = len(str(value))
            ml[key] = max(ml.get(key, 0), value_length)

        games.append(entry)

    ml[MATCH] = max(ml[MATCH], (ml[AWAY] + ml(AT) + ml[HOME]))
    menu_width = sum(ml.values()) + (len(ml) * len(COL)) + 1


def prompt_games(date=None, days_ago=0):
    '''Prompt the user to select a game from a list of games on a given date.
       Returns a game object.'''
    
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
    game_info = { #useful game info for display
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
        "es": "Spanish",
        "fr": "French",
    }

    broadcasts = []
    ml = { # max lengths
        NAME: len(NAME), #initial min lengths
        TYPE: len(TYPE),
        AVAILABILE: len(AVAILABILE),
        FREE: len(FREE),
        STREAMING: len(STREAMING),
        STATE: len(STATE),
        LANGUAGE: len(LANGUAGE),
        TEAM: len(TEAM)+1
    }
    for broadcast in game["broadcasts"]:
        entry ={
            NAME: broadcast["name"],
            TYPE: broadcast["type"],
            AVAILABILE: broadcast.get("availability", {}).get("availabilityText", "N/A"),
            FREE: broadcast["freeGame"],
            STREAMING: broadcast["availableForStreaming"],
            STATE: broadcast["mediaState"]["mediaStateText"],
            LANGUAGE: languages[broadcast["language"]],
            TEAM: game_info["teams"][broadcast["homeAway"]]["abbr"],
        }

        for key, value in entry.items():
            value_length = len(str(value))
            ml[key] = max(ml.get(key, 0), value_length)

        entry[MEDIA_ID] = broadcast["mediaId"]

        broadcasts.append(entry)

    match_str = f"{game_info['teams']['away']['name']} at {game_info['teams']['home']['name']}"
    dash_width = sum(ml.values()) + (len(ml) * 3) + 1

    # PRINT MENU
    u.clear_terminal()
    print(f"{match_str:^{dash_width}}")
    print(f"{game_info['datetime']:^{dash_width}}")
    print("-" * dash_width)
    print(f"{'#':^1}{COL}{NAME:>{ml[NAME]}}{COL}{TYPE:<{ml[TYPE]}}{COL}{AVAILABILE:<{ml[AVAILABILE]}}{COL}{FREE:<{ml[FREE]}}{COL}{STREAMING:<{ml[STREAMING]}}{COL}{STATE:<{ml[STATE]}}{COL}{LANGUAGE:<{ml[LANGUAGE]}}{COL}{TEAM:<{ml[TEAM]}}")
    print("-" * dash_width)
    for i, b in enumerate(broadcasts):
        print(f"{u.pesudo_hex(i):>1}{COL}{b[NAME]:>{ml[NAME]}}{COL}{b[TYPE]:<{ml[TYPE]}}{COL}{b[AVAILABILE]:<{ml[AVAILABILE]}}{COL}{b[FREE]:<{ml[FREE]}}{COL}{b[STREAMING]:<{ml[STREAMING]}}{COL}{b[STATE]:<{ml[STATE]}}{COL}{b[LANGUAGE]:<{ml[LANGUAGE]}}{COL}{b[TEAM]:<{ml[TEAM]}}")
    print("-" * dash_width)

    hex_chars = ''.join(str(u.pesudo_hex(i)) for i in range(len(broadcasts)))

    if not hex_chars:
        hc = ""
    elif len(hex_chars) == 1:
        hc = f"select stream: {hex_chars},"
    else:
        hc = f"select stream: [{hex_chars[0]}-{hex_chars[-1]}],"

    print(f"{hc} quit: q")
    while True:
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN:
            choice = event.name.lower()

            if choice in hex_chars:
                return {MEDIA_ID: broadcasts[u.pesudo_hex(choice)][MEDIA_ID],
                        "gamepk": game_info["gamePk"]}
                        
            match choice:
                case 'q':
                    print("Exiting...")
                    sys.exit()
                case 'z':
                    return prompt_games(days_ago=days_ago + 1)
                case 'x':
                    return prompt_games(days_ago=days_ago - 1)

def get_team_game_from_games(games, team_name):
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

def get_stream_from_game(game, team_name):
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