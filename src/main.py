import subprocess
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
import asyncio
import re
import orjson
from fastapi.responses import JSONResponse
import socket
import aiohttp
import xml.etree.ElementTree as ET
import os
import io
import speech_recognition as sr
from pydub import AudioSegment
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
import csv


adb_connected = False
app = FastAPI()


directory_name = "all_firetv_app_list"
# Ensure the directory exists, create it if not
if not os.path.exists(directory_name):
    os.mkdir(directory_name)
    print(f"Directory '{directory_name}' created.")
else:
    print(f"Directory '{directory_name}' already exists.")

# Define the working directory and file path
WORKING_DIR = os.path.abspath(directory_name)  # Use absolute path for clarity
CSV_FILE_PATH = os.path.join(WORKING_DIR, "app_labels.csv")



MSEARCH_PAYLOAD = (
    "M-SEARCH * HTTP/1.1\r\n"
    "HOST: 239.255.255.250:1900\r\n"
    "MAN: \"ssdp:discover\"\r\n"
    "MX: 3\r\n"
    "ST: urn:dial-multiscreen-org:service:dial:1\r\n\r\n"
)

async def send_ssdp_discovery():
    """Send SSDP M-SEARCH requests and collect responses."""
    devices = []
    message = MSEARCH_PAYLOAD.encode("utf-8")
    multicast_group = ("239.255.255.250", 1900)

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(5)
    sock.sendto(message, multicast_group)

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            ip = addr[0]
            response = data.decode("utf-8", errors="ignore")
            # Parse the LOCATION field
            location = None
            for line in response.split("\r\n"):
                if line.startswith("LOCATION:"):
                    location = line.split("LOCATION:")[1].strip()
            if location:
                devices.append({"ip": ip, "location": location})
    except socket.timeout:
        pass  # Timeout indicates no more responses
    finally:
        sock.close()

    return devices

async def fetch_device_details(location_url):
    """Fetch and parse XML from the device location."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(location_url) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    # Parse XML
                    root = ET.fromstring(xml_content)
                    ns = {"ns": "urn:schemas-upnp-org:device-1-0"}  # Namespace
                    device = root.find("ns:device", ns)
                    if device is not None:
                        friendly_name = device.find("ns:friendlyName", ns)
                        return friendly_name.text if friendly_name is not None else None
        except Exception as e:
            return None
    return None

@app.get("/devices/list")
async def discover_devices():
    """Discover devices and return their IP and friendly name."""
    ssdp_responses = await send_ssdp_discovery()
    devices = []
    for response in ssdp_responses:
        ip = response["ip"]
        location = response["location"]
        friendly_name = await fetch_device_details(location)
        devices.append({
            "ip": ip + ":5555",
            "friendlyName": friendly_name
        })

    # Filter out devices with no friendly name
    filtered_devices = [device for device in devices if device["friendlyName"]]

    return JSONResponse(content={"devices": filtered_devices})


# ADB commands mapping
commands = {
    "awake": "adb shell input keyevent KEYCODE_WAKEUP",
    "sleep": "adb shell input keyevent KEYCODE_SLEEP",
    "exit": "adb shell input keyevent 3",
    "home": "adb shell input keyevent 3",
    "back": "adb shell input keyevent 4",
    "menu": "adb shell am start -a android.settings.SETTINGS",
    "volume_up": "adb shell input keyevent 24",
    "volume_down": "adb shell input keyevent 25",
    "mute": "adb shell input keyevent 164",
    "left": "adb shell input keyevent 21",
    "right": "adb shell input keyevent 22",
    "up": "adb shell input keyevent 19",
    "down": "adb shell input keyevent 20",
    "ok": "adb shell input keyevent 23",
    "increment": "adb shell input keyevent KEYCODE_CHANNEL_UP",
    "decrement": "adb shell input keyevent KEYCODE_CHANNEL_DOWN",
    "amazon": "adb shell am start com.amazon.firebat/com.amazon.firebatcore.deeplink.DeepLinkRoutingActivity",
    "netflix": "adb shell am start -n com.netflix.ninja/.MainActivity",
    "youtube": "adb shell am start -n com.amazon.firetv.youtube/dev.cobalt.app.MainActivity",
    "hotstar": "adb shell am start -n in.startv.hotstar/com.hotstar.MainActivity",
    "0": "adb shell input keyevent KEYCODE_0",
    "1": "adb shell input keyevent KEYCODE_1",
    "2": "adb shell input keyevent KEYCODE_2",
    "3": "adb shell input keyevent KEYCODE_3",
    "4": "adb shell input keyevent KEYCODE_4",
    "5": "adb shell input keyevent KEYCODE_5",
    "6": "adb shell input keyevent KEYCODE_6",
    "7": "adb shell input keyevent KEYCODE_7",
    "8": "adb shell input keyevent KEYCODE_8",
    "9": "adb shell input keyevent KEYCODE_9",
    "11":"adb shell input keyevent KEYCODE_DEL",
    "12":"adb shell input keyevent 67"
}


def run_command(command: str):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return {"status_code": 200, "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"status_code": e.returncode, "error_message": e.stderr.strip() or "Unknown error occurred"}


# def connect_adb(device_ip: str):
#     """
#     Connects to a device via ADB using the provided IP address with retries and polling.
#     """
#     global adb_connected
#     try:
#         devices_result = run_command("adb devices")
#         if f"{device_ip}\tdevice" in devices_result["output"]:
#             adb_connected = True
#             return {"status_code": 200, "message": "Already connected."}

