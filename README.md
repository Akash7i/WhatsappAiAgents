# 🤖 WhatsApp AI Agent - Complete Package

A powerful, feature-rich AI agent for WhatsApp Web that can handle file processing, web services, AI tasks, and much more!

## 🌟 Features

### 📁 **File Processing**
- Remove backgrounds from images using AI
- Convert PDF to images
- Convert CSV files to readable text
- Compress and extract files
- Extract text from documents
- Image enhancement and format conversion

### 🌐 **Web Services**
- Real-time weather information
- Stock price tracking
- URL shortening
- Wikipedia search
- Language translation
- Currency conversion

### 🤖 **AI & Image Processing**
- Generate QR codes
- Create word clouds
- Image enhancement (brightness, contrast, sharpness)
- Text analysis and sentiment detection
- Background removal with AI

### ⚡ **Productivity Tools**
- Set reminders
- Generate secure passwords
- Hash text (MD5, SHA256, etc.)
- Send emails automatically
- Calendar and scheduling

### 💻 **System Utilities**
- System performance monitoring
- Internet speed testing
- Get public IP address
- Memory and CPU usage tracking

### 🎮 **Entertainment**
- Tell jokes
- Share inspirational quotes
- Roll dice and flip coins
- Random number generation

## 📋 Prerequisites

1. **Python 3.8+** installed on your system
2. **Google Chrome** browser installed
3. **ChromeDriver** downloaded and placed in `C:\chromedriver-win64\chromedriver.exe`
4. **OpenAI API Key** (required)
5. **WhatsApp Web** account access

## 🚀 Quick Setup

### Step 1: Clone and Setup
```bash
# Download all files to a folder
# Navigate to the folder in command prompt/terminal

# Install dependencies
python setup.py
```

### Step 2: Configure Environment
1. Copy `.env.template` to `.env`
2. Edit `.env` file with your credentials:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional APIs
WEATHER_API_KEY=your_openweathermap_api_key
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Paths (adjust if needed)
CHROME_DRIVER_PATH=C:/chromedriver-win64/chromedriver.exe
CHROME_PROFILE_PATH=C:/Temp/ChromeProfile
```

### Step 3: Run the Agent
```bash
python start.py
```

## 🔧 Installation Details

### Manual Installation
```bash
# Install required packages
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"

# Create directories
mkdir downloads temp logs backups
```

### Chrome Driver Setup
1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver from [here](https://chromedriver.chromium.org/)
3. Extract to `C:\chromedriver-win64\chromedriver.exe`

## 📖 Usage Guide

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show all available features | `help` |
| `time` | Get current time | `what time is it?` |
| `weather [city]` | Get weather info | `weather in London` |
| `stock [symbol]` | Get stock price | `stock AAPL` |
| `translate [text] to [lang]` | Translate text | `translate hello to spanish` |
| `wiki [topic]` | Search Wikipedia | `wiki artificial intelligence` |

### File Processing Commands

| Command | Description | Example |
|---------|-------------|---------|
| `remove background` | Remove image background | Send image + "remove background" |
| `convert pdf to image` | Convert PDF pages | Send PDF + "convert to images" |
| `csv to text` | Convert CSV to readable format | Send CSV + "convert csv" |
| `compress file` | Compress files to ZIP | Send file + "compress" |

### AI & Creative Commands

| Command | Description | Example |
|---------|-------------|---------|
| `qr code [text]` | Generate QR code | `qr code https://google.com` |
| `word cloud` | Create word cloud | `word cloud artificial intelligence` |
| `analyze [text]` | Text sentiment analysis | `analyze I love this product` |
| `generate password` | Create secure password | `generate password 16` |

### System Commands

| Command | Description | Example |
|---------|-------------|---------|
| `system info` | Get PC performance | `system info` |
| `my ip` | Get public IP | `my ip` |
| `speed test` | Test internet speed | `speed test` |

### Fun Commands

| Command | Description | Example |
|---------|-------------|---------|
| `joke` | Get a random joke | `tell me a joke` |
| `quote` | Get inspiration | `motivational quote` |
| `roll dice` | Roll dice | `roll 2d6` |
| `flip coin` | Flip coin | `flip coin` |

