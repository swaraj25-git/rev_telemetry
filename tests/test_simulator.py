
from simulation.rov_simulator import (
    ROVSimulator,
    ROVCommand
)


def test_forward_movement():

    rov = ROVSimulator()

    rov.set_command(ROVCommand(surge=1.0))

    for _ in range(100):
        rov.update(0.05)

    assert rov.state.x > 0
    assert rov.state.surge_velocity > 0


def test_drag_slows_robot():

    rov = ROVSimulator()

    rov.set_command(ROVCommand(surge=1.0))

    for _ in range(100):
        rov.update(0.05)

    velocity_before = rov.state.surge_velocity

    rov.stop()

    for _ in range(100):
        rov.update(0.05)

    velocity_after = rov.state.surge_velocity

    assert velocity_after < velocity_before


def test_depth_increases_when_moving_down():

    rov = ROVSimulator()

    rov.set_command(ROVCommand(heave=1.0))

    for _ in range(100):
        rov.update(0.05)

    assert rov.state.depth > 0


def test_yaw_changes_when_turning():

    rov = ROVSimulator()

    rov.set_command(ROVCommand(yaw=1.0))

    for _ in range(100):
        rov.update(0.05)

    assert rov.state.yaw > 0


def test_command_is_limited():

    command = ROVCommand(surge=5.0, sway=-5.0)

    command.clamp()

    assert command.surge == 1.0
    assert command.sway == -1.0


def test_battery_decreases_with_thrust():

    rov = ROVSimulator()

    initial_voltage = rov.state.battery_voltage

    rov.set_command(ROVCommand(surge=1.0))

    for _ in range(100):
        rov.update(0.05)

    assert rov.state.battery_voltage < initial_voltage