#         run_command("adb kill-server")
#         run_command("adb start-server")
#         run_command(f"adb connect {device_ip}")

#         # Poll for connection status
#         for _ in range(10):  # Retry 10 times with 1-second intervals
#             devices_result = run_command("adb devices")
#             if f"{device_ip}\tdevice" in devices_result["output"]:
#                 adb_connected = True
#                 return {"status_code": 200, "message": "adb Connected successfully."}
#             elif f"{device_ip}\tunauthorized" in devices_result["output"]:
#                 return {"status_code": 401, "message": "Unauthorized. Allow access on the device."}
#             import time
#             time.sleep(1)  # Use synchronous sleep here
#         return {"status_code": 402, "message": "Connection timed out."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


# @app.get("/devices/connect")
# async def adb_connect(device_ip: str):
#     return connect_adb(device_ip)



def connect_adb(device_ip: str):
    """
    Connects to a device via ADB using the provided IP address with retries and polling.
    """
    global adb_connected

    try:
        # Check if already connected
        devices_result = run_command("adb devices")
        if f"{device_ip}\tdevice" in devices_result["output"]:
            adb_connected = True
            return {"status_code": 200, "message": "ADB is already connected to the device."}

        # Restart ADB server to ensure proper connection
        run_command("adb kill-server")
        run_command("adb start-server")

        # Attempt to connect to the device
        connect_command = f"adb connect {device_ip}"
        run_command(connect_command)

        # Poll for connection status
        for attempt in range(30):  # Retry for 30 seconds
            devices_result = run_command("adb devices")
            if f"{device_ip}\tdevice" in devices_result["output"]:
                adb_connected = True
                return {"status_code": 200, "message": "ADB connection successful."}
            elif f"{device_ip}\tunauthorized" in devices_result["output"]:
                adb_connected = False
                return {"status_code": 401, "message": "ADB connection unauthorized. Please allow access on the device."}
            else:
                time.sleep(1)  # Wait 1 second before rechecking

        # Timeout after 30 seconds
        adb_connected = False
        return {"status_code": 402, "message": "Connection attempt timed out. Please check your device and network."}

    except Exception as e:
        adb_connected = False
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Function to execute a shell command and return output
def run_command_for_system_Apps(command):
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except Exception as e:
        return None


# Function to get the application label directly using dumpsys
def get_application_labels(app_id):
    command = f"adb shell dumpsys package {app_id} | grep 'ApplicationLabel'"
    output = run_command_for_system_Apps(command)
    if output:
        return output.split(":")[-1].strip()
    return "Unknown"


