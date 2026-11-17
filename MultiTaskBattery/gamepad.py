"""Gamepad support: gamepad button presses become the experiment's response keys.

Every task reads responses as keystrokes through ``psychopy.event`` (``getKeys`` /
``waitKeys``). Instead of changing each task, a press on a mapped gamepad button is
added to PsychoPy's key buffer as the matching key, e.g. the first entry of
``gamepad_buttons`` arrives as ``response_keys[0]``. All tasks, the TTL clock and the
scoreboard therefore work unchanged, and the keyboard keeps working alongside.

The gamepad is read with SDL2 (``pip install pysdl2 pysdl2-dll``), the library most games
use. It decodes Xbox, PlayStation and Switch(-style) controllers and gives their buttons
the same names on Windows, macOS and Linux.

Enable it in constants.py::

    response_device = 'gamepad'
    gamepad_buttons = ['y', 'x', 'b', 'a']   # gamepad button for response 1, 2, 3, 4
    gamepad_other_buttons = {'start': 't'}   # optional: any other button -> any key
                                             # (here: Start / + simulates the scanner trigger)

Button names: a, b, x, y, back, guide, start, leftstick, rightstick, leftshoulder,
rightshoulder, dpup, dpdown, dpleft, dpright, misc1, paddle1-4, touchpad.
Gamepads SDL does not recognise only have numbers (0, 1, 2, ...); don't mix names and
numbers. To see what each of your buttons is called, run::

    python -m MultiTaskBattery.gamepad
"""
import ctypes
from psychopy import event

try:
    import sdl2
except ImportError:  # optional dependency, only needed when a gamepad is used
    sdl2 = None


def _init_sdl():
    if sdl2 is None:
        raise ImportError("Gamepad support needs SDL2: run  pip install pysdl2 pysdl2-dll")
    # keep reading the gamepad when the experiment window is not the focused window
    sdl2.SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")
    if sdl2.SDL_WasInit(sdl2.SDL_INIT_GAMECONTROLLER) == 0:
        if sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER) != 0:
            raise RuntimeError(f"Could not start SDL: {sdl2.SDL_GetError().decode()}")


def _button_names():
    """{SDL button id: name} for standard (named) controller buttons."""
    return {b: sdl2.SDL_GameControllerGetStringForButton(b).decode()
            for b in range(sdl2.SDL_CONTROLLER_BUTTON_MAX)}


def list_gamepads():
    """Returns [(index, name, has_named_buttons)] for the connected gamepads."""
    _init_sdl()
    return [(i, (sdl2.SDL_JoystickNameForIndex(i) or b'?').decode(),
             bool(sdl2.SDL_IsGameController(i)))
            for i in range(sdl2.SDL_NumJoysticks())]


