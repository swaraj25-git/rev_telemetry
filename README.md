# ROV Telemetry Ground Station

A desktop-based ROV (Remotely Operated Vehicle) telemetry and control simulation built with Python and PySide6.

## Project overview

This application provides a simulated ground station for monitoring and controlling an underwater vehicle. It includes a desktop dashboard, simulated movement and orientation, live telemetry, manual keyboard input, automatic depth and heading control, a depth-versus-time graph, and an embedded OpenStreetMap view.

**Important:** This is a software simulation. It is not connected to real ROV hardware, does not provide real GPS or underwater positioning, and is not a certified vehicle safety system.

## Features

- Desktop user interface built with PySide6.
- Simulated forward/backward, sideways, vertical and rotational movement.
- Live roll, pitch, yaw, depth and battery-voltage telemetry.
- Manual keyboard control.
- Depth Hold and Heading Hold proportional controllers.
- Arm and Disarm controls.
- Simulated linear/angular drag and delayed thruster response.
- Live depth-versus-time plot using pyqtgraph.
- Embedded Leaflet map using OpenStreetMap tiles.
- Automated unit tests using pytest.

## Technology stack

- Python 3
- PySide6 / Qt
- PySide6 QtWebEngine
- NumPy (if used by the installed project modules)
- pyqtgraph
- pytest
- Leaflet
- OpenStreetMap

## Project structure

```text
Crotia_Assesment/
├── main.py
├── controllers/
│   ├── __init__.py
│   ├── manual_controller.py
│   └── mode_controller.py
├── simulation/
│   ├── __init__.py
│   └── rov_simulator.py
├── tests/
│   ├── test_simulator.py
│   ├── test_mode_controller.py
│   └── test_safety.py
└── .venv/
```

## Installation on Windows

Open PowerShell in the project directory.

Create a virtual environment if one does not already exist:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
pip install PySide6 PySide6-Addons numpy pyqtgraph pytest
```

Run the application:

```powershell
python main.py
```

Run the automated tests:

```powershell
python -m pytest -v
```

## Controls

The vehicle must be armed before manual keyboard commands are accepted.

| Key | Action |
|---|---|
| W / S | Forward / backward |
| A / D | Left / right |
| Q / E | Up / down |
| Left / Right arrows | Turn left / right |
| I / K | Pitch |
| J / L | Roll |

Release a key to stop requesting movement on that axis. Simulated momentum and drag may cause movement to decay rather than stop instantaneously.

## Operating modes

### Manual

The operator commands movement using the keyboard.

### Depth Hold

The proportional depth controller calculates vertical thrust from the difference between target depth and current simulated depth.

### Heading Hold

The proportional heading controller calculates yaw thrust from the shortest angular difference between target heading and current heading.

The automatic controllers are simplified simulation controllers. Their gains may require tuning to reduce overshoot and oscillation.

## Simulation model

The simulator models:

- Normalized control commands.
- Linear and angular acceleration.
- Linear and angular drag.
- First-order thruster response.
- Position and orientation updates.
- Approximate battery-voltage drain.

Coordinate conventions:

- Positive depth means downward.
- Positive surge means forward at zero heading.
- Positive sway means right at zero heading.
- Heading is represented in degrees.

The simulation is intended for demonstrating control and telemetry behavior, not for predicting the performance of a physical underwater vehicle.

## Safety behavior

- The application starts disarmed.
- When disarmed, the application calls the simulator stop function, which zeros requested and actual simulated thruster commands.
- Manual input is cleared when changing operating modes.
- The manual controller returns a zero command after its one-second input timeout.
- The application clears manual input and stops simulated thrust when it loses window focus or closes.

These are software-simulation safeguards only. They are not a substitute for independent hardware interlocks, emergency-stop circuitry, or a safety-rated control system.

## Map and location display

The application embeds a Leaflet map and requests map tiles from OpenStreetMap's public tile service.

The configured map origin is:

- Latitude: 18.5204
- Longitude: 73.8567
- Reference location: Pune, Maharashtra, India

The marker position is derived from simulated local X/Y displacement converted approximately into latitude/longitude. It is not GPS data and does not represent a real underwater vehicle location.

The map requires an internet connection. OpenStreetMap's public tile service is subject to its tile usage policy. If tiles are blocked or unavailable, review the current policy and use a tile provider whose terms are appropriate for the application.

Map attribution must remain visible: © OpenStreetMap contributors.

## Testing

Run:

```powershell
python -m pytest -v
```

The test suite covers simulator movement, command clamping, battery behavior, automatic controller responses, manual input timeout and simulator stop behavior.

Record the actual test result and date before submitting. Do not report a passing test count unless it is confirmed by the local test run.

## AI-tool disclosure

AI assistance was used during development to help explain the project requirements, generate and revise portions of Python code, troubleshoot errors, and prepare tests and documentation.

All generated code and behavior should be reviewed and tested by the project author before submission.

## Limitations

- No physical ROV or hardware interface is implemented.
- Telemetry is simulated.
- Depth and heading hold use simplified proportional control.
- Map position is a visualization derived from simulated X/Y coordinates.
- Map tiles require internet connectivity and may be unavailable under provider usage restrictions.
- This application is not intended for real vehicle operation.

## License and third-party attribution

OpenStreetMap data © OpenStreetMap contributors. See the [OpenStreetMap Copyright and License](https://www.openstreetmap.org/copyright) page and the [Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/) for applicable attribution and usage terms.

Leaflet is used for map display. See the [Leaflet project](https://leafletjs.com/).