# Function to process a single app ID
def process_app_ids(app_id):
    app_label = get_application_labels(app_id)
    if app_label != "Unknown":
        return {"app_id": app_id, "app_name": app_label}

    command = f"adb shell pm path {app_id}"
    apk_paths = run_command_for_system_Apps(command)
    if not apk_paths:
        return {"app_id": app_id, "app_name": "Not Found"}

    apk_path = apk_paths.splitlines()[0].split(":")[1]
    apk_file = os.path.join(WORKING_DIR, f"{app_id}.apk")
    pull_command = f"adb pull {apk_path} {apk_file}"
    if not run_command_for_system_Apps(pull_command):
        return {"app_id": app_id, "app_name": "Pull Failed"}

    aapt_command = f"aapt dump badging {apk_file} | grep 'application-label'"
    aapt_output = run_command_for_system_Apps(aapt_command)
    if aapt_output:
        label = aapt_output.split(":")[-1].strip().strip("'")
        return {"app_id": app_id, "app_name": label}

    return {"app_id": app_id, "app_name": "Unknown"}


# Function to fetch the list of installed third-party packages
def fetch_all_installed_packages():
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"ADB error: {result.stderr.strip()}")

        packages = result.stdout.splitlines()
        package_list = [pkg.split(":")[1] for pkg in packages if pkg.startswith("package:")]

        return package_list
    except subprocess.TimeoutExpired:
        raise Exception("ADB command timed out.")
    except Exception as e:
        raise Exception(str(e))


# Background task for fetching installed apps
async def fetch_and_store_apps():
    package_list = fetch_all_installed_packages()
    existing_apps = {}
    if os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_apps = {row["app_id"]: row["app_name"] for row in reader}

    new_app_ids = [app_id for app_id in package_list if app_id not in existing_apps]

    if new_app_ids:
        os.makedirs(WORKING_DIR, exist_ok=True)
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            new_results = await loop.run_in_executor(executor, lambda: list(map(process_app_ids, new_app_ids)))

        with open(CSV_FILE_PATH, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["app_id", "app_name"])
            if not existing_apps:
                writer.writeheader()
            writer.writerows(new_results)

        for result in new_results:
            existing_apps[result["app_id"]] = result["app_name"]


# API Endpoint for device connection
@app.get("/devices/connects")
async def adb_connects(device_ip: str):
    """
    API endpoint to connect to a device via ADB and fetch installed apps in the background.
    """
    global adb_connected
    try:
        # Attempt to connect to the device
        connection_response = connect_adb(device_ip)
        if os.path.exists(CSV_FILE_PATH):
            with open(CSV_FILE_PATH, "r") as csvfile:
                reader = csv.reader(csvfile)
                # Skip header and check if there's at least one row of data
                if any(row for index, row in enumerate(reader) if index > 0):
                    return JSONResponse(
                        status_code=200,
                        content={"status_code": 200, "message": "ADB connection successful"}
                    )

        # If connection is successful, start the background task
        if connection_response["status_code"] == 200:
            asyncio.create_task(fetch_and_store_apps())

        # Return the connection response
        return JSONResponse(
            status_code=connection_response["status_code"],
            content=connection_response
        )
    except HTTPException as e:
        adb_connected = False
        raise e




def run_adb_command(command: str):
    if not adb_connected:
        raise HTTPException(status_code=500, detail="ADB not connected. Connect first.")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return {"status_code": 200}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail={"status_code": e.returncode, "error_message": e.stderr.strip()})


