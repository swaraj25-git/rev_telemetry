
import sys

import pyqtgraph as pg

from PySide6.QtCore import Qt
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
)


class ROVGroundStation(QMainWindow):

    def __init__(self):
        super().__init__()

        self.is_armed = False
        self.telemetry_labels = {}

        self.setWindowTitle("ROV Telemetry Ground Station")
        self.resize(1250, 850)
        self.setMinimumSize(1000, 700)

        # Main application container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(14)

        # Build dashboard sections
        self.create_header()
        self.create_telemetry_section()
        self.create_control_sections()
        self.create_monitoring_section()

        # Apply application theme
        self.apply_styles()

    # -----------------------------------------
    # 1. HEADER
    # -----------------------------------------

    def create_header(self):

        header = QHBoxLayout()

        title = QLabel("ROV GROUND STATION")
        title.setObjectName("mainTitle")

        subtitle = QLabel("UNDERWATER VEHICLE MONITORING")
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

    # -----------------------------------------
    # 2. TELEMETRY CARDS
    # -----------------------------------------

    def create_telemetry_section(self):

        section_title = QLabel("LIVE TELEMETRY")
        section_title.setObjectName("sectionTitle")

        self.main_layout.addWidget(section_title)

        telemetry_grid = QGridLayout()
        telemetry_grid.setSpacing(12)

        telemetry_data = [
            ("ROLL", "2.5", "°"),
            ("PITCH", "-1.2", "°"),
            ("YAW", "90.0", "°"),
            ("DEPTH", "12.5", "m"),
            ("BATTERY", "14.5", "V"),
        ]

        for index, (name, value, unit) in enumerate(telemetry_data):

            card = QFrame()
            card.setObjectName("telemetryCard")

            card_layout = QVBoxLayout(card)

            name_label = QLabel(name)
            name_label.setObjectName("telemetryName")

            value_label = QLabel(value + " " + unit)
            value_label.setObjectName("telemetryValue")

            card_layout.addWidget(name_label)
            card_layout.addWidget(value_label)

            telemetry_grid.addWidget(card, 0, index)

            self.telemetry_labels[name] = value_label

        self.main_layout.addLayout(telemetry_grid)

    # -----------------------------------------
    # 3. CONTROL SECTIONS
    # -----------------------------------------

    def create_control_sections(self):

        controls_layout = QGridLayout()
        controls_layout.setSpacing(12)

        # Operating mode card
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

        mode_layout.addWidget(mode_title)
        mode_layout.addWidget(self.mode_selector)

        # Target settings card
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

        depth_label = QLabel("Target Depth")
        heading_label = QLabel("Target Heading")

        target_layout.addWidget(target_title)
        target_layout.addWidget(depth_label)
        target_layout.addWidget(self.depth_input)
        target_layout.addWidget(heading_label)
        target_layout.addWidget(self.heading_input)

        # Arm / Disarm card
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

        # Movement control preview
        movement_card = QFrame()
        movement_card.setObjectName("panel")

        movement_layout = QVBoxLayout(movement_card)

        movement_title = QLabel("MOVEMENT CONTROLS")
        movement_title.setObjectName("sectionTitle")

        movement_note = QLabel(
            "Keyboard controls and thruster commands "
            "will be implemented in the simulation stage."
        )
        movement_note.setWordWrap(True)
        movement_note.setObjectName("mutedText")

        movement_layout.addWidget(movement_title)
        movement_layout.addWidget(movement_note)

        controls_layout.addWidget(mode_card, 0, 0)
        controls_layout.addWidget(target_card, 0, 1)
        controls_layout.addWidget(safety_card, 1, 0)
        controls_layout.addWidget(movement_card, 1, 1)

        self.main_layout.addLayout(controls_layout)

    # -----------------------------------------
    # 4. MONITORING SECTION
    # -----------------------------------------

    def create_monitoring_section(self):

        monitoring_layout = QHBoxLayout()
        monitoring_layout.setSpacing(12)

        # Depth graph
        graph_card = QFrame()
        graph_card.setObjectName("panel")

        graph_layout = QVBoxLayout(graph_card)

        graph_title = QLabel("DEPTH VS TIME")
        graph_title.setObjectName("sectionTitle")

        self.depth_plot = pg.PlotWidget()
        self.depth_plot.setBackground("#172235")
        self.depth_plot.setLabel("left", "Depth", units="m")
        self.depth_plot.setLabel("bottom", "Time", units="s")
        self.depth_plot.showGrid(x=True, y=True, alpha=0.3)
        self.depth_plot.invertY(True)

        sample_times = [0, 2, 4, 6, 8, 10]
        sample_depths = [0, 2, 4, 6, 9, 12.5]

        self.depth_plot.plot(
            sample_times,
            sample_depths,
            pen=pg.mkPen("#00BFFF", width=2),
            symbol="o",
            symbolSize=6
        )

        graph_layout.addWidget(graph_title)
        graph_layout.addWidget(self.depth_plot)

        # Map placeholder
        map_card = QFrame()
        map_card.setObjectName("panel")

        map_layout = QVBoxLayout(map_card)

        map_title = QLabel("UNDERWATER LOCATION MAP")
        map_title.setObjectName("sectionTitle")

        map_placeholder = QLabel(
            "OpenStreetMap integration\n\n"
            "Will be added in the map integration stage."
        )
        map_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        map_placeholder.setObjectName("mapPlaceholder")

        map_layout.addWidget(map_title)
        map_layout.addWidget(map_placeholder)

        monitoring_layout.addWidget(graph_card, 3)
        monitoring_layout.addWidget(map_card, 2)

        self.main_layout.addLayout(monitoring_layout)

    # -----------------------------------------
    # 5. ARM / DISARM UI ACTIONS
    # -----------------------------------------

    def arm_vehicle(self):

        self.is_armed = True

        self.armed_label.setText("ARMED")
        self.armed_label.setObjectName("armedStatus")

        self.refresh_status_style()

    def disarm_vehicle(self):

        self.is_armed = False

        self.armed_label.setText("DISARMED")
        self.armed_label.setObjectName("disarmedStatus")

        self.refresh_status_style()

    def refresh_status_style(self):

        # Refresh the label after changing its style identifier
        self.armed_label.style().unpolish(self.armed_label)
        self.armed_label.style().polish(self.armed_label)

    # -----------------------------------------
    # 6. APPLICATION STYLING
    # -----------------------------------------

    def apply_styles(self):

        self.setStyleSheet("""

            QMainWindow {
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

        """)


# -----------------------------------------
# APPLICATION ENTRY POINT
# -----------------------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = ROVGroundStation()
    window.show()

    sys.exit(app.exec())
