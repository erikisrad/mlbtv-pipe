from datetime import datetime
import time
import os
import requests
import random
import string
import base64
import hashlib

from .mlbtv_token import Token

INTERACT_URL = "https://ids.mlb.com/oauth2/aus1m088yK07noBfh356/v1/interact"
INTROSPECT_URL = "https://ids.mlb.com/idp/idx/introspect"
IDENTITY_URL = "https://ids.mlb.com/idp/idx/identify"
CHALLENGE_URL = "https://ids.mlb.com/idp/idx/challenge"
ANSWER_URL = "https://ids.mlb.com/idp/idx/challenge/answer"
TOKEN_URL = "https://ids.mlb.com/oauth2/aus1m088yK07noBfh356/v1/token"

USERNAME = "erik.rad@gmail.com"
PASSWORD = "#a7ZB8b!X53CjLC"

'''
The client_id is a fundamental credential for an OAuth 2.0/OpenID Connect client (in this case, the MLB.com website or application). 
It identifies the specific application making the request to the authorization server (ids.mlb.com).

The value of client_id is pre-configured on the client. 
It's a value that the developers of the MLB.com application obtain when they register their application with the identity provider 
    (presumably Okta, given the URL structure and headers).

The network request merely sends the client_id as part of the payload. 
It doesn't reveal the logic used to generate or retrieve that value on the client side.
'''
CLIENT_ID = "0oap7wa857jcvPlZ5355"

def gen_random_string(n):
    """Generate a random string of uppercase letters and digits of length n."""
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

class Account:

    def __init__(self, username=USERNAME, password=PASSWORD):
        self.username = username
        self.password = password
        self.__token__ = None

        self.code_verifier = None
        self.code_challenge = None
        self.interaction_handle = None
        self.introspect_state_handle = None
        self.identity_state_handle = None
        self.id_email = None
        self.id_password = None
        self.challenge_state_handle = None
        self.answer_state_handle = None
        self.interaction_code = None

    def __gen_challenge__(self):
        code_challenge = self.code_verifier.encode('ascii')
        code_challenge = hashlib.sha256(code_challenge)
        code_challenge = code_challenge.digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge)
        code_challenge = code_challenge.decode('ascii')
        code_challenge = code_challenge[:-1]
        self.code_challenge = code_challenge

    def get_token(self):
        if not self.__token__:
            self.__gen_token__()
            
        return self.__token__

    def __interact__(self):
        #begin INTERACT
        state_param = gen_random_string(64)
        nonce_param = gen_random_string(64)

        self.code_verifier = gen_random_string(58)
        self.__gen_challenge__()

        payload = [f"client_id={CLIENT_ID}",
                "scope=openid%20email",
                "redirect_uri=https%3A%2F%2Fwww.mlb.com%2Flogin",
                f"code_challenge={self.code_challenge}",
                "code_challenge_method=S256",
                f"state={state_param}",
                f"nonce={nonce_param}"
        ]
        payload = '&'.join(payload)

        headers = {"Accept": "application/json",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": "https://www.mlb.com/login?redirectUri=/",
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(INTERACT_URL, headers=headers, data=payload, verify=False)

        if not r.ok:
            raise Exception(f"INTERACT failed: {r.text}")

        self.interaction_handle =  r.json()["interaction_handle"]

    def __introspect__(self):
        #begin INTROSPECT

        if not self.interaction_handle:
            self.__interact__() 

        payload = '{"interactionHandle":"%s"}' % self.interaction_handle

        headers = {"Accept": "application/ion+json; okta-version=1.0.0",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en",
                "Content-Type": "application/ion+json; okta-version=1.0.0",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": "https://www.mlb.com/login?redirectUri=/",
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(INTROSPECT_URL, headers=headers, data=payload, verify=False)

        if not r.ok:
            raise Exception(f"INTROSPECT failed: {r.text}")

        self.introspect_state_handle =  r.json()["stateHandle"]

    def __identity__(self):
        # begin IDENTITY

        if not self.introspect_state_handle:
            self.__introspect__()

        payload = '{"identifier":"%s","stateHandle":"%s"}' % (self.username, self.introspect_state_handle)

        headers = {"Accept": "application/json; okta-version=1.0.0",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en",
                "Content-Type": "application/json",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": "https://www.mlb.com/login?redirectUri=/",
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(IDENTITY_URL, headers=headers, data=payload, verify=False)

        if not r.ok:
            raise Exception(f"IDENTITY failed: {r.text}")

        self.identity_state_handle = r.json()["stateHandle"]
        authenticators = r.json()["authenticators"]["value"]
        self.id_email = None
        self.id_password = None
        for value in authenticators:
            if value["type"] == "email":
                self.id_email = value["id"]
            elif value["type"] == "password":
                self.id_password = value["id"]
            if self.id_email and self.id_password:
                break

        if not self.id_email or not self.id_password:
            raise Exception(f"IDENTITY failed, email or password authenticator not found in IDENTITY response: {r.text}")

    def __challenge__(self):
        # begin CHALLENGE

        if not self.id_password or not self.identity_state_handle:
            self.__identity__()

        payload = '{"authenticator":{"id":"%s"},"stateHandle":"%s"}' % (self.id_password, self.identity_state_handle)

        headers = {"Accept": "application/json; okta-version=1.0.0",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en",
                "Content-Type": "application/json",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": "https://www.mlb.com/login?redirectUri=/",
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(CHALLENGE_URL, headers=headers, data=payload, verify=False)

        if not r.ok:
            raise Exception(f"CHALLENGE failed: {r.text}")

        self.challenge_state_handle =  r.json()["stateHandle"]

    def __answer__(self):
        # begin ANSWER

        if not self.challenge_state_handle:
            self.__challenge__()

        payload = '{"credentials":{"passcode":"%s"},"stateHandle":"%s"}' % (self.password, self.challenge_state_handle)

        headers = {"Accept": "application/json; okta-version=1.0.0",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en",
                "Content-Type": "application/json",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": "https://www.mlb.com/login?redirectUri=/",
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(ANSWER_URL, headers=headers, data=payload, verify=False)

        if not r.ok:
            raise Exception(f"ANSWER failed: {r.text}")

        self.answer_state_handle =  r.json()["stateHandle"]
        success_with_interaction_code = r.json()["successWithInteractionCode"]["value"]
        self.interaction_code = None
        for value in success_with_interaction_code:
            if value["name"] == "interaction_code":
                self.interaction_code = value["value"]
                break

        if not self.interaction_code:
            raise Exception(f"ANSWER failed: interaction code not found in response: {r.text}")
        
    def __gen_token__(self):
        #begin TOKEN

        if not self.interaction_code:
            self.__answer__()

        if not self.code_verifier:
            raise ValueError("Code verifier is not set. Authentication is occuring out of order.")

        payload = [f"client_id={CLIENT_ID}",
                "redirect_uri=https://www.mlb.com/login",
                "grant_type=interaction_code",
                f"code_verifier={self.code_verifier}",
                f"interaction_code={self.interaction_code}"
        ]
        payload = '&'.join(payload)

        headers = {"Accept": "application/json",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.mlb.com",
                "Priority": "u=1, i",
                "Referer": "https://www.mlb.com/login?redirectUri=/",
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        r = requests.post(TOKEN_URL, headers=headers, data=payload, verify=False)

        if not r.ok:
            raise Exception(f"TOKEN failed: {r.text}")

        self.__token__ = Token(r.json()) 

        #print(f"Access token generated: {self.__token__}")