async def send_number(number: str):
    if number not in commands:
        raise HTTPException(status_code=400, detail="Invalid number.")
    command = commands[number]
    return run_adb_command(command)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global adb_connected
    await websocket.accept()
    if not adb_connected:
        await websocket.send_text(orjson.dumps({"error": "ADB not connected. Connect first using /adb/connect."}).decode())
        return

    try:
        await websocket.send_text("ADB WebSocket connection established. Send a command to execute.")
        while True:
            try:
                raw_command_key = await websocket.receive_text()
                command_key = re.sub(r"(?:keypad:)?", "", raw_command_key.strip())
                print('rohit',command_key)
                if command_key in commands:
                    response = await asyncio.to_thread(run_adb_command, commands[command_key])
                else:
                    response = {"status_code": 400, "error_message": "Invalid command."}
                await websocket.send_text(orjson.dumps(response).decode())
            except WebSocketDisconnect:
                print("WebSocket disconnected.")
                break
            except Exception as e:
                await websocket.send_text(orjson.dumps({"error": str(e)}).decode())
    except Exception as e:
        await websocket.send_text(orjson.dumps({"error": f"WebSocket error: {str(e)}"}).decode())



def fetch_third_party_packages():
    """
    Fetch the list of third-party app IDs using adb.
    """
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", "-3"],  # Third-party apps
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"ADB error: {result.stderr.strip()}")

        # Parse the output to extract package names
        packages = result.stdout.splitlines()
        package_list = [pkg.split(":")[1] for pkg in packages if pkg.startswith("package:")]

        return package_list
    except subprocess.TimeoutExpired:
        raise Exception("ADB command timed out.")
    except Exception as e:
        raise Exception(str(e))


