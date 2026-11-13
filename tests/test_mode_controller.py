
from controllers.mode_controller import ModeController
from simulation.rov_simulator import ROVState


def test_depth_hold_moves_down_when_too_shallow():
    controller = ModeController()
    controller.set_target_depth(10.0)

    state = ROVState(depth=5.0)

    command = controller.get_command("Depth Hold", state)

    assert command.heave > 0


def test_depth_hold_moves_up_when_too_deep():
    controller = ModeController()
    controller.set_target_depth(5.0)

    state = ROVState(depth=10.0)

    command = controller.get_command("Depth Hold", state)

    assert command.heave < 0


def test_heading_hold_turns_towards_target():
    controller = ModeController()
    controller.set_target_heading(90.0)

    state = ROVState(yaw=0.0)

    command = controller.get_command("Heading Hold", state)

    assert command.yaw > 0


def test_heading_hold_uses_shortest_direction():
    controller = ModeController()
    controller.set_target_heading(350.0)

    state = ROVState(yaw=10.0)

    command = controller.get_command("Heading Hold", state)

    assert command.yaw < 0


def test_manual_mode_returns_zero_automatic_command():
    controller = ModeController()

    command = controller.get_command(
        "Manual",
        ROVState()
    )

    assert command.is_zero()
