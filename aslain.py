#v0.93
import requests, bs4, os, re, sys, json, logging
from time import sleep, time
from subprocess import Popen
from xml.dom import minidom
from tqdm import tqdm
from urllib3.exceptions import ProtocolError
from logging.handlers import RotatingFileHandler
from pywinauto.application import Application
from pywinauto import timings
from pywinauto.findwindows import ElementNotFoundError
import warnings
warnings.simplefilter('ignore', category=UserWarning)


DEBUG = False
DEV = False
START_GAME = True
S = requests.Session()


def version_compare(version1, version2):
    # version1 < version2 -> -1
    # version2 < version1 -> 1
    # version1 = version2 -> 0
    add_version_1 = ""
    add_version_2 = ""
    if "_" in version1:
        add_version_1 = version1.split("_")[1]
        version1 = version1.split("_")[0]
    if "_" in version2:
        add_version_2 = version2.split("_")[1]
        version2 = version2.split("_")[0]
    version_1_list = version1.split(".")
    version_2_list = version2.split(".")
    while len(version_1_list) != len(version_2_list):
        if len(version_1_list) > len(version_2_list):
            version_2_list.append("0")
        else:
            version_1_list.append("0")
    print(version_1_list)
    print(version_2_list)   
    if version_2_list == version_1_list:
        if add_version_1 > add_version_2:
            return 1
        if add_version_2 > add_version_1:
            return -1
        return 0
    for i in range(0, len(version_1_list)):
        if version_1_list[i] > version_2_list[i]:
            return 1 
        if version_2_list[i] > version_1_list[i]:
            return -1
   

def update():
    global S
    if not DEV:
        print("Überprüfe auf Aslain-Checker Update")
        online_code = S.get("https://raw.githubusercontent.com/Eltonmaster/aslain_grabber/main/aslain.py").content.decode("utf-8")
        online_version = online_code.split("\n")[0][2:]
        print(__file__)
        with open(__file__, "r") as f:
            local_code = f.read()
            local_version = local_code.split("\n")[0][2:]
            try:
                float(local_version)
            except:
                local_version = "0.0"
        if float(online_version) > float(local_version):
            print("Update gefunden!\nÜberschreibe lokalen Code")
            with open(__file__, "w", encoding="utf-8") as f:
                f.write(online_code)
            print("Installieren der pip Packages")
            resp = S.get("https://raw.githubusercontent.com/Eltonmaster/aslain_grabber/main/requirements.txt").content.decode("utf-8")
            with open("temp_requirements.txt", "w", encoding="utf-8") as f:
                f.write(resp)
            pip_process = Popen(["pip", "install", "-r", "temp_requirements.txt"])
            pip_process.wait()
            Popen(["python", __file__])
            sys.exit()
        print("Aslain Checker ist up to date")
    else:
        print("Skipping in dev mode")


def start_game():
    global DEBUG
    if not DEV and START_GAME:
        print("Starte Spiel")
        sleep(1)
        try:
            Popen(EXECUTABLE_PATH)
        except:
            if DEBUG:
                print("ERROR in der start_game function")
    else:
        print("Skipping in dev mode")

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
        try:
            with open(ASLAIN_LOG_PATH, 'r') as f:
                lines = f.read().splitlines()
                last_line = lines[-1]
                if "_Aslains_movetree_mods.bat at mods finished" in last_line:
                    break
                if DEBUG: print(f"Aslain läuft noch - {last_line}")
                sleep(.5)
        except:
            LOGGER.error("Error reading log file (file blocked)?. Assuming that aslasin finished with installation")
            print("Error reading log file (file blocked?)")
            print("Aslain probably finished")
            break        

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

def get_config(checker_config_path):
    if not os.path.exists(checker_config_path):
        input("Es liegt noch keine Config-Datei vor. Bitte wähle den World of Tanks root Ordner aus. (fortfahren mit ENTER)")
        import tkinter as tk      
        
        root = tk.Tk()
        root.attributes('-topmost', True)  # Display the dialog in the foreground.
        root.iconify()  # Hide the little window.
        wot_path = tk.askdirectory(title='...', parent=root)
        root.destroy()  # Destroy the root window when folder selected.
        
        config = {"wot_path":wot_path, "local_aslain_version": "", "aslain_installer_version":""}
        with open(checker_config_path, "w") as f:
            f.write(json.dumps(config))
        return (wot_path, "")

    else:
        print("loading config")
        with open(checker_config_path, "r") as f:
            config = json.loads(f.read())
        if "local_aslain_version" not in config:
            config["local_aslain_version"] = ""
        if "aslain_installer_version" not in config:
            config["aslain_installer_version"] = ""
        return (config["wot_path"], config["local_aslain_version"], config["aslain_installer_version"])

def update_config(key, value):
    with open(checker_config_path, "r") as f:
        config = json.loads(f.read())
    config[key] = value
    with open(checker_config_path, "w") as f:
        f.write(json.dumps(config))

