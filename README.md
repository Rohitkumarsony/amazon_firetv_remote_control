# 📺 Fire TV Remote Control System

A comprehensive voice-controlled and web-based remote control solution for Android TVs using ADB (Android Debug Bridge). Control your TV through an intuitive web interface with touch controls or voice commands.

## 🌟 Features

### 🎮 Remote Control Interface
- **Realistic Remote UI**: Authentic TV remote design with tactile button feedback
- **Complete Control**: Power, navigation (D-pad), volume, channel controls
- **Quick Access**: Direct buttons for Netflix, Prime Video, YouTube, Disney+
- **Action Buttons**: Menu, Home, Back navigation
- **Real-time Feedback**: Live command log with timestamps

### 🎤 Voice Control
- **Natural Language Processing**: Speak commands naturally
- **App Launch**: "Open Netflix", "Launch YouTube", etc.
- **TV Controls**: "Volume up", "Channel down", "Mute"
- **Smart Search**: Fuzzy matching finds apps even with partial names
- **Text Input Fallback**: Type commands if voice isn't available

### 🔌 Device Management
- **Auto-Discovery**: Automatic ADB connection to your TV
- **App Detection**: Scans and catalogs all installed apps
- **Third-Party Apps**: Filters and manages installed applications
- **Background Processing**: Non-blocking app list generation
- **Connection Status**: Real-time connection monitoring

### 📱 Web Interface
- **Responsive Design**: Works on phones, tablets, and desktops
- **WebSocket Communication**: Real-time bidirectional communication
- **Dark Theme**: Easy on the eyes with modern gradient design
- **Touch Optimized**: Perfect for mobile touch controls
- **Cross-Platform**: Works on any device with a web browser

---

## 🏗️ Architecture

```
┌─────────────────┐         WebSocket          ┌──────────────────┐
│  Web Interface  │◄──────────────────────────►│  FastAPI Server  │
│   (HTML/JS)     │                             │   (Python)       │
└─────────────────┘                             └──────────────────┘
                                                          │
                                                          │ ADB Protocol
                                                          ▼
                                                ┌──────────────────┐
                                                │   Android TV     │
                                                │  (via ADB)       │
                                                └──────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **WebSockets**: Real-time bidirectional communication
- **ADB (Android Debug Bridge)**: Android device control
- **SpeechRecognition**: Voice-to-text processing
- **Pydub**: Audio processing
- **orjson**: Fast JSON serialization

### Frontend
- **HTML5/CSS3**: Modern responsive design
- **JavaScript (ES6+)**: WebSocket client implementation
- **Font Awesome**: Icon library
- **Google Fonts**: Inter typography

### Device Communication
- **TCP/IP**: Network communication with TV
- **ADB Protocol**: Android Debug Bridge commands
- **WebSocket Protocol**: Real-time client-server communication

---

## 📋 Prerequisites

### Hardware Requirements
- Android TV (Fire TV, Google TV, Smart TV with Android)
- Computer/Server (Windows, macOS, or Linux)
- Same network connectivity for TV and server

### Software Requirements
- Python 3.8 or higher
- ADB (Android Debug Bridge) installed and configured
- AAPT (Android Asset Packaging Tool) - optional for advanced app detection

### Python Dependencies
```
fastapi
uvicorn[standard]
websockets
orjson
SpeechRecognition
pydub
pandas
```

---

## Quick Start Guide
Step 1: Ensure Same WiFi Network

Connect your computer and TV to the same WiFi network
This is crucial for ADB wireless connection

## Step 2: Find Your TV's IP Address

Go to TV Settings → Network → Network Status
Note the IP address (e.g., 192.168.1.100)
Alternatively, check your router's connected devices list

## Step 3: Enable ADB on TV (One-time setup)

Go to Settings → About
Click "Build Number" 7 times to enable Developer Options
Go to Developer Options
Enable "USB Debugging" and "Network Debugging"


## 🚀 Installation

### 1. Clone the Repository
```bash
git git clone https://github.com/Rohitkumarsony/amazon_firetv_remote_control.git
cd smart-tv-remote
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

The application will auto-install missing packages on first run:
- fastapi
- uvicorn
- websockets
- orjson
- SpeechRecognition
- pydub

### 3. Install ADB
**Windows:**
```bash
# Download Android Platform Tools
# Extract and add to PATH
```

**macOS:**
```bash
brew install android-platform-tools
```

**Linux:**
```bash
sudo apt-get install adb
```

### 4. Configure Your TV
## when connect with same wifi run this command 
```
adb connect ip:port
```

#### Enable Developer Options:
1. Go to TV Settings → About
2. Click "Build Number" 7 times
3. Developer Options will be enabled

#### Enable ADB Debugging:
1. Go to Developer Options
2. Enable "USB Debugging"
3. Enable "Network Debugging" (if available)

#### Find TV IP Address:
1. Settings → Network → Network Status
2. Note down the IP address (e.g., 192.168.1.100)

### 5. Configure Port
Edit `port.py`:
```python
device_port = "5555"  # Default ADB port
```

---

## 🎯 Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://127.0.0.1:8000`

### Connecting to Your TV

**Method 1: API Endpoint**
```bash
curl "http://127.0.0.1:8000/devices/connect?device_ip=192.168.1.100"
```

**Method 2: Web Interface**
First connect via API, then open `index.html` in your browser.

### Using the Remote

1. **Open the Web Interface**: Open `index.html` in any web browser
2. **Wait for Connection**: The remote will automatically connect via WebSocket
3. **Control Your TV**:
   - Click navigation buttons (Up, Down, Left, Right, OK)
   - Use volume and channel controls
   - Press streaming service buttons for quick access
   - Use the microphone button for voice commands