class Gamepad:
    def __init__(self, button_to_key, window, device_index=0):
        """Opens a gamepad and forwards presses of mapped buttons as key presses.

        Args:
            button_to_key (dict): gamepad button (name or number) -> key name
            window (psychopy.visual.Window): the experiment window (pyglet backend)
            device_index (int): which gamepad to use if several are connected
        """
        self.button_to_key = dict(button_to_key)
        self._polling = False

        names = [b for b in self.button_to_key if isinstance(b, str)]
        numbers = [b for b in self.button_to_key if isinstance(b, int)]
        if names and numbers:
            raise ValueError("Gamepad buttons must be all names (e.g. 'a') or all "
                             f"numbers (e.g. 0), not a mix: {list(self.button_to_key)}")

        pads = list_gamepads()
        if len(pads) <= device_index:
            raise RuntimeError("No gamepad found. Connect it (USB or Bluetooth), then check "
                               "with  python -m MultiTaskBattery.gamepad")
        _, self.name, named = pads[device_index]

        if names:
            if not named:
                raise RuntimeError(f"'{self.name}' has no named buttons; use button numbers "
                                   "in gamepad_buttons (see  python -m MultiTaskBattery.gamepad)")
            unknown = set(names) - set(_button_names().values())
            if unknown:
                raise ValueError(f"Unknown gamepad button name(s) {sorted(unknown)}; valid: "
                                 f"{sorted(_button_names().values())}")
            self._controller = sdl2.SDL_GameControllerOpen(device_index)
            ids = {name: b for b, name in _button_names().items()}
            self._buttons = [(ids[n], n) for n in names]
            self._read = lambda b: sdl2.SDL_GameControllerGetButton(self._controller, b)
            self._update = sdl2.SDL_GameControllerUpdate
        else:
            self._joystick = sdl2.SDL_JoystickOpen(device_index)
            self._buttons = [(n, n) for n in numbers]
            self._read = lambda b: sdl2.SDL_JoystickGetButton(self._joystick, b)
            self._update = sdl2.SDL_JoystickUpdate
        self._down = set()

        # PsychoPy processes window events on every flip and every getKeys/waitKeys call.
        # Hooking in here means the gamepad is read at exactly those moments, in every task.
        handle = window.winHandle
        original_dispatch = handle.dispatch_events

        def dispatch_events():
            self.poll()
            return original_dispatch()

        handle.dispatch_events = dispatch_events
        print(f"Gamepad: using '{self.name}'; "
              + ", ".join(f"{b!r} -> '{k}'" for b, k in self.button_to_key.items()))

    def poll(self):
        """Reads the gamepad; each newly pressed mapped button is added as a key press."""
        if self._polling:  # guard against re-entry
            return
        self._polling = True
        try:
            self._update()
            down = {label for b, label in self._buttons if self._read(b)}
            for label in down - self._down:
                event._onPygletKey(self.button_to_key[label], 0, emulated=True)
            self._down = down
        finally:
            self._polling = False


def from_constants(const, window):
    """Creates a Gamepad from constants.py, or returns None if response_device is not 'gamepad'."""
    if getattr(const, 'response_device', 'keyboard') != 'gamepad':
        return None
    buttons = list(getattr(const, 'gamepad_buttons', []))
    if len(buttons) != len(const.response_keys):
        raise ValueError(f"gamepad_buttons needs one button per response key: got {len(buttons)} "
                         f"buttons for {len(const.response_keys)} response_keys {const.response_keys}")
    button_to_key = dict(zip(buttons, const.response_keys))
    button_to_key.update(getattr(const, 'gamepad_other_buttons', {}) or {})
    return Gamepad(button_to_key, window, getattr(const, 'gamepad_index', 0))


def _button_test():
    """Prints the name (and number) of every gamepad button pressed. Esc on the keyboard quits."""
    import time
    from psychopy import visual

    pads = list_gamepads()
    if not pads:
        print("No gamepad found. Connect it (USB or Bluetooth) and try again.")
        return
    for i, name, named in pads:
        print(f"Gamepad {i}: '{name}' -> use button {'names' if named else 'numbers'}")
    win = visual.Window([700, 250], units='norm', color='#808080')
    visual.TextStim(win, 'Press gamepad buttons.\nEsc (keyboard) to quit.', height=0.15).draw()
    win.flip()

    names = _button_names()
    pad = sdl2.SDL_GameControllerOpen(0) if pads[0][2] else None
    joy = sdl2.SDL_GameControllerGetJoystick(pad) if pad else sdl2.SDL_JoystickOpen(0)
    n_raw = sdl2.SDL_JoystickNumButtons(joy)
    last = set()
    while 'escape' not in event.getKeys():
        sdl2.SDL_GameControllerUpdate() if pad else sdl2.SDL_JoystickUpdate()
        now = {('name', names[b]) for b in names if pad and sdl2.SDL_GameControllerGetButton(pad, b)}
        now |= {('number', i) for i in range(n_raw) if sdl2.SDL_JoystickGetButton(joy, i)}
        new = now - last
        if new:
            named_ = [v for k, v in new if k == 'name']
            nums = [v for k, v in new if k == 'number']
            print("pressed:", f"name {named_[0]!r}  " if named_ else "", f"(number {nums[0]})" if nums else "")
        last = now
        time.sleep(0.002)
    win.close()


if __name__ == '__main__':
    _button_test()
