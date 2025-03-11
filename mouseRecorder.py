import time
import pyautogui
import pickle
import argparse
import atexit
from pynput import mouse, keyboard
import sys
from threading import Thread
import signal

# Function to release mouse and keyboard control
def release_control():
    print("Releasing mouse and keyboard control...")
    # Release all mouse buttons
    for button in ["left", "middle", "right"]:
        pyautogui.mouseUp(button=button)
    
    # Release common keys that might be held down
    for key in ["shift", "ctrl", "alt", "cmd"]:
        pyautogui.keyUp(key)
    
    print("Control returned to user")

# Global variables
buffers = {}
current_buffer = None
playback_speed = 1.0
is_recording = False
is_playing = False
loop_playback = False
pyautogui.PAUSE = 0.00001
save_file = None
start_time = 0  # Added for key recording

# Command line configuration
parser = argparse.ArgumentParser(description="Mouse Recorder/Player")
parser.add_argument("--load", help="Load buffers from file")
parser.add_argument("--save", help="Save buffers to file on exit")
parser.add_argument(
    "-b", "--buffer", help="Auto-play specified buffer on launch")
args = parser.parse_args()


def get_valid_keyname(key):
    try:
        if key.char and key.char != "":
            return key.char
    except AttributeError:
        pass
    try:
        name = key.name.lower()
    except AttributeError:
        return None
    modifiers = {
        "shift": ["shift_l", "shift_r"],
        "ctrl": ["ctrl_l", "ctrl_r"],
        "alt": ["alt_l", "alt_r"],
        "cmd": ["cmd_l", "cmd_r", "super"],
        "win": ["super_l", "super_r"],
    }
    for std_name, variants in modifiers.items():
        if name in variants:
            return std_name
    return name


def play_actions(buffer_number):
    global is_playing, loop_playback, playback_speed
    if buffer_number not in buffers or not buffers[buffer_number]:
        print(f"Buffer {buffer_number} is empty.")
        return
    is_playing = True
    actions = buffers[buffer_number]

    try:
        while True:
            start_playback_time = time.time()
            prev_move_timestamp = None
            prev_move_time = None

            for action in actions:
                if not is_playing:
                    break

                current_time = time.time() - start_playback_time
                if action[0] == "move":
                    _, x, y, timestamp = action
                    if prev_move_timestamp is not None:
                        time_diff = (
                            timestamp - prev_move_timestamp) / playback_speed
                        pyautogui.moveTo(x, y, duration=time_diff)
                    else:
                        pyautogui.moveTo(x, y)
                    prev_move_timestamp = timestamp
                elif action[0] == "click":
                    _, button, x, y, action_type, timestamp = action
                    target_time = start_playback_time + \
                        (timestamp / playback_speed)
                    while time.time() < target_time:
                        if not is_playing:
                            break
                        time.sleep(0.001)
                    if is_playing:
                        if action_type == "press":
                            pyautogui.mouseDown(button=button, x=x, y=y)
                        else:
                            pyautogui.mouseUp(button=button, x=x, y=y)
                elif action[0] == "key_press":
                    _, key_name, timestamp = action
                    target_time = start_playback_time + \
                        (timestamp / playback_speed)
                    while time.time() < target_time:
                        if not is_playing:
                            break
                        time.sleep(0.001)
                    if is_playing:
                        pyautogui.keyDown(key_name)
                elif action[0] == "key_release":
                    _, key_name, timestamp = action
                    target_time = start_playback_time + \
                        (timestamp / playback_speed)
                    while time.time() < target_time:
                        if not is_playing:
                            continue
                    time.sleep(0.001)
                    if is_playing:
                        pyautogui.keyUp(key_name)

            if not loop_playback or not is_playing:
                break
    finally:
        is_playing = False
        loop_playback = False
        release_control()  # Release control when playback ends
        print("Playback finished.")


def save_buffers():
    if args.save and buffers:
        with open(args.save, "wb") as f:
            pickle.dump(buffers, f)
        print(f"\nBuffers saved to {args.save}")
    release_control()  # Release control on exit


atexit.register(save_buffers)

# Signal handler for clean exit
def handle_exit(sig=None, frame=None):
    print("\nExiting script...")
    global is_playing, is_recording
    is_playing = False
    is_recording = False
    release_control()
    save_buffers()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Load buffers if specified
