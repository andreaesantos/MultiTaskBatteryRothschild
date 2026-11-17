# constants.py defines parameters and settings for an experiment
# it is passed to the Experiment class on initialization
from pathlib import Path
import os
import MultiTaskBattery as mtb

#Necessary definitions for the experiment:
exp_name = 'example_minimal' # name of the experiment

#UNCOMMENT THIS FOR SCANNING
#response_keys    = ['y', 'g', 'r', 'm'] # scanner keys

#COMMENT THIS FOR SCANNING
response_keys    = ['a', 's', 'd', 'f']

# Optional: respond with a gamepad. Each button press arrives as the response key at the
# same position (first button -> response_keys[0], ...); the keyboard keeps working too.
# Needs:  pip install pysdl2 pysdl2-dll
# Find your gamepad's button names with:  python -m MultiTaskBattery.gamepad
response_device = 'gamepad'
gamepad_buttons = ['y', 'x', 'b', 'a']    # button for response 1, 2, 3, 4 (same names on Windows and macOS)
gamepad_other_buttons = {'start': 't'}    # optional: other button -> key ('t' = simulate scanner trigger)

#not used
response_fingers = ['Pinky', 'Ring','Middle', 'Index']

# Directory definitions for experiment
exp_dir = Path(os.path.dirname(os.path.realpath(__file__)))   # where the experiment code is stored
task_dir = exp_dir / "task_files"  # contains target files for the task
run_dir    = exp_dir / "run_files"     # contains run files for each session
data_dir   = exp_dir / "data"          # This is where the result files are being saved

# Use {} so the GUI auto-fills the run number (e.g. run_01.tsv, run_02.tsv, ...)
default_run_filename = 'run_{}.tsv'

# This is were the stimuli for the different task are stored
package_dir = Path(os.path.dirname(os.path.dirname(os.path.realpath(mtb.__file__))))
stim_dir   = package_dir / "stimuli"

# Is the Eye tracker being used?
eye_tracker = False                                     # do you want to do  eyetracking?

# Running in debug mode?
debug = False                                           # set to True for debugging

# Screen settings for subject display
screen = {}
screen['size'] = [1100, 800]        # screen resolution
screen['fullscr'] = False           # full screen, if false it's in a separate window
screen['number'] = 0                # 0 = main display, 1 = secondary display
# required: stimuli are drawn in degrees, so measure these for your setup
screen['width'] = 53                # physical width of the screen image in cm
screen['distance'] = 57             # eye-to-screen distance in cm
