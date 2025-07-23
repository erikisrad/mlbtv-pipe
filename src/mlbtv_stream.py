
import re
import requests
requests.packages.urllib3.disable_warnings()
from mlbtv_token import Token
from milestones import Milestones
import csv
import io

BEST = "BEST"
BANDWIDTH = "BANDWIDTH"
AVG_BANDWIDTH = "AVERAGE-BANDWIDTH"
RESOLUTION = "RESOLUTION"
FRAME_RATE = "FRAME-RATE"
STREAM_INF = "#EXT-X-STREAM-INF:"
URI = "URI"
GRAPHQL_URL = "https://media-gateway.mlb.com/graphql"

def format_bandwidth(bps):

    if not isinstance(bps, int):
        try:
            bps = int(bps)
        except ValueError as err:
            print("Bandwidth must be an integer value in bps")
            raise err

    if bps >= 1_000_000_000:
        return f"{bps / 1_000_000_000:.2f} Gbps"
    elif bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mbps"
    elif bps >= 1_000:
        return f"{bps / 1_000:.2f} kbps"
    else:
        return f"{bps} bps"

#get games
#GAME_PK = "777218"
#MEDIA_ID = "408db4cb-41de-4805-80ea-62700421f33b"

class Stream():

    def __init__(self, token: Token, game_pk: str, media_id: str, quality=BEST):
        self.token = token
        self.game_pk = game_pk
        self.media_id = media_id
        self.url = "https://www.mlb.com/tv/g%s/v%s" % (self.game_pk, self.media_id)
        self.device_id = ""

        self.session_id = None
        self._manifest = None
        self._url_prefix = None
        self._playback_session_id = None
        self._playlist = None
        self._milestones = None
        self.stream_url = None

    def get_manifest(self):
        if not self._manifest:
            self._gen_manifest()
        return self._manifest
    
    def get_milestones(self):
        if not self._milestones:
            self._gen_milestones()
        return self._milestones

    def _gen_session(self):
        #begin INIT_SESSION

        payload = {
            "operationName": "initSession",
            "query": '''mutation initSession($device: InitSessionInput!, $clientType: ClientType!) {
                initSession(device: $device, clientType: $clientType) {
                    deviceId
                    sessionId
                    entitlements {
                        code
                    }
                    location {
                        countryCode
                        regionName
                        zipCode
                        latitude
                        longitude
                    }
                    clientExperience
                    features
                }
            }''',
            "variables": {
                "clientType": "WEB",
                "device": {
                    "appVersion": "8.1.0",
                    "deviceFamily": "desktop",
                    "knownDeviceId": self.device_id,
                    "languagePreference": "ENGLISH",
                    "manufacturer": "Google Inc.",
                    "model": "",
                    "os": "windows",
                    "osVersion": "10"
                }
            }
        }

        headers = {"Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Authorization": f"{self.token.token_type} {self.token.access_token}",
                "Content-Type": "application/json",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": "https://www.mlb.com/tv/g%s" % self.game_pk,
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(GRAPHQL_URL, headers=headers, json=payload, verify=False)

        if not r.ok:
            raise Exception(f"INIT_SESSION failed: {r.text}")

        self.device_id = r.json()["data"]["initSession"]["deviceId"]
        self.session_id = r.json()["data"]["initSession"]["sessionId"]

    def _gen_manifest(self):
        #begin INIT_PLAYBACK_SESSION

        if not self.session_id:
            self._gen_session()

        payload = {
            "operationName":"initPlaybackSession",
            "query":'''mutation initPlaybackSession(
                $adCapabilities: [AdExperienceType]
                $mediaId: String!
                $deviceId: String!
                $sessionId: String!
                $quality: PlaybackQuality
                $playbackCapabilities: PlaybackCapabilities
            ) {
                initPlaybackSession(
                    adCapabilities: $adCapabilities
                    mediaId: $mediaId
                    deviceId: $deviceId
                    sessionId: $sessionId
                    quality: $quality
                    playbackCapabilities: $playbackCapabilities
                ) {
                    playbackSessionId
                    playback {
                        url
                        token
                        expiration
                        cdn
                    }
                    adScenarios {
                        adParamsObj
                        adScenarioType
                        adExperienceType
                    }
                    adExperience {
                        adExperienceTypes
                        adEngineIdentifiers {
                            name
                            value
                        }
                        adsEnabled
                    }
                    heartbeatInfo {
                        url
                        interval
                    }
                    trackingObj
                }
            }''',
            "variables":{
                "adCapabilities":["GOOGLE_STANDALONE_AD_PODS"],
                "deviceId":"%s" % self.device_id,
                "mediaId":"%s" % self.media_id,
                "playbackCapabilities":{},
                "quality":"PLACEHOLDER",
                "sessionId":"%s" % self.session_id}
            }

        headers = {"Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Authorization": f"{self.token.token_type} {self.token.access_token}",
                "Content-Type": "application/json",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": self.url,
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(GRAPHQL_URL, headers=headers, json=payload, verify=False)

        if not r.ok:
            raise Exception(f"INIT_PLAYBACK_SESSION failed: {r.text}")

        self._manifest = r.json()["data"]["initPlaybackSession"]["playback"]["url"]
        self._url_prefix = self._manifest[:self._manifest.rfind("/")]
        self._playback_session_id = r.json()["data"]["initPlaybackSession"]["playbackSessionId"]

    def _gen_milestones(self):
        #begin MEDIA_INFO

        payload = {
            "operationName":"mediaInfo",
            "query":'''query mediaInfo($ids: [String]) {
                mediaInfo(ids: $ids) {
                    contentId
                    mediaId
                    milestones {
                        milestoneType
                        relativeTime
                        absoluteTime
                        title
                        keywords {
                            name
                            value
                        }
                    }
                }
            }''',"variables":{"ids":[self.media_id]}
        }

        headers = {"Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": self.url,
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(GRAPHQL_URL, headers=headers, json=payload, verify=False)

        if not r.ok:
            raise Exception(f"INIT_MILESTONES failed: {r.text}")
        
        self._milestones = Milestones(r.json()["data"]["mediaInfo"][0]["milestones"])

    def gen_playlist(self):

        if not self._manifest or self._url_prefix:
            self._gen_manifest()

        headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Priority": "u=1, i",
                    "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "sec-Ch-Ua-Platform": '"Windows"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                }

        r = requests.get(self._manifest, headers=headers)

        if not r.ok:
            raise Exception(f"gen_playlist failed: {r.text}")

        raw_playlist = r.text.split("\n")

        self._playlist = []
        for i, line in enumerate(raw_playlist):
            if line.startswith(STREAM_INF):
                raw_stream_params = line[len(STREAM_INF):]
            else:
                continue

            params = re.findall(r'(?:[^,"]|"(?:\\.|[^"])*")+', raw_stream_params) # Split the string at commas not inside quotes
            param_dict = {}
            for param in params:
                key, value = param.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')

                if BANDWIDTH in key:
                    value = format_bandwidth(value)

                param_dict[key] = value

            # for param in raw_stream_params.split(","):
            #     k, v = param.split("=")
            #     stream_params.append((k.strip(), v.strip().strip('"')))

            next_line = raw_playlist[i + 1]
            param_dict[URI] = next_line.strip()
            self._playlist.append(param_dict)
            
        self.stream_url = f"{self._url_prefix}/{self._playlist[-1][URI]}"

        for choice in self._playlist:
            print(f"Stream choice: {choice.get(RESOLUTION, 'unknown')} {choice.get(AVG_BANDWIDTH, 'unknown')} {choice.get(FRAME_RATE, 'unknown')} fps")




