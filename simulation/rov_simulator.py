
from dataclasses import dataclass
import math


@dataclass
class SimulationConfig:
    """Configuration values for the ROV physics simulation."""

    linear_acceleration: float = 1.5
    angular_acceleration: float = 60.0

    linear_drag: float = 0.8
    angular_drag: float = 1.5

    thruster_response_time: float = 0.3

    initial_battery_voltage: float = 16.8
    minimum_battery_voltage: float = 12.0
    battery_drain_rate: float = 0.0005

    # Maximum allowed simulation time step.
    max_dt: float = 0.1


@dataclass
class ROVCommand:
    """
    Normalized ROV control command.

    Every axis must remain between -1.0 and +1.0.
    """

    surge: float = 0.0
    sway: float = 0.0
    heave: float = 0.0

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    def clamp(self):
        """Keep all command axes within their permitted range."""

        for axis in (
            "surge",
            "sway",
            "heave",
            "roll",
            "pitch",
            "yaw",
        ):
            value = getattr(self, axis)
            value = max(-1.0, min(1.0, float(value)))
            setattr(self, axis, value)

        return self

    def is_zero(self):
        """Return True if all command axes are zero."""

        return all(
            getattr(self, axis) == 0.0
            for axis in (
                "surge",
                "sway",
                "heave",
                "roll",
                "pitch",
                "yaw",
            )
        )


@dataclass

@dataclass
class ROVState:
    """Current simulated ROV position, orientation and telemetry."""

    x: float = 0.0
    y: float = 0.0
    depth: float = 0.0

    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_depth: float = 0.0

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    roll_rate: float = 0.0
    pitch_rate: float = 0.0
    yaw_rate: float = 0.0

    battery_voltage: float = 16.8

    @property
    def surge_velocity(self):
        """Forward velocity in the ROV's body frame."""
        yaw_rad = math.radians(self.yaw)

        return (
            self.velocity_x * math.cos(yaw_rad)
            + self.velocity_y * math.sin(yaw_rad)
        )


class ROVSimulator:
    """
    Simulates basic underwater ROV movement and telemetry.

    Coordinate conventions:
        +X: Forward when yaw is zero
        +Y: Sideways to the right when yaw is zero
        +Depth: Downward
        +Yaw: Clockwise heading change

    The simulator uses:
        - First-order thruster response
        - Linear and angular acceleration
        - Linear and angular drag
        - Battery voltage drain
    """

    AXES = (
        "surge",
        "sway",
        "heave",
        "roll",
        "pitch",
        "yaw",
    )

    def __init__(self, config=None):
        self.config = config or SimulationConfig()

        self.command = ROVCommand()
        self.actual_command = ROVCommand()

        self.state = ROVState(
            battery_voltage=self.config.initial_battery_voltage
        )

    def set_command(self, command):
        """
        Set the requested thruster command.

        The supplied command is copied so external modifications
        cannot unexpectedly change the simulator's command.
        """

        if not isinstance(command, ROVCommand):
            raise TypeError("command must be an ROVCommand")

        self.command = ROVCommand(
            surge=command.surge,
            sway=command.sway,
            heave=command.heave,
            roll=command.roll,
            pitch=command.pitch,
            yaw=command.yaw,
        ).clamp()

    def stop(self):
        """
        Immediately set requested and actual thruster commands to zero.

        This is used when the vehicle is disarmed or a safety stop
        is requested. Vehicle momentum may still decay through drag.
        """

        self.command = ROVCommand()
        self.actual_command = ROVCommand()

    def update_thrusters(self, dt):
        """
        Simulate the delayed response of the thrusters.

        Uses a first-order response model:
            output change = (target - output) * dt / response_time
        """

        response_time = max(
            0.001,
            self.config.thruster_response_time
        )

        alpha = min(1.0, dt / response_time)

        for axis in self.AXES:
            target = getattr(self.command, axis)
            actual = getattr(self.actual_command, axis)

            updated = actual + (target - actual) * alpha

            setattr(self.actual_command, axis, updated)

    def update_translation(self, dt):
        """Update position and linear velocity."""

        state = self.state
        command = self.actual_command

        acceleration = self.config.linear_acceleration
        drag = self.config.linear_drag

        # Convert body-frame forward/sideways thrust to world-frame
        # X/Y movement using the current heading.
        yaw_rad = math.radians(state.yaw)

        surge_world_x = (
            command.surge * math.cos(yaw_rad)
            - command.sway * math.sin(yaw_rad)
        )

        surge_world_y = (
            command.surge * math.sin(yaw_rad)
            + command.sway * math.cos(yaw_rad)
        )

        ax = surge_world_x * acceleration - state.velocity_x * drag
        ay = surge_world_y * acceleration - state.velocity_y * drag

        az = command.heave * acceleration - state.velocity_depth * drag

        state.velocity_x += ax * dt
        state.velocity_y += ay * dt
        state.velocity_depth += az * dt

        state.x += state.velocity_x * dt
        state.y += state.velocity_y * dt
        state.depth += state.velocity_depth * dt

        # An underwater ROV cannot move above the water surface.
        if state.depth < 0.0:
            state.depth = 0.0
            state.velocity_depth = max(0.0, state.velocity_depth)

    def update_rotation(self, dt):
        """Update roll, pitch and yaw angles."""

        state = self.state
        command = self.actual_command

        acceleration = self.config.angular_acceleration
        drag = self.config.angular_drag

        roll_acc = command.roll * acceleration - state.roll_rate * drag
        pitch_acc = command.pitch * acceleration - state.pitch_rate * drag
        yaw_acc = command.yaw * acceleration - state.yaw_rate * drag

        state.roll_rate += roll_acc * dt
        state.pitch_rate += pitch_acc * dt
        state.yaw_rate += yaw_acc * dt

        state.roll += state.roll_rate * dt
        state.pitch += state.pitch_rate * dt
        state.yaw += state.yaw_rate * dt

        # Keep roll and pitch within -180 to +180 degrees.
        state.roll = (state.roll + 180.0) % 360.0 - 180.0
        state.pitch = (state.pitch + 180.0) % 360.0 - 180.0

        # Keep heading between 0 and 360 degrees.
        state.yaw %= 360.0

    def update_battery(self, dt):
        """Simulate gradual battery voltage reduction."""

        total_effort = sum(
            abs(getattr(self.actual_command, axis))
            for axis in self.AXES
        )

        drain = (
            total_effort
            * self.config.battery_drain_rate
            * dt
        )

        self.state.battery_voltage = max(
            self.config.minimum_battery_voltage,
            self.state.battery_voltage - drain
        )

    def update(self, dt):
        """
        Advance the simulation by dt seconds.

        Invalid, zero or negative time steps are ignored.
        Large time steps are capped to maintain numerical stability.
        """

        try:
            dt = float(dt)
        except (TypeError, ValueError):
            return self.state

        if not math.isfinite(dt) or dt <= 0.0:
            return self.state

        dt = min(dt, self.config.max_dt)

        self.update_thrusters(dt)
        self.update_translation(dt)
        self.update_rotation(dt)
        self.update_battery(dt)

        return self.state

    def get_state(self):
        """Return the current simulated telemetry state."""
        return self.state

    def get_actual_command(self):
        """Return the current simulated thruster output."""
        return self.actual_command
