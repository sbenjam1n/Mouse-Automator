# Mouse Recorder
  
ฅ^•ﻌ•^ฅ  ฅ^•ﻌ•^ฅ  ฅ^•ﻌ•^ฅ

A powerful and flexible utility for recording and playing back mouse movements, clicks, and keyboard actions to automate repetitive tasks.

## Features

- Record and playback mouse movements with precise timing
- Capture and replay mouse clicks and keyboard inputs
- Store multiple recorded sequences in separate buffers
- Adjust playback speed
- Loop playback functionality
- Save and load recording buffers from files

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mouse-recorder.git
cd mouse-recorder

# Install dependencies
pip install pyautogui pynput
```

## Dependencies

- Python 3.6+
- pyautogui
- pynput

## Usage

Run the script from the command line:

```bash
python mouseRecorder.py
```

### Command-line Options

```
--load FILENAME    Load previously saved buffers from a file
--save FILENAME    Save buffers to a file when exiting
-b, --buffer NUM   Auto-play the specified buffer on launch
```

### Key Controls

| Key      | Action                            |
|----------|-----------------------------------|
| 1-9      | Select buffer                     |
| F8       | Start/stop recording              |
| F9       | Start playback/toggle loop mode   |
| F10      | Stop playback                     |
| +/-      | Increase/decrease playback speed  |

## Examples

### Basic Recording and Playback

1. Run the script: `python mouseRecorder.py`
2. Press `1` to select buffer 1
3. Press `F8` to start recording
4. Perform mouse/keyboard actions
5. Press `F8` again to stop recording
6. Press `F9` to play back the recorded actions

### Save and Load Recordings

```bash
# Record and save buffers
python mouseRecorder.py --save my_recordings.pkl

# Load and use saved buffers
python mouseRecorder.py --load my_recordings.pkl
```

### Auto-Play on Launch

```bash
# Automatically play buffer 2 on launch
python mouseRecorder.py --load my_recordings.pkl -b 2
```

## How It Works

The script uses `pynput` to capture mouse and keyboard events, storing them with precise timing information. During playback, `pyautogui` is used to replicate these actions with the same timing.

