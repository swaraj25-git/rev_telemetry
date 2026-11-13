
from dataclasses import dataclass
import math


# -----------------------------------------
# 1. SIMULATION CONFIGURATION
# -----------------------------------------

@dataclass
class SimulationConfig:
    # Translational acceleration (m/s^2)
    linear_acceleration: float = 1.5

    # Angular acceleration (degrees/s^2)
    angular_acceleration: float = 60.0

    # Water resistance coefficients
    linear_drag: float = 0.8
    angular_drag: float = 1.5

    # Thruster response time (seconds)
    thruster_response_time: float = 0.3

    # Battery configuration
    initial_battery_voltage: float = 16.8
    minimum_battery_voltage: float = 12.0

    # Approximate battery discharge rate
    battery_drain_rate: float = 0.0005


# -----------------------------------------
# 2. ROBOT COMMANDS
# -----------------------------------------

@dataclass
class ROVCommand:

    # Translational commands: -1 to +1
    surge: float = 0.0
    sway: float = 0.0
    heave: float = 0.0

    # Rotational commands: -1 to +1
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    def clamp(self):

        # Prevent commands outside valid range
        for axis in (
            "surge",
            "sway",
            "heave",
            "roll",
            "pitch",
            "yaw"
        ):
            value = getattr(self, axis)
            setattr(self, axis, max(-1.0, min(1.0, value)))


# -----------------------------------------
# 3. ROBOT STATE
# -----------------------------------------

@dataclass
class ROVState:

    # World position
    x: float = 0.0
    y: float = 0.0
    depth: float = 0.0

    # Translational velocity
    surge_velocity: float = 0.0
    sway_velocity: float = 0.0
    heave_velocity: float = 0.0

    # Orientation in degrees
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    # Angular velocities in degrees/second
    roll_rate: float = 0.0
    pitch_rate: float = 0.0
    yaw_rate: float = 0.0

    # Battery voltage
    battery_voltage: float = 16.8


# -----------------------------------------
# 4. ROV SIMULATION ENGINE
# -----------------------------------------

class ROVSimulator:

    def __init__(self, config=None):

        self.config = config or SimulationConfig()

        self.state = ROVState(
            battery_voltage=self.config.initial_battery_voltage
        )

        self.command = ROVCommand()

        # Actual thruster outputs after response delay
        self.actual_command = ROVCommand()

    # -------------------------------------
    # Set movement commands
    # -------------------------------------

    def set_command(self, command):

        command.clamp()
        self.command = command

    def stop(self):

        self.command = ROVCommand()

    # -------------------------------------
    # Thruster response calculation
    # -------------------------------------

    def update_thrusters(self, dt):

        response_time = self.config.thruster_response_time

        if response_time <= 0:
            factor = 1.0
        else:
            factor = min(1.0, dt / response_time)

        for axis in (
            "surge",
            "sway",
            "heave",
            "roll",
            "pitch",
            "yaw"
        ):

            target = getattr(self.command, axis)
            actual = getattr(self.actual_command, axis)

            updated = actual + (target - actual) * factor

            setattr(self.actual_command, axis, updated)

    # -------------------------------------
    # Translational movement
    # -------------------------------------

    def update_translation(self, dt):

        state = self.state
        config = self.config
        command = self.actual_command

        # Calculate acceleration
        surge_acceleration = (
            config.linear_acceleration * command.surge
            - config.linear_drag * state.surge_velocity
        )

        sway_acceleration = (
            config.linear_acceleration * command.sway
            - config.linear_drag * state.sway_velocity
        )

        heave_acceleration = (
            config.linear_acceleration * command.heave
            - config.linear_drag * state.heave_velocity
        )

        # Update body-frame velocities
        state.surge_velocity += surge_acceleration * dt
        state.sway_velocity += sway_acceleration * dt
        state.heave_velocity += heave_acceleration * dt

        # Convert body-frame velocity to world coordinates
        yaw_radians = math.radians(state.yaw)

        world_x_velocity = (
            state.surge_velocity * math.cos(yaw_radians)
            - state.sway_velocity * math.sin(yaw_radians)
        )

        world_y_velocity = (
            state.surge_velocity * math.sin(yaw_radians)
            + state.sway_velocity * math.cos(yaw_radians)
        )

        # Update position
        state.x += world_x_velocity * dt
        state.y += world_y_velocity * dt

        # Positive heave means downward movement
        state.depth += state.heave_velocity * dt

        # Prevent negative depth
        if state.depth < 0:
            state.depth = 0.0

            if state.heave_velocity < 0:
                state.heave_velocity = 0.0

    # -------------------------------------
    # Rotational movement
    # -------------------------------------

    def update_rotation(self, dt):

        state = self.state
        config = self.config
        command = self.actual_command

        # Calculate angular acceleration
        roll_acceleration = (
            config.angular_acceleration * command.roll
            - config.angular_drag * state.roll_rate
        )

        pitch_acceleration = (
            config.angular_acceleration * command.pitch
            - config.angular_drag * state.pitch_rate
        )

        yaw_acceleration = (
            config.angular_acceleration * command.yaw
            - config.angular_drag * state.yaw_rate
        )

        # Update angular velocities
        state.roll_rate += roll_acceleration * dt
        state.pitch_rate += pitch_acceleration * dt
        state.yaw_rate += yaw_acceleration * dt

        # Update orientation
        state.roll = (
            state.roll + state.roll_rate * dt + 180
        ) % 360 - 180

        state.pitch = (
            state.pitch + state.pitch_rate * dt + 180
        ) % 360 - 180

        state.yaw = (
            state.yaw + state.yaw_rate * dt
        ) % 360

    # -------------------------------------
    # Battery simulation
    # -------------------------------------

    def update_battery(self, dt):

        config = self.config
        state = self.state
        command = self.actual_command

        total_thrust = (
            abs(command.surge)
            + abs(command.sway)
            + abs(command.heave)
            + abs(command.roll)
            + abs(command.pitch)
            + abs(command.yaw)
        )

        state.battery_voltage -= (
            total_thrust * config.battery_drain_rate * dt
        )

        state.battery_voltage = max(
            config.minimum_battery_voltage,
            state.battery_voltage
        )

    # -------------------------------------
    # Main simulation update
    # -------------------------------------

    def update(self, dt):

        if dt <= 0:
            return

        # Avoid unstable updates after long pauses
        dt = min(dt, 0.1)

        self.update_thrusters(dt)
        self.update_translation(dt)
        self.update_rotation(dt)
        self.update_battery(dt)

        return self.state