def download_aslain(urllist):
    global S
    print("Starte Download")
    url = urllist.pop()
    while True:
        try:
            with S.get(url, stream=True) as rq:
                rq.raise_for_status()
                length_in_byte = int(rq.headers["Content-Length"])
                with tqdm(total=length_in_byte, unit="byte", unit_scale=True) as pbar:
                    with open(aslain_path, "wb") as f:
                        for chunk in rq.iter_content(chunk_size=1024*1024):
                            f.write(chunk)    
                            pbar.update(len(chunk))
            print("Download Fertiggestellt")
            return 
        except ConnectionResetError as con_ret:
            LOGGER.error(con_ret)
            print("Connection Reset Error: "+con_ret)
            sleep(.25)
        except requests.exceptions.ConnectionError as con_ret:
            LOGGER.error(con_ret)
            sleep(.25)
        except ProtocolError as prot_err:
            LOGGER.error(prot_err)
            sleep(.25)
        except Exception as e:
            LOGGER.error(con_ret)
            print(f"Error downloading {url}\nERROR: {e}\nRetrying with next url if possible")
            return download_aslain(urllist)
        
def init_logging():
    formatter = logging.Formatter(
        fmt='%(asctime)s : %(levelname)s: %(filename)s::%(funcName)s:%(lineno)d %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    file_handler = logging.handlers.TimedRotatingFileHandler("script.log", when="m", interval=1, backupCount=5)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger("Aslain")
    #logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    logger.setLevel(logging.DEBUG)
    logger.debug("Logging initialized") 

    return logger

def wait_for_window(window_title, app):
    while True:
        try:
            app.connect(title=window_title)
            return app
        except ElementNotFoundError as ex:
            sleep(.1)

def automate_aslain_install():
    print("Running the aslain installer automated")
    app = Application().start("./aslain_installer.exe")
    app = wait_for_window("Select Installer Language", app)
    app["TSelectLanguageForm"].child_window(title="OK").wait("enabled", timeout=30).click()
    app = wait_for_window("Aslain's WoT Modpack - Welcome Page", app)
    for i in range(6):
        app["TWizardForm"].child_window(title="&Next").wait("enabled", timeout=30).click()
    app["TWizardForm"].child_window(title="&Install").wait("enabled", timeout=30).click()
    app["TWizardForm"].child_window(title="&Finish").wait("enabled", timeout=60).click()
    print("Aslain successfully installed")


update()
LOGGER = init_logging()

#S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0"})
while True:
    try:
        S.get("https://aslain.com")
        break
    except Exception as e:
        LOGGER.info("Could not reach https://aslain.com, retrying...")
        LOGGER.debug(e)
        if DEV: print(e)
        sleep(.25)



appdata_path = os.getenv("LOCALAPPDATA")
folder_path = os.path.join(appdata_path, "Aslain-Checker")
aslain_path = os.path.join(folder_path, "aslain_installer.exe")
checker_config_path = os.path.join(folder_path, "config.json")

WOT_PATH, LOCAL_ASLAIN_VERSION, ASLAIN_INSTALLER_VERSION = get_config(checker_config_path)

CONFIG_PATH = os.path.join(WOT_PATH, "mods\\configs\\spoter\\marksOnGunExtended\\marksOnGunExtended.json")
WOT_VERSION_PATH = os.path.join(WOT_PATH, "game_info.xml")
ASLAIN_LOG_PATH = os.path.join(WOT_PATH, "Aslain_Modpack\\_Aslains_Installer.log")
EXECUTABLE_PATH = os.path.join(WOT_PATH, "WorldOfTanks.exe")


if not os.path.exists(folder_path):
    os.mkdir(folder_path)

resp = S.get("https://aslain.com/index.php?/topic/13-download-%E2%98%85-world-of-tanks-%E2%98%85-modpack/")
soup = bs4.BeautifulSoup(resp.text, "html.parser")

url = None

search_keys = ["ftp.wot.modpack", "wot.flcl.eu/public", "aslain.legionriders.club", "modp.wgcdn.co/media/mod_files", "flcl.uk"]
urls = []

for entry in soup.find_all("a", href=True):
    for subentry in search_keys:
        if subentry in entry["href"] and entry["href"].endswith(".exe"):
            urls.append(entry["href"])

aslain_version_short = re.search(r"\d+\.\d+\.\d", urls[0]).group(0)
aslain_version_full = re.search(r"\d+\.\d+\.\d.+?.exe", urls[0]).group(0)[:-4]


if aslain_version_full != LOCAL_ASLAIN_VERSION :
    print(f"Version {aslain_version_full} verfügbar!")
    if aslain_version_full == ASLAIN_INSTALLER_VERSION and os.path.exists(aslain_path):
        print("Installer already downloaded")
    else:
        download_aslain(urls)
        update_config("aslain_installer_version", aslain_version_full)
    wait_for_patch()
    wait_for_version(aslain_version_short)

    print("Starte den neuen Installer")
    automate_aslain_install()

    update_config("local_aslain_version", aslain_version_full)

    #print("Einstellen von MOE")
    #config_moe()
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
    LOGGER.info("Skript ran successfully. Shutting down...")