if args.load:
    try:
        # Handle filename without extension
        load_file = args.load
        if not load_file.endswith(".pkl") and not load_file.endswith(".pickle") and "." not in load_file:
            # Try both with extensions and without
            try_files = [load_file, load_file + ".pkl", load_file + ".pickle"]
        else:
            try_files = [load_file]
            
        loaded = False
        for file_to_try in try_files:
            try:
                with open(file_to_try, "rb") as f:
                    buffers = pickle.load(f)
                print(f"Loaded buffers from {file_to_try}")
                loaded = True
                break
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Error loading {file_to_try}: {str(e)}")
                
        if not loaded:
            print(f"Could not load buffers from {args.load}")
    except Exception as e:
        print(f"Error loading buffers: {str(e)}")


def auto_play_buffer():
    if args.buffer:
        # Convert buffer name to string to ensure matching
        buffer_key = args.buffer
        # Check if the buffer exists
        if buffer_key in buffers:
            print(f"Auto-playing buffer {buffer_key}")
            play_actions(buffer_key)
            sys.exit(0)
        else:
            # List available buffers to help debugging
            print(f"Available buffers: {list(buffers.keys())}")
            print(f"Buffer '{buffer_key}' not found in loaded data")
            sys.exit(1)


def record_actions(buffer_number):
    global is_recording, buffers
    buffers[buffer_number] = []

    def on_move(x, y):
        if is_recording:
            elapsed = time.time() - start_time
            buffers[buffer_number].append(("move", x, y, elapsed))

    def on_click(x, y, button, pressed):
        if is_recording:
            elapsed = time.time() - start_time
            action_type = "press" if pressed else "release"
            buffers[buffer_number].append(
                ("click", button.name, x, y, action_type, elapsed)
            )

    with mouse.Listener(on_move=on_move, on_click=on_click) as listener:
        listener.join()


def on_press(key):
    global is_recording, is_playing, current_buffer, playback_speed, loop_playback, start_time

    # Handle control keys even during playback
    try:
        if key == keyboard.Key.f10:
            is_playing = False
            loop_playback = False
            release_control()  # Release control when stopping playback
            print("Playback stopped.")
            return
        elif key == keyboard.Key.f9:
            if not is_playing and current_buffer is not None:
                # Start playback in a new thread to avoid blocking
                Thread(target=play_actions, args=(current_buffer,)).start()
            else:
                # If already playing, toggle loop mode
                loop_playback = not loop_playback
                print(f"Looping {'enabled' if loop_playback else 'disabled'}")
            return
        elif hasattr(key, "char"):
            if key.char == "+" and not is_recording and not is_playing:
                new_speed = min(playback_speed + 0.5, 5.0)
                if new_speed != playback_speed:
                    playback_speed = new_speed
                    print(f"Speed: {playback_speed}x")
                return
            elif key.char == "-" and not is_recording and not is_playing:
                new_speed = max(playback_speed - 0.5, 0.5)
                if new_speed != playback_speed:
                    playback_speed = new_speed
                    print(f"Speed: {playback_speed}x")
                return
    except AttributeError:
        pass

    if is_playing:
        return  # Ignore other keys during playback

    try:
        if key == keyboard.Key.f8:
            if is_recording:
                is_recording = False
                print(
                    f"Stopped recording buffer {current_buffer}. {len(buffers[current_buffer])} actions saved."
                )
            else:
                if current_buffer is None:
                    print("Select a buffer with a number key first.")
                    return
                is_recording = True
                start_time = time.time()
                Thread(target=record_actions, args=(current_buffer,)).start()
                print(f"Recording buffer {current_buffer}...")
            return

        if is_recording:
            elapsed = time.time() - start_time
            key_name = get_valid_keyname(key)
            if not key_name:
                return
            buffers[current_buffer].append(("key_press", key_name, elapsed))

        if hasattr(key, "char"):
            if key.char.isdigit() and not is_recording:
                current_buffer = key.char
                print(f"Buffer {current_buffer} selected")
    except AttributeError:
        pass


def on_release(key):
    global is_recording, start_time
    if is_playing or not is_recording:
        return
    if key == keyboard.Key.f8:
        return
    elapsed = time.time() - start_time
    key_name = get_valid_keyname(key)
    if not key_name:
        return
    buffers[current_buffer].append(("key_release", key_name, elapsed))


# Main execution
if args.buffer:
    auto_play_buffer()
else:
    print("Controls:")
    print("1-9: Select buffer | F8: Record | F9: Play/loop | F10: Stop")
    print("+/-: Adjust speed (0.5x to 5x)")
    if args.save:
        print(f"Buffers will be saved to {args.save} on exit")
    print("Press Ctrl+C to exit")
    
    # Start keyboard listener with suppress=False to allow Ctrl+C
    listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=False)
    listener.start()
    
    try:
        # Keep the main thread alive while allowing Ctrl+C to work
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        handle_exit()
