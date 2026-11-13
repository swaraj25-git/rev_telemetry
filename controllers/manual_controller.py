
import time

from simulation.rov_simulator import ROVCommand


class ManualController:
    """
    Converts keyboard input into normalized ROV commands.

    Controls:
        W / S       Forward / Backward
        D / A       Right / Left
        E / Q       Down / Up
        L / J       Roll right / Roll left
        K / I       Pitch down / Pitch up
        RIGHT / LEFT Turn right / Turn left

    If no operator input is received for INPUT_TIMEOUT seconds,
    all requested manual thrust is set to zero.
    """

    INPUT_TIMEOUT = 1.0

    KEY_MAP = {
        "W": ("surge", 1.0),
        "S": ("surge", -1.0),

        "D": ("sway", 1.0),
        "A": ("sway", -1.0),

        "E": ("heave", 1.0),
        "Q": ("heave", -1.0),

        "L": ("roll", 1.0),
        "J": ("roll", -1.0),

        "K": ("pitch", 1.0),
        "I": ("pitch", -1.0),

        "RIGHT": ("yaw", 1.0),
        "LEFT": ("yaw", -1.0),
    }

    def __init__(self):
        self.pressed_keys = set()
        self.last_input_time = time.monotonic()

    def key_pressed(self, key):
        """Register a key press."""
        key = str(key).upper()

        if key not in self.KEY_MAP:
            return

        self.pressed_keys.add(key)
        self.last_input_time = time.monotonic()

    def key_released(self, key):
        """Register a key release."""
        key = str(key).upper()

        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

        # Refresh the watchdog timestamp when an operator releases
        # a recognized control key.
        self.last_input_time = time.monotonic()

    def clear(self):
        """Clear all pressed keys and reset the input watchdog."""
        self.pressed_keys.clear()
        self.last_input_time = time.monotonic()

    def get_command(self):
        """
        Return the current manual command.

        If the operator has provided no input for more than one
        second, return a zero command.
        """
        elapsed = time.monotonic() - self.last_input_time

        if elapsed > self.INPUT_TIMEOUT:
            self.pressed_keys.clear()
            return ROVCommand()

        command = ROVCommand()

        for key in self.pressed_keys:
            if key not in self.KEY_MAP:
                continue

            axis, value = self.KEY_MAP[key]
            current_value = getattr(command, axis)

            # Allows opposite keys to cancel each other.
            setattr(command, axis, current_value + value)

        command.clamp()
        return command
