import sys
import time
import math
import bisect

import pyqtgraph as pg

from PySide6.QtCore import Qt, QTimer, QEvent, QUrl
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QAbstractSpinBox,
    QSizePolicy,
    QScrollArea,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from simulation.rov_simulator import ROVSimulator
from controllers.manual_controller import ManualController
from controllers.mode_controller import ModeController


class ROVGroundStation(QMainWindow):

    def __init__(self):
        super().__init__()

        # ---------------------------------
        # 1. INITIALIZE SIMULATION
        # ---------------------------------

        self.is_armed = False

        self.simulator = ROVSimulator()
        self.manual_controller = ManualController()
        self.mode_controller = ModeController()

        self.simulation_time = 0.0
        self.last_update_time = time.monotonic()

        self.time_history = []
        self.depth_history = []

        # How many seconds are visible while the graph follows live data
        self.plot_window_seconds = 30.0

        # How much history is kept so you can scroll/zoom back in time
        self.max_history_seconds = 600.0

        # True  -> axes lock to the live data and follow the line
        # False -> the user is free to pan/zoom; axes stay where they are
        self.follow_live = True

        self.telemetry_labels = {}

        # ---------------------------------
        # 2. MAIN WINDOW
        # ---------------------------------

        self.setWindowTitle("ROV Telemetry Ground Station")

        # Small minimum so the window can always fit on a laptop screen.
        self.setMinimumSize(900, 550)

        # Size the window relative to the usable screen area
        # (excludes the taskbar).
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(
            min(1250, int(screen.width() * 0.95)),
            min(750, int(screen.height() * 0.90)),
        )

        # The dashboard lives inside a scroll area, so if the window is
        # ever smaller than the content, a scroll bar appears instead of
        # content being cut off.
        central_widget = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(central_widget)
        self.setCentralWidget(scroll)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(14)

        # ---------------------------------
        # 3. BUILD DASHBOARD
        # ---------------------------------

        self.create_header()
        self.create_telemetry_section()
        self.create_control_sections()
        self.create_monitoring_section()

        self.apply_styles()

        # ---------------------------------
        # 4. KEYBOARD EVENT FILTER
        # ---------------------------------

        # Listen for keyboard events throughout the application.
        # This prevents keyboard controls from depending only on
        # the main window having direct keyboard focus.

        QApplication.instance().installEventFilter(self)

        # ---------------------------------
        # 5. SIMULATION TIMER
        # ---------------------------------

        self.simulation_timer = QTimer(self)
        self.simulation_timer.timeout.connect(
            self.update_simulation
        )

        # 50 milliseconds = approximately 20 updates per second
        self.simulation_timer.start(50)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # =====================================
    # HEADER
    # =====================================

    def create_header(self):

        header = QHBoxLayout()

        title = QLabel("ROV GROUND STATION")
        title.setObjectName("mainTitle")

        subtitle = QLabel(
            "UNDERWATER VEHICLE MONITORING SYSTEM"
        )
        subtitle.setObjectName("subtitle")

        title_layout = QVBoxLayout()
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        self.connection_label = QLabel("● SIMULATED")
        self.connection_label.setObjectName("connectionStatus")

        self.armed_label = QLabel("DISARMED")
        self.armed_label.setObjectName("disarmedStatus")

        header.addLayout(title_layout)
        header.addStretch()
        header.addWidget(self.connection_label)
        header.addWidget(self.armed_label)

        self.main_layout.addLayout(header)

    # =====================================
    # TELEMETRY
    # =====================================

    def create_telemetry_section(self):

        section_title = QLabel("LIVE TELEMETRY")
        section_title.setObjectName("sectionTitle")

        self.main_layout.addWidget(section_title)

        telemetry_grid = QGridLayout()
        telemetry_grid.setSpacing(12)

        telemetry_data = [
            ("ROLL", "0.0 °"),
            ("PITCH", "0.0 °"),
            ("YAW", "0.0 °"),
            ("DEPTH", "0.00 m"),
            ("BATTERY", "16.80 V"),
        ]

        for index, (name, value) in enumerate(telemetry_data):

            card = QFrame()
            card.setObjectName("telemetryCard")

            card_layout = QVBoxLayout(card)

            name_label = QLabel(name)
            name_label.setObjectName("telemetryName")

            value_label = QLabel(value)
            value_label.setObjectName("telemetryValue")

            card_layout.addWidget(name_label)
            card_layout.addWidget(value_label)

            telemetry_grid.addWidget(card, 0, index)

            self.telemetry_labels[name] = value_label

        self.main_layout.addLayout(telemetry_grid)

        # Additional position information

        self.position_label = QLabel(
            "POSITION: X = 0.00 m | Y = 0.00 m"
        )
        self.position_label.setObjectName("mutedText")

        self.main_layout.addWidget(self.position_label)

    # =====================================
    # CONTROL PANELS
    # =====================================

    def create_control_sections(self):

        # All four control panels sit in ONE row to save vertical space.
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        # ---------------------------------
        # Operating mode
        # ---------------------------------

        mode_card = QFrame()
        mode_card.setObjectName("panel")

        mode_layout = QVBoxLayout(mode_card)

        mode_title = QLabel("OPERATING MODE")
        mode_title.setObjectName("sectionTitle")

        self.mode_selector = QComboBox()
        self.mode_selector.addItems([
            "Manual",
            "Depth Hold",
            "Heading Hold"
        ])
        self.mode_selector.currentTextChanged.connect(
            self.on_mode_changed
        )

        mode_layout.addWidget(mode_title)
        mode_layout.addWidget(self.mode_selector)
        mode_layout.addStretch()

        # ---------------------------------
        # Target settings
        # ---------------------------------

        target_card = QFrame()
        target_card.setObjectName("panel")

        target_layout = QVBoxLayout(target_card)

        target_title = QLabel("TARGET SETTINGS")
        target_title.setObjectName("sectionTitle")

        self.depth_input = QDoubleSpinBox()
        self.depth_input.setRange(0, 100)
        self.depth_input.setSuffix(" m")
        self.depth_input.setValue(12.5)

        self.heading_input = QDoubleSpinBox()
        self.heading_input.setRange(0, 359.9)
        self.heading_input.setSuffix(" °")
        self.heading_input.setValue(90)

        target_layout.addWidget(target_title)

        # Keep labels and spin boxes on separate rows to prevent overlap
        # when Windows scaling or a smaller window compresses the panel.
        target_layout.setSpacing(10)

        depth_row = QHBoxLayout()
        depth_label = QLabel("Target Depth")
        depth_label.setMinimumWidth(110)
        self.depth_input.setFixedHeight(40)
        depth_row.addWidget(depth_label)
        depth_row.addWidget(self.depth_input, 1)

        heading_row = QHBoxLayout()
        heading_label = QLabel("Target Heading")
        heading_label.setMinimumWidth(110)
        self.heading_input.setFixedHeight(40)
        heading_row.addWidget(heading_label)
        heading_row.addWidget(self.heading_input, 1)

        target_layout.addLayout(depth_row)
        target_layout.addLayout(heading_row)

        # ---------------------------------
        # Safety controls
        # ---------------------------------

        safety_card = QFrame()
        safety_card.setObjectName("panel")

        safety_layout = QVBoxLayout(safety_card)

        safety_title = QLabel("VEHICLE SAFETY")
        safety_title.setObjectName("sectionTitle")

        self.arm_button = QPushButton("ARM VEHICLE")
        self.arm_button.setObjectName("armButton")

        self.disarm_button = QPushButton("DISARM VEHICLE")
        self.disarm_button.setObjectName("disarmButton")

        self.arm_button.clicked.connect(self.arm_vehicle)
        self.disarm_button.clicked.connect(self.disarm_vehicle)

        safety_layout.addWidget(safety_title)
        safety_layout.addWidget(self.arm_button)
        safety_layout.addWidget(self.disarm_button)

        # ---------------------------------
        # Keyboard instructions
        # ---------------------------------

        movement_card = QFrame()
        movement_card.setObjectName("panel")

        movement_layout = QVBoxLayout(movement_card)

        movement_title = QLabel("KEYBOARD CONTROLS")
        movement_title.setObjectName("sectionTitle")

        movement_note = QLabel(
            "W / S  - Forward / Backward\n"
            "A / D  - Left / Right\n"
            "Q / E  - Up / Down\n"
            "← / →  - Turn Left / Right\n"
            "I / K  - Pitch\n"
            "J / L  - Roll\n\n"
            "Hold a key to move. Release to slow down."
        )

        movement_note.setObjectName("mutedText")
        movement_note.setWordWrap(True)

        movement_layout.addWidget(movement_title)
        movement_layout.addWidget(movement_note)

        controls_layout.addWidget(mode_card, 1)
        controls_layout.addWidget(target_card, 2)
        controls_layout.addWidget(safety_card, 1)
        controls_layout.addWidget(movement_card, 2)

        self.main_layout.addLayout(controls_layout)

    # =====================================
    # MONITORING
    # =====================================

    def create_monitoring_section(self):

        monitoring_layout = QHBoxLayout()
        monitoring_layout.setSpacing(12)

        # ---------------------------------
        # Depth graph
        # ---------------------------------

        graph_card = QFrame()
        graph_card.setObjectName("panel")

        graph_layout = QVBoxLayout(graph_card)

        graph_title = QLabel("LIVE DEPTH VS TIME")
        graph_title.setObjectName("sectionTitle")

        self.depth_plot = pg.PlotWidget()
        self.depth_plot.setBackground("#172235")

        self.depth_plot.setLabel(
            "left", "Depth", units="m"
        )

        self.depth_plot.setLabel(
            "bottom", "Time", units="s"
        )

        # Stop pyqtgraph from switching to "mm" / "ks" style prefixes.
        self.depth_plot.getAxis("left").enableAutoSIPrefix(False)
        self.depth_plot.getAxis("bottom").enableAutoSIPrefix(False)

        self.depth_plot.showGrid(
            x=True,
            y=True,
            alpha=0.3
        )

        # Positive depth is displayed downward
        self.depth_plot.invertY(True)

        self.depth_curve = self.depth_plot.plot(
            [],
            [],
            pen=pg.mkPen("#00BFFF", width=2)
        )

        # Hide pyqtgraph's built-in "A" auto-range button; the reset
        # button below replaces it.
        self.depth_plot.hideButtons()

        # Any manual pan/zoom with the mouse releases the live-follow lock.
        # (Range changes made from code do not trigger this signal.)
        self.depth_plot.getViewBox().sigRangeChangedManually.connect(
            self.on_plot_manually_changed
        )

        # Header row: title on the left, status + reset button on the right
        graph_header = QHBoxLayout()

        self.graph_status_label = QLabel("● LIVE")
        self.graph_status_label.setStyleSheet(
            "color: #86EFAC; font-size: 11px; font-weight: bold;"
        )

        self.reset_view_button = QPushButton("⟲ RESET VIEW")
        self.reset_view_button.setObjectName("resetViewButton")
        self.reset_view_button.setToolTip(
            "Lock the axes and follow the live line"
        )
        self.reset_view_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_view_button.clicked.connect(self.reset_graph_view)

        graph_header.addWidget(graph_title)
        graph_header.addStretch()
        graph_header.addWidget(self.graph_status_label)
        graph_header.addWidget(self.reset_view_button)

        graph_layout.addLayout(graph_header)
        graph_layout.addWidget(self.depth_plot)

        # ---------------------------------
        # Map
        # ---------------------------------

        map_card = QFrame()
        map_card.setObjectName("panel")

        map_layout = QVBoxLayout(map_card)

        map_title = QLabel("UNDERWATER LOCATION MAP")
        map_title.setObjectName("sectionTitle")

        self.map_status_label = QLabel("Loading map resources...")
        self.map_status_label.setObjectName("mapStatus")
        self.map_status_label.setWordWrap(True)

        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(150)
        self.map_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.map_view.loadFinished.connect(self.on_map_load_finished)

        # Identify this desktop application to the OSM tile service.
        # Add a real project contact URL/email when one is available.
        self.map_view.page().profile().setHttpUserAgent(
            "CrotiaROVGroundStation/1.0"
        )

        # Change these coordinates to the intended simulation location.
        # X/Y simulator positions are treated as local east/north metres.
        self.map_origin_lat = 18.5204
        self.map_origin_lon = 73.8567

        map_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet"
                  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
            </script>
            <style>
                html, body, #map {
                    height: 100%;
                    width: 100%;
                    margin: 0;
                    padding: 0;
                    background: #172235;
                }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <div id="map-message"
                 style="position:absolute;bottom:8px;left:8px;z-index:1000;
                        background:#ffffffdd;color:#26364c;padding:5px 8px;
                        border-radius:4px;font:12px Arial;">
                Loading OpenStreetMap tiles...
            </div>
            <script>
                const map = L.map('map').setView(
                    [__MAP_LAT__, __MAP_LON__],
                    15
                );

                const osmTiles = L.tileLayer(
                    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    {
                        maxZoom: 19,
                        attribution: '&copy; OpenStreetMap contributors'
                    }
                ).addTo(map);

                let tileErrors = 0;
                osmTiles.on('tileerror', function () {
                    tileErrors += 1;
                    const status = document.getElementById('map-message');
                    if (status) {
                        status.textContent =
                            'Map tiles are unavailable or blocked by the tile provider. ' +
                            'Check the network and tile usage policy.';
                    }
                });

                const rovMarker = L.marker(
                    [__MAP_LAT__, __MAP_LON__]
                ).addTo(map);

                rovMarker.bindPopup('Simulated ROV position');

                function updateRovMarker(lat, lon) {
                    rovMarker.setLatLng([lat, lon]);
                }
            </script>
        </body>
        </html>
        """

        # Insert the configured starting coordinates into the map HTML.
        map_html = map_html.replace(
            "__MAP_LAT__", str(self.map_origin_lat)
        ).replace(
            "__MAP_LON__", str(self.map_origin_lon)
        )

        self.map_view.setHtml(
            map_html,
            QUrl("https://unpkg.com/")
        )

        map_layout.addWidget(map_title)
        map_layout.addWidget(self.map_status_label)
        map_layout.addWidget(self.map_view, 1)

        # Smaller minimums: the row now stretches to fill spare height.
        graph_card.setMinimumHeight(220)
        map_card.setMinimumHeight(220)
        monitoring_layout.addWidget(graph_card, 3)
        monitoring_layout.addWidget(map_card, 2)

        # Stretch factor 1 -> this row absorbs all remaining vertical space.
        self.main_layout.addLayout(monitoring_layout, 1)

    # =====================================
    # ARM
    # =====================================

    def arm_vehicle(self):

        self.is_armed = True

        self.manual_controller.clear()

        self.armed_label.setText("ARMED")
        self.armed_label.setObjectName("armedStatus")

        self.refresh_status_style()

        self.setFocus()

    # =====================================
    # DISARM
    # =====================================

    def disarm_vehicle(self):

        self.is_armed = False

        self.manual_controller.clear()

        # Immediately zero requested and actual thrust
        self.simulator.stop()

        self.armed_label.setText("DISARMED")
        self.armed_label.setObjectName("disarmedStatus")

        self.refresh_status_style()

        self.setFocus()

    # =====================================
    # REFRESH STATUS STYLE
    # =====================================

    def refresh_status_style(self):

        self.armed_label.style().unpolish(
            self.armed_label
        )

        self.armed_label.style().polish(
            self.armed_label
        )

        self.armed_label.update()

    # =====================================
    # KEYBOARD EVENT FILTER
    # =====================================

    def eventFilter(self, watched, event):

        event_type = event.type()

        # Clear held keys when application loses focus
        if event_type in (
            QEvent.Type.ApplicationDeactivate,
            QEvent.Type.WindowDeactivate
        ):

            self.manual_controller.clear()
            self.simulator.stop()

            return False

        # Only accept keyboard controls while armed
        if not self.is_armed:
            return super().eventFilter(watched, event)

        # Only Manual mode accepts keyboard commands
        if self.mode_selector.currentText() != "Manual":
            return super().eventFilter(watched, event)

        # Do not hijack typing in target input fields
        if isinstance(
            watched,
            (QLineEdit, QAbstractSpinBox, QComboBox)
        ):
            return super().eventFilter(watched, event)

        key_map = {
            Qt.Key.Key_W: "W",
            Qt.Key.Key_S: "S",
            Qt.Key.Key_A: "A",
            Qt.Key.Key_D: "D",
            Qt.Key.Key_Q: "Q",
            Qt.Key.Key_E: "E",

            Qt.Key.Key_Left: "LEFT",
            Qt.Key.Key_Right: "RIGHT",

            Qt.Key.Key_I: "I",
            Qt.Key.Key_K: "K",
            Qt.Key.Key_J: "J",
            Qt.Key.Key_L: "L",
        }

        # Key pressed
        if event_type == QEvent.Type.KeyPress:

            key = key_map.get(event.key())

            if key:

                # Repeated key events refresh the input timeout
                self.manual_controller.key_pressed(key)

                return True

        # Key released
        elif event_type == QEvent.Type.KeyRelease:

            key = key_map.get(event.key())

            if key:

                # Ignore auto-repeat release events
                if event.isAutoRepeat():
                    return True

                self.manual_controller.key_released(key)

                return True

        return super().eventFilter(watched, event)

    # =====================================
    # SIMULATION UPDATE
    # =====================================

    def update_simulation(self):

        current_time = time.monotonic()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        # Keep the simulation stable if the application pauses briefly.
        dt = max(0.001, min(dt, 0.1))

        selected_mode = self.mode_selector.currentText()

        # Safety gate: disarmed always means zero requested and actual thrust.
        if not self.is_armed:
            self.manual_controller.clear()
            self.simulator.stop()

        elif selected_mode == "Manual":
            command = self.manual_controller.get_command()
            self.simulator.set_command(command)

        elif selected_mode == "Depth Hold":
            self.manual_controller.clear()
            self.mode_controller.set_target_depth(
                self.depth_input.value()
            )
            command = self.mode_controller.get_command(
                "Depth Hold",
                self.simulator.get_state()
            )
            self.simulator.set_command(command)

        elif selected_mode == "Heading Hold":
            self.manual_controller.clear()
            self.mode_controller.set_target_heading(
                self.heading_input.value()
            )
            command = self.mode_controller.get_command(
                "Heading Hold",
                self.simulator.get_state()
            )
            self.simulator.set_command(command)

        else:
            # Unknown mode: fail safe.
            self.manual_controller.clear()
            self.simulator.stop()

        # Advance simulation and retrieve current telemetry.
        state = self.simulator.update(dt)
        self.simulation_time += dt

        # Update the map marker using the simulated local position.
        self.update_map_position(state.x, state.y)

        # Update telemetry cards.
        self.telemetry_labels["ROLL"].setText(
            f"{state.roll:.1f} °"
        )
        self.telemetry_labels["PITCH"].setText(
            f"{state.pitch:.1f} °"
        )
        self.telemetry_labels["YAW"].setText(
            f"{state.yaw:.1f} °"
        )
        self.telemetry_labels["DEPTH"].setText(
            f"{state.depth:.2f} m"
        )
        self.telemetry_labels["BATTERY"].setText(
            f"{state.battery_voltage:.2f} V"
        )

        self.position_label.setText(
            f"POSITION: X = {state.x:.2f} m | "
            f"Y = {state.y:.2f} m | "
            f"VELOCITY = {state.surge_velocity:.2f} m/s"
        )

        # Update depth-versus-time graph.
        self.time_history.append(self.simulation_time)
        self.depth_history.append(state.depth)

        # Keep a long history so the user can scroll / zoom back in time.
        cutoff = self.simulation_time - self.max_history_seconds
        if self.time_history[0] < cutoff:
            first = bisect.bisect_left(self.time_history, cutoff)
            self.time_history = self.time_history[first:]
            self.depth_history = self.depth_history[first:]

        self.depth_curve.setData(
            self.time_history,
            self.depth_history
        )

        # Axes are only forced while live-follow is on. When the user has
        # panned or zoomed, the view stays exactly where they left it.
        if self.follow_live:

            # X axis: sliding time window that moves with the line.
            t_end = max(self.simulation_time, self.plot_window_seconds)
            t_start = t_end - self.plot_window_seconds
            self.depth_plot.setXRange(t_start, t_end, padding=0)

            # Y axis: fit the visible samples, always including 0 m and
            # at least 15 m, expanding if the ROV goes deeper.
            first_visible = bisect.bisect_left(self.time_history, t_start)
            visible = self.depth_history[first_visible:]
            y_min = min(0.0, min(visible))
            y_max = max(15.0, max(visible) * 1.1)
            self.depth_plot.setYRange(y_min, y_max, padding=0)

    def set_follow_live(self, follow):
        """Switch the depth graph between live-follow and free-look."""
        self.follow_live = follow

        if follow:
            self.graph_status_label.setText("● LIVE")
            self.graph_status_label.setStyleSheet(
                "color: #86EFAC; font-size: 11px; font-weight: bold;"
            )
        else:
            self.graph_status_label.setText("● FREE VIEW")
            self.graph_status_label.setStyleSheet(
                "color: #FCD34D; font-size: 11px; font-weight: bold;"
            )

    def on_plot_manually_changed(self, *args):
        """User dragged or zoomed the graph: stop forcing the axes."""
        if self.follow_live:
            self.set_follow_live(False)

    def reset_graph_view(self):
        """Lock the axes again so the graph follows the live line."""
        self.set_follow_live(True)

        # Apply the live range immediately instead of waiting for the
        # next simulation tick.
        if self.time_history:
            t_end = max(self.simulation_time, self.plot_window_seconds)
            t_start = t_end - self.plot_window_seconds
            self.depth_plot.setXRange(t_start, t_end, padding=0)

            first_visible = bisect.bisect_left(self.time_history, t_start)
            visible = self.depth_history[first_visible:]
            y_min = min(0.0, min(visible))
            y_max = max(15.0, max(visible) * 1.1)
            self.depth_plot.setYRange(y_min, y_max, padding=0)

    def on_map_load_finished(self, success):
        """Report whether the embedded map page itself loaded."""
        if success:
            self.map_status_label.setText(
                "Map page loaded. Map tiles require an internet connection."
            )
        else:
            self.map_status_label.setText(
                "Map page failed to load. Check internet access or CDN availability."
            )

    def update_map_position(self, x_metres, y_metres):
        """
        Convert local simulator metres to approximate map coordinates.
        This marker is a visualization, not GPS or navigation data.
        """
        metres_per_degree_lat = 111320.0
        latitude = self.map_origin_lat + (
            y_metres / metres_per_degree_lat
        )

        longitude_scale = metres_per_degree_lat * max(
            0.01,
            abs(math.cos(math.radians(self.map_origin_lat)))
        )
        longitude = self.map_origin_lon + (
            x_metres / longitude_scale
        )

        javascript = (
            "if (typeof updateRovMarker === 'function') {"
            f"updateRovMarker({latitude:.8f}, {longitude:.8f});"
            "}"
        )
        self.map_view.page().runJavaScript(javascript)

    def on_mode_changed(self, mode):
        """
        Clear any held manual input when changing operating modes.
        The simulation timer will apply the newly selected mode.
        """
        self.manual_controller.clear()

        # Stop residual commanded thrust before the next mode computes
        # its own command. This does not reset vehicle momentum.
        self.simulator.stop()

    # =====================================
    # APPLICATION STYLING
    # =====================================

    def apply_styles(self):

        self.setStyleSheet("""

            QMainWindow {
                background-color: #101827;
            }

            QScrollArea {
                background-color: #101827;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background-color: #101827;
            }

            QLabel {
                color: #FFFFFF;
            }

            QLabel#mainTitle {
                color: #00BFFF;
                font-size: 25px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #94A3B8;
                font-size: 11px;
            }

            QLabel#sectionTitle {
                color: #00BFFF;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#telemetryName {
                color: #94A3B8;
                font-size: 12px;
            }

            QLabel#telemetryValue {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: bold;
            }

            QFrame#telemetryCard,
            QFrame#panel {
                background-color: #1A273A;
                border: 1px solid #293B53;
                border-radius: 10px;
            }

            QLabel#connectionStatus {
                color: #38BDF8;
                font-weight: bold;
                padding: 8px;
            }

            QLabel#armedStatus {
                background-color: #14532D;
                color: #86EFAC;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }

            QLabel#disarmedStatus {
                background-color: #7F1D1D;
                color: #FCA5A5;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }

            QLabel#mutedText,
            QLabel#mapPlaceholder {
                color: #94A3B8;
            }

            QLabel#mapStatus {
                color: #94A3B8;
                font-size: 10px;
                padding: 2px 4px;
            }

            QComboBox,
            QDoubleSpinBox {
                background-color: #26364C;
                color: white;
                border: 1px solid #40536D;
                border-radius: 5px;
                padding: 8px;
                min-height: 25px;
            }

            QPushButton {
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                color: white;
            }

            QPushButton#armButton {
                background-color: #15803D;
            }

            QPushButton#armButton:hover {
                background-color: #166534;
            }

            QPushButton#disarmButton {
                background-color: #B91C1C;
            }

            QPushButton#disarmButton:hover {
                background-color: #991B1B;
            }

            QPushButton#resetViewButton {
                background-color: #26364C;
                color: #00BFFF;
                border: 1px solid #40536D;
                border-radius: 5px;
                padding: 3px 10px;
                font-size: 11px;
            }

            QPushButton#resetViewButton:hover {
                background-color: #31455F;
            }

        """)

    # =====================================
    # CLOSE EVENT
    # =====================================

    def closeEvent(self, event):

        # Stop simulation and clear commands on exit
        self.is_armed = False

        self.manual_controller.clear()
        self.simulator.stop()

        self.simulation_timer.stop()

        QApplication.instance().removeEventFilter(self)

        event.accept()


# =========================================
# APPLICATION ENTRY POINT
# =========================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = ROVGroundStation()
    window.show()

    sys.exit(app.exec())