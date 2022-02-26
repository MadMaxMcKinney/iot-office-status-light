import time
import random
import board
import terminalio
import displayio
import neopixel
from digitalio import DigitalInOut, Direction, Pull
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_matrixportal.network import Network

# --- Vars
UPDATE_DELAY = 3
IS_BUSY = True
IS_DIMMED = False
# ---

# --- Display setup ---
matrixportal = MatrixPortal(debug=False)
display = matrixportal.display

# Turn off onboard neopixel
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels[0] = (0, 0, 0)

# Create groups to hold content
contentGroup = displayio.Group()

# --- Content ---
# Background object
background = Rect(0,0,64,32, fill=0x000000)

contentGroup.append(background)

# Create status label (with a default y spacing for the 'connecting' text
font = bitmap_font.load_font("/IBMPlexMono-Medium-24_jep.bdf")
status_label = Label(font,y=14)
# Default text show as connecting, once the internet connection has happened it will resume the code flow and update the text
status_label.text = "..."

contentGroup.append(status_label)
# ---

def update_bg():
    # Pop the background off the bottom of the stack
    background = contentGroup.pop(0)

    # Change the background color of the background
    if IS_BUSY:
        background.fill = 0xFF0000
    else:
        background.fill = 0x00FF00
    # Insert the modified background back at the bottom of the stack
    contentGroup.insert(0, background)

def update_text():
    # Set status text
    status_label.text = "BUSY" if IS_BUSY else "FREE"

    # Set status text position
    # Get the bouding box info from the label component so we can center it. I subtract 1 from the final value to offset it due to the custom font sizing.
    bbx, bby, bbwidth, bbh = status_label.bounding_box
    status_label.x = round((display.width / 2 - bbwidth / 2) - 1)
    status_label.y = display.height // 2

def fetch_updates():
    print("Fetching status...")

    # Returns a JSON object as a python dict object from the selected AdafruitIO feed
    meetingFeed = matrixportal.get_io_feed("meeting-status.inmeeting")
    meetingValue = meetingFeed['last_value']

    isDimmedFeed = matrixportal.get_io_feed("meeting-status.isdimmed")
    isDimmedValue = isDimmedFeed['last_value']

    # Update the value with the converted string
    global IS_BUSY
    IS_BUSY = str_to_bool(meetingValue)

    global IS_DIMMED
    IS_DIMMED = str_to_bool(isDimmedValue)

def update_screen():
    fetch_updates()
    update_bg()
    update_text()

def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError # evil ValueError that doesn't tell you what the wrong value was

# --- Initial display ---
display.show(contentGroup)
update_screen()

# --- Loop ---
while True:

    # Check if dimmed, then hide content
    # Once a bug within Circuitpython has been fixed I can use display.brightness
    # https://github.com/adafruit/circuitpython/issues/3664
    if IS_DIMMED:
        display.brightness = 0
    else:
        display.brightness = 1

    try:
        update_screen()
        time.sleep(UPDATE_DELAY)
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)