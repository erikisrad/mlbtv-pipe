import subprocess
import requests
import time
import xml.etree.ElementTree as ET

VLC_LOCATION = "C:/Program Files/VideoLAN/VLC/vlc.exe"
HOSTNAME = "localhost"
PORT = 8080
PASSWORD = "mlbtv"

class VLC_Handler():

    def __init__(self, stream, args=[]):
        self.stream = stream
        self.args = args + ["--extraintf=http", f"--http-host={HOSTNAME}", f"--http-port={PORT}", f"--http-password={PASSWORD}"]
        self.url = f"http://{HOSTNAME}:{PORT}/requests/status.xml"

        self.handle = None
    

    def start(self):
        self.handle = subprocess.Popen([VLC_LOCATION, self.stream.get_master_playlist()] + self.args)
        self.monitor()

    def monitor(self):
        skip = False
        if skip:
            commercials = self.stream.get_commercial_breaks()
            while self.handle.poll() is None:
                t = int(self.get_status("time")) * 1000  # Convert to milliseconds
                commercial_break = next((end for start, end in commercials if start <= t <= end), None)
                if commercial_break:
                    self.set_time(round(commercial_break/1000))
                    time.sleep(5)

                time.sleep(.25)


    def send(self, cmd=None, params=None):
        if not self.handle:
            raise RuntimeError("VLC handler is not running")
        
        target = f"{self.url}"
        if cmd:
            target+=f"?command={cmd}"
        if params and isinstance(params, dict):
            for k, v in params.items():
                target += f"&{k}={v}"

        response = requests.get(target, auth=("", PASSWORD))
        
        if response.ok:
            return ET.fromstring(response.text)
        else:
            raise Exception(f"Failed to send.\nStatus code: {response.status_code}\nResponse: {response.text}")

    def get_status(self, target=None):
        res = self.send()
        if target:
            return res.find(target).text
        return res

    def set_time(self, time):
        cmd = "seek"
        params = {"val": str(time)}
        return(self.send(cmd, params))