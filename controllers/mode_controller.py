
from dataclasses import dataclass

from simulation.rov_simulator import ROVCommand, ROVState


@dataclass
class HoldConfig:
    depth_kp: float = 0.8
    heading_kp: float = 0.025


class ModeController:
    """
    Provides automatic depth-hold and heading-hold control.

    Manual movement remains the responsibility of ManualController.
    """

    def __init__(self, config=None):
        self.config = config or HoldConfig()

        self.target_depth = 0.0
        self.target_heading = 0.0

    def set_target_depth(self, depth):
        self.target_depth = max(0.0, float(depth))

    def set_target_heading(self, heading):
        self.target_heading = float(heading) % 360.0

    def calculate_depth_hold(self, state: ROVState):
        """Calculate heave command to maintain target depth."""

        error = self.target_depth - state.depth

        # Positive heave means downward movement.
        command = self.config.depth_kp * error

        return max(-1.0, min(1.0, command))

    def calculate_heading_hold(self, state: ROVState):
        """Calculate yaw command to maintain target heading."""

        error = (
            self.target_heading - state.yaw + 180.0
        ) % 360.0 - 180.0

        command = self.config.heading_kp * error

        return max(-1.0, min(1.0, command))

    def get_command(self, mode, state: ROVState):
        """
        Return the automatic control command for the selected mode.

        Modes:
            Manual
            Depth Hold
            Heading Hold
        """

        command = ROVCommand()

        if mode == "Depth Hold":
            command.heave = self.calculate_depth_hold(state)

        elif mode == "Heading Hold":
            command.yaw = self.calculate_heading_hold(state)

        return command.clamp()
