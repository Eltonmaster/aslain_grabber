#V0.5
import requests
import bs4
import os
from time import sleep
from time import time
from subprocess import Popen
import json
from xml.dom import minidom
import re
import pywinauto

WOT_PATH = "E:\\Games\\World_of_Tanks_EU"
DEBUG = True

CONFIG_PATH = os.path.join(WOT_PATH, "mods\\configs\\spoter\\marksOnGunExtended\\marksOnGunExtended.json")
WOT_VERSION_PATH = os.path.join(WOT_PATH, "game_info.xml")
ASLAIN_LOG_PATH = os.path.join(WOT_PATH, "Aslain_Modpack\\_Aslains_Installer.log")

def start_game():
    global DEBUG
    print("Starte Spiel")
    sleep(2)
    try:
        app = pywinauto.Application().connect(path="wgc.exe")
        form = app.window(title_re="Wargaming.net Game Center")
        form_rect = form.rectangle()
        height = form_rect.bottom - form_rect.top
        width = form_rect.right - form_rect.left

        right_move = int(width/100*10)
        down_move = int(height/100*90)

        form.click(coords=(right_move, down_move))
    except:
        if DEBUG:
            print("ERROR in der start_game function")

def wait_for_patch():
    global DEBUG
    print("Teste ob patch fertig")
    doc = minidom.parse(WOT_VERSION_PATH)
    version = doc.getElementsByTagName("version")[0]
    while version.attributes["installed"].value != version.attributes["available"].value:
        if DEBUG: print(f"Patch läuft noch - {version.attributes['installed'].value} != {version.attributes['available'].value}")
        sleep(1)
        doc = minidom.parse(WOT_VERSION_PATH)
        version = doc.getElementsByTagName("version")[0]  
    if DEBUG: print(f"Patch scheint fertig zu sein - {version.attributes['installed'].value}")
    return 

def wait_for_version(aslain_version):
    print("Teste ob sich die Versionen von Aslain und WoT gleichen")
    doc = minidom.parse(WOT_VERSION_PATH)
    version = doc.getElementsByTagName("version")[0]
    local_version = ".".join(version.attributes["installed"].value.split(".")[:3])
    while local_version != aslain_version:
        if DEBUG: print(f"Versionen noch nicht gleich  {aslain_version} != {local_version}")
        sleep(1)
        doc = minidom.parse(WOT_VERSION_PATH)
        version = doc.getElementsByTagName("version")[0]  
        local_version = ".".join(version.attributes["installed"].value.split(".")[:3])
    return 

def wait_for_aslain():
    global ASLAIN_LOG_PATH
    if DEBUG: print("Lesen des Aslain-log")
    while True:
        if time() - os.stat(ASLAIN_LOG_PATH).st_mtime < 2:
            break
        if DEBUG: print(f"Log time diff: {time() - os.stat(ASLAIN_LOG_PATH).st_mtime}")
        sleep(.25)
    while True:
        with open(ASLAIN_LOG_PATH, 'r') as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            if "_Aslains_movetree_mods.bat at mods finished" in last_line:
                break
            if DEBUG: print(f"Aslain läuft noch - {last_line}")
            sleep(.5)
        

def config_moe():
    global CONFIG_PATH
    while not os.path.exists(CONFIG_PATH):
        if DEBUG: print("MOE-Config noch nicht vorhanden")
        sleep(.5)
    with open(CONFIG_PATH, "r") as f:
        text = f.read()
        begin_char = text[:3]
        dat = json.loads(text[3:])
    dat["UI"] = 4
    dat["backgroundData"]["height"] = 42
    dat["backgroundData"]["width"] = 54
    dat["panel"].pop("index", None)
    dat["panel"].pop("visible", None)
    dat["panel"].pop("limit", None)
    dat["panel"]["width"] = 163
    dat["panel"]["height"] = 50
    dat["showInTechTreeMastery"] = True
    dat_string = json.dumps(dat, indent=4)
    output_string = begin_char + dat_string
    with open(CONFIG_PATH, "w") as f:
        f.write(output_string)


appdata_path = os.getenv("LOCALAPPDATA")
folder_path = os.path.join(appdata_path, "Aslain-Checker")
file_path = os.path.join(folder_path, "last_url")
aslain_path = os.path.join(folder_path, "aslain_installer.exe")
if not os.path.exists(folder_path):
    os.mkdir(folder_path)

last_url = ""

if os.path.exists(file_path):
    with open(file_path, "r") as f:
        last_url = f.read()

resp = requests.get("https://aslain.com/index.php?/topic/13-download-%E2%98%85-world-of-tanks-%E2%98%85-modpack/")
soup = bs4.BeautifulSoup(resp.text, "html.parser")

url = None

for entry in soup.find_all("a", href=True):
    if "ftp.wot.modpack" in entry["href"]:
        url = entry["href"]
        break

aslain_version_short = re.search(r"\d+\.\d+\.\d", url).group(0)
aslain_version_full = re.search(r"\d+\.\d+\.\d.+?.exe", url).group(0)[:-4]

if url != last_url:
    print(f"Version {aslain_version_full} verfügbar!")
    print("Starte Download")
    with requests.get(url, stream=True) as rq:
        rq.raise_for_status()
        with open(aslain_path, "wb") as f:
            for chunk in rq.iter_content(chunk_size=1024):
                f.write(chunk)    
    print("Download Fertiggestellt")
    with open(file_path, "w") as f:
        f.write(url)

    wait_for_patch()
    wait_for_version(aslain_version_short)

    print("Starte den neuen Installer")
    p = Popen(aslain_path)
    p.wait()
    wait_for_aslain()
    print("Einstellen von MOE")
    config_moe()
    start_game()

else:
    print("Neuste Version bereits heruntergeladen")
    start_game()
    print("Closing in 3")
    sleep(1)
    print("Closing in 2")
    sleep(1)
    print("Closing in 1")
    sleep(1)