@app.get("/filter-third-party-apps")
async def filter_third_party_apps():
    """
    Filter third-party apps based on app_id from CSV.
    """
    try:
        # Step 1: Fetch third-party app IDs from adb
        third_party_app_ids = fetch_third_party_packages()

        # Step 2: Load system app data from the CSV file
        if not os.path.exists(CSV_FILE_PATH):
            raise Exception(f'''Fetching installed apps from the device. This may take some time as it is only required during the first connection. Please keep the app open and avoid shutting down your system until the process completes...''')


        with open(CSV_FILE_PATH, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            csv_data = {row["app_id"]: row["app_name"] for row in reader}

        # Step 3: Filter apps in CSV that match third-party app IDs
        filtered_apps = [
            {"app_id": app_id, "app_name": csv_data[app_id]}
            for app_id in third_party_app_ids
            if app_id in csv_data
        ]

        # Step 4: Return the filtered apps
        return {
            "status": 200,
            "message": "Filtered third-party apps successfully.",
            "filtered_count": len(filtered_apps),
            "apps": filtered_apps
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def open_app(app_id):
    """
    Open the app on the Android device using ADB command.
    If 'monkey' fails, try opening the app explicitly using the main activity.
    """
    try:
        # First try using monkey
        result = subprocess.run(
            ["adb", "shell", "monkey", "-p", app_id, "-c", "android.intent.category.LAUNCHER", "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,  # Timeout for opening the app
            text=True
        )

        if result.returncode != 0:
            # If monkey fails, try opening the main activity explicitly
            print(f"Monkey failed for {app_id}. Trying explicit launch...")
            if app_id == "com.sonyliv":
                # SonyLiv explicit launch command
                activity = "com.sonyliv/.ui.splash.SplashActivity"
            else:
                # Handle other apps with the main activity if necessary
                activity = f"{app_id}/.MainActivity"  # Adjust this as needed
            result = subprocess.run(
                ["adb", "shell", "am", "start", "-n", activity],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )

        if result.returncode != 0:
            raise Exception(f"Failed to launch app {app_id}: {result.stderr.strip()}")

        return f"App {app_id} opened successfully."
    except subprocess.TimeoutExpired:
        raise Exception("ADB command timed out.")
    except Exception as e:
        raise Exception(str(e))


@app.get("/open-app/{app_id}")
async def open_app_endpoint(app_id: str):
    """
    Endpoint to open an app on the connected Android device based on the app_id (package name).
    """
    try:
        # Step 2: Open the app
        launch_status = open_app(app_id)

        return {
            "status": 200,
            "connection":"app open successfully",
            "message": launch_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



commands = {
    "power on": "adb shell input keyevent KEYCODE_WAKEUP",
    "power off": "adb shell input keyevent KEYCODE_SLEEP",
    "home": "adb shell input keyevent 3",
    "exit": "adb shell input keyevent 3",
    "back": "adb shell input keyevent 4",
    "menu": "adb shell am start -a android.settings.SETTINGS",
    "volume up": "adb shell input keyevent 24",
    "volume down": "adb shell input keyevent 25",
    "mute": "adb shell input keyevent 164",
    "unmute": "adb shell input keyevent 24",
    "left": "adb shell input keyevent 21",
    "right": "adb shell input keyevent 22",
    "up": "adb shell input keyevent 19",
    "down": "adb shell input keyevent 20",
    "ok": "adb shell input keyevent 23",
    "okay": "adb shell input keyevent 23",
    "channel up": "adb shell input keyevent KEYCODE_CHANNEL_UP",
    "channel down": "adb shell input keyevent KEYCODE_CHANNEL_DOWN",
    "amazon": "adb shell am start com.amazon.firebat/com.amazon.firebatcore.deeplink.DeepLinkRoutingActivity",
    "netflix": "adb shell am start -n com.netflix.ninja/.MainActivity",
    "youtube": "adb shell am start -n com.amazon.firetv.youtube/dev.cobalt.app.MainActivity",
    "hotstar": "adb shell am start -n in.startv.hotstar/com.hotstar.MainActivity",
}



# Load app data from CSV file
def load_app_data(csv_file="all_firetv_app_list/app_labels.csv"):
    app_data = []
    try:
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                app_data.append({
                    "app_id": row["app_id"],
                    "app_name": row["app_name"]
                })
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return app_data

# In-memory store for app data
app_data = load_app_data()

# Extract meaningful keywords from the query
def extract_keywords(query):
    filler_phrases = [
        "please", "plz", "the", "app", "program", "application", "run", "start", "launch", "move", "go", "come",
        "increase", "decrease", 'volume', "open", "open the", "open this", "open up", "open now", "open it", 
        "open it up", "open my app", "open the app", "open the application", "open this app", "open my program", 
        "open that app", "please open", "please open the", "please open this app", "can you open", "can you open the", 
        "could you open", "let me open", "let me open the", "show me", "open up the", "i want to open", "i want", 
        "open my application", "launch", "launch the", "launch the app", "launch this", "launch this app", "please launch", 
        "please launch the", "could you launch", "could you launch please", "launch my app", "let me launch", "let me launch the","i want to open","i want to lunch",
        "start launching", "please launch the app", "launch my application", "could you please launch", "start", "start the", 
        "start this", "start this app", "start the app", "please start", "please start the", "please start the app", "start opening", 
        "start the program", "can I start", "i want to start", "start my application", "run", "run the", "run this", "run this app", 
        "run the app", "please run", "please run the", "let me run", "let me run the", "can you run", "can you run the", "run my application", 
        "can i launch", "would you open", "can i open", "start opening", "move", "go", "come", "would you", "can you","hey bro","hey babby","hey buddy","hey dude"
    ]
    
    # Sort the filler phrases by length (longer phrases should be checked first)
    filler_phrases.sort(key=len, reverse=True)
    
    # Initialize a list to store the extracted keywords
    keywords = []
    
    # Lowercase the query and check for filler phrases
    query_lower = query.lower()

    # Check if any filler phrase exists in the query and remove it
    while query_lower:
        matched = False
        for phrase in filler_phrases:
            # If a phrase is found in the query, remove it
            if query_lower.startswith(phrase + " "):
                query_lower = query_lower[len(phrase) + 1:].strip()
                matched = True
                break
            elif query_lower == phrase:
                query_lower = ""
                matched = True
                break
        if not matched:
            # If no filler phrase is found, take the first word and add it as a keyword
            word = query_lower.split(" ", 1)[0]
            keywords.append(word)
            query_lower = query_lower[len(word):].strip()

    return " ".join(keywords)




# Calculate similarity between two strings
def string_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Search for app name based on similarity
def search_app_name(query, app_data, similarity_threshold=0.7):
    search_string = extract_keywords(query)
    results = []

    for app in app_data:
        similarity = string_similarity(search_string.lower(), app["app_name"].lower())
        if similarity >= similarity_threshold:
            results.append({
                "app_id": app["app_id"],
                "app_name": app["app_name"],
                "similarity": round(similarity * 100, 2)
            })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results if results else f"No matches found for '{query}'"

# Recognize speech from audio data
async def recognize_audio(audio_data):
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        with io.BytesIO() as wav_file:
            audio.export(wav_file, format="wav")
            wav_file.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_file) as source:
                audio = recognizer.record(source)
                try:
                    return recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    return "Sorry, I could not understand the audio."
                except sr.RequestError as e:
                    return f"Error with Google Speech API: {e}"
    except Exception as e:
        return f"Error processing the audio: {e}"


def open_apps(app_id):
    """
    Open the app on the Android device using ADB command.
    It first tries using the 'monkey' command, if it fails, it tries using an explicit launch command.
    """
    try:
        # Try using monkey first
        result = subprocess.run(
            ["adb", "shell", "monkey", "-p", app_id, "-c", "android.intent.category.LAUNCHER", "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,  # Timeout for opening the app
            text=True
        )

        if result.returncode != 0:
            print(f"Monkey failed for {app_id}. Trying explicit launch...")

            # For explicitly launched apps, you can add specific conditions or defaults
            activity = None
            
            # Define app-specific explicit activity names if necessary
            if app_id == "com.amazon.firebat":
                activity = "com.amazon.firebat/com.amazon.firebatcore.deeplink.DeepLinkRoutingActivity"
            else:
                # Default to the main activity if not specifically defined
                activity = f"{app_id}/.MainActivity"

            if activity:
                result = subprocess.run(
                    ["adb", "shell", "am", "start", "-n", activity],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    text=True
                )

        if result.returncode != 0:
            raise Exception(f"Failed to launch app {app_id}: {result.stderr.strip()}")

        return f"App {app_id} opened successfully."
    
    except subprocess.TimeoutExpired:
        raise Exception("ADB command timed out.")
    except Exception as e:
        raise Exception(f"Error opening app {app_id}: {str(e)}")


def run_commands(commands):
    try:
        result = subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Command failed with error: {result.stderr.strip()}")
        
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise Exception("ADB command timed out.")
    except Exception as e:
        raise Exception(f"Error running command: {str(e)}")


###for text

@app.websocket("/voice/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive text directly from the client
            data = await websocket.receive_json()  # Assuming the frontend sends a JSON payload
            text = data.get("text", "").strip()

            if not text:
                await websocket.send_json({"error": "No text provided."})
                continue

            # Search for the app based on the received text
            results = search_app_name(text, app_data)
            if isinstance(results, list) and results:
                app_id = results[0]['app_id']
                try:
                    play = open_apps(app_id)
                    response = {
                        "text": text,
                        "matches": results,
                        "message": play
                    }
                except Exception as e:
                    response = {
                        "text": text,
                        "matches": results,
                        "error": str(e)
                    }
            else:
                # Handle cases where no app matches are found
                extracted_command = extract_keywords(text)
                print(extracted_command)
                command_to_run = commands.get(extracted_command, None)

                if command_to_run:
                    try:
                        run_output = run_commands(command_to_run)
                        response = {
                            "text": text,
                            "command": extracted_command,
                            "output": run_output
                        }
                    except Exception as e:
                        response = {
                            "text": text,
                            "command": extracted_command,
                            "error": str(e)
                        }
                else:
                    response = {
                        "text": text,
                        "message": results
                    }

            # Send the response back to the frontend
            await websocket.send_json(response)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Unexpected error: {e}")
        await websocket.send_json({"error": "An unexpected error occurred."})



@app.get('/health-router')
def health():
    return {'status_code':200,'message':"successfull"}