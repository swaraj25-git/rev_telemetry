import pytest

from controllers.manual_controller import ManualController
from controllers.mode_controller import ModeController
from simulation.rov_simulator import ROVCommand, ROVSimulator, ROVState


def test_disarm_stop_zeros_requested_and_actual_thrusters():
    simulator = ROVSimulator()

    simulator.set_command(
        ROVCommand(surge=1.0, heave=0.5, yaw=-0.75)
    )
    simulator.actual_command = ROVCommand(
        surge=0.8, heave=0.4, yaw=-0.6
    )

    simulator.stop()

    assert simulator.command.is_zero()
    assert simulator.get_actual_command().is_zero()


def test_manual_controller_returns_zero_after_one_second_without_input(
    monkeypatch,
):
    fake_time = {"now": 100.0}
    monkeypatch.setattr(
        "controllers.manual_controller.time.monotonic",
        lambda: fake_time["now"],
    )

    controller = ManualController()
    controller.key_pressed("W")

    assert controller.get_command().surge == 1.0

    # More than INPUT_TIMEOUT has elapsed without another key event.
    fake_time["now"] += controller.INPUT_TIMEOUT + 0.01

    assert controller.get_command().is_zero()


def test_manual_controller_release_stops_requested_motion():
    controller = ManualController()

    controller.key_pressed("W")
    assert controller.get_command().surge == 1.0

    controller.key_released("W")
    assert controller.get_command().is_zero()


def test_mode_controller_never_exceeds_normalized_command_limits():
    controller = ModeController()
    controller.set_target_depth(100.0)
    controller.set_target_heading(270.0)

    depth_command = controller.get_command(
        "Depth Hold", ROVState(depth=0.0)
    )
    heading_command = controller.get_command(
        "Heading Hold", ROVState(yaw=0.0)
    )

    for command in (depth_command, heading_command):
        for axis in (
            "surge", "sway", "heave", "roll", "pitch", "yaw"
        ):
            value = getattr(command, axis)
            assert -1.0 <= value <= 1.0


def test_unknown_mode_returns_zero_automatic_command():
    controller = ModeController()

    command = controller.get_command("Unknown Mode", ROVState())

    assert command.is_zero()