### Voice Commands

Click the microphone button and say:
- **App Launch**: "Open Netflix", "Launch YouTube", "Start Prime Video"
- **Volume**: "Volume up", "Volume down", "Mute"
- **Navigation**: "Go up", "Go down", "Go left", "Go right"
- **Channel**: "Channel up", "Channel down"
- **System**: "Go to home", "Open menu", "Go back"

---

## 📡 API Reference

### Device Connection
```http
GET /devices/connect?device_ip={ip}
```
Connects to the Android TV and initiates app scanning.

**Response:**
```json
{
  "status_code": 200,
  "message": "ADB connection successful"
}
```

### WebSocket - Remote Control
```
WS /ws
```
Send command keys to control the TV.

**Commands:**
- Navigation: `up`, `down`, `left`, `right`, `ok`
- Power: `power`
- Volume: `volume_up`, `volume_down`, `mute`
- Channel: `channel_up`, `channel_down`
- System: `menu`, `home`, `back`
- Apps: `netflix`, `youtube`, `amazon`, `disney`

### WebSocket - Voice Control
```
WS /voice/ws
```
Send voice/text commands.

**Payload:**
```json
{
  "text": "open netflix"
}
```

**Response:**
```json
{
  "text": "open netflix",
  "matches": [...],
  "message": "App opened successfully"
}
```

### Get Third-Party Apps
```http
GET /filter-third-party-apps
```
Returns list of installed third-party applications.

### Open Specific App
```http
GET /open-app/{app_id}
```
Opens an app by package name (e.g., `com.netflix.ninja`).

---

## 📁 Project Structure

```
smart-tv-remote/
│
├── main.py                  # FastAPI server with ADB control
├── index.html               # Web-based remote interface
├── requirements.txt         # Python dependencies
│
├── all_adb_app_list/       # App data directory
│   └── app_labels.csv      # Cached app names and IDs
│
└── README.md               # This file
```

---

## ⚙️ Configuration

### Command Mappings (`command.py`)

Define custom ADB commands:
```python
commands = {
    "power": "adb shell input keyevent KEYCODE_POWER",
    "volume_up": "adb shell input keyevent KEYCODE_VOLUME_UP",
    "netflix": "adb shell am start -n com.netflix.ninja/.MainActivity",
    # Add more commands...
}

voice_commands = {
    "volume up": "adb shell input keyevent KEYCODE_VOLUME_UP",
    "mute": "adb shell input keyevent KEYCODE_MUTE",
    # Add more voice commands...
}
```

### Port Configuration (`port.py`)
```python
device_port = "5555"  # Default ADB wireless port
```

---

## 🔧 Troubleshooting

### Connection Issues

**TV Not Found:**
- Ensure TV and computer are on the same network
- Verify TV IP address is correct
- Check that ADB debugging is enabled on TV

**Connection Timeout:**
```bash
# Reset ADB server
adb kill-server
adb start-server
```

**Unauthorized Device:**
- Accept the authorization prompt on TV screen
- If prompt doesn't appear, disable and re-enable USB debugging

### Voice Command Issues

**Speech Not Recognized:**
- Ensure microphone permissions are granted
- Speak clearly and avoid background noise
- Use text input as fallback

**App Not Opening:**
- Verify app is installed on TV
- Check app package name in CSV file
- Some apps may require specific launch activities

### Performance Issues

**Slow App Scanning:**
- Initial scan takes time (first connection only)
- Subsequent connections use cached data
- Process runs in background, doesn't block usage

**WebSocket Disconnects:**
- Check firewall settings
- Ensure port 8000 is not blocked
- Restart the server if needed

---

## 🎨 Customization

### Styling the Remote

Edit the `<style>` section in `index.html`:
```css
.remote {
    max-width: 320px;  /* Adjust size */
    background: linear-gradient(145deg, #1c1c28, #25253a);  /* Colors */
}
```

### Adding New Buttons

1. **Add HTML button:**
```html
<button class="action-btn" onclick="sendCommand('info')">INFO</button>
```

2. **Add command mapping in `command.py`:**
```python
commands = {
    "info": "adb shell input keyevent KEYCODE_INFO",
}
```

### Custom Voice Commands

Add to `command.py`:
```python
voice_commands = {
    "play pause": "adb shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE",
    "fast forward": "adb shell input keyevent KEYCODE_MEDIA_FAST_FORWARD",
}
```

---

## 🔐 Security Considerations

- **Local Network Only**: Server binds to localhost by default
- **No Authentication**: Implement authentication for production use
- **ADB Security**: Enable ADB only when needed
- **CORS Enabled**: Currently allows all origins (restrict in production)

### Production Recommendations:
```python
# Add authentication
# Restrict CORS origins
# Use HTTPS/WSS
# Implement rate limiting
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **ADB** - Android Debug Bridge by Google
- **Font Awesome** - Icon library
- **SpeechRecognition** - Python speech recognition library

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@example.com

---

## 🗺️ Roadmap

- [ ] Multi-device support
- [ ] TV screen mirroring
- [ ] Gesture controls
- [ ] Macro commands
- [ ] Mobile app (iOS/Android)
- [ ] Smart home integration
- [ ] Voice assistant integration (Alexa, Google Assistant)
- [ ] Schedule commands
- [ ] Remote sharing/collaboration

---

## 📊 Version History

### v1.0.0 (2025-01-XX)
- Initial release
- Basic remote control functionality
- Voice command support
- Web interface
- App launching capability

---