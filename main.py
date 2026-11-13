import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)

from PySide6.QtCore import Qt

class ROVGroundStation(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ROV Telementary Ground Station")
        self.resize(1100,700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        title = QLabel("ROV Ground Station")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #00BFFF;
            padding: 20px;
        """)

        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Underwater Vehicle Monitoring System")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setStyleSheet("font-size: 15px; color: white;")

        main_layout.addWidget(subtitle)

        # Telemetry section
        telemetry_layout = QHBoxLayout()

        telemetry_values = [
            ("ROLL", "2.5°"),
            ("PITCH", "-1.2°"),
            ("YAW", "90°"),
            ("DEPTH", "12.5 m"),
            ("BATTERY", "14.5 V"),
        ]

        for name, value in telemetry_values:

            card_layout = QVBoxLayout()

            name_label = QLabel(name)
            value_label = QLabel(value)

            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            name_label.setStyleSheet(
                "font-size: 14px; color: #A0AEC0;"
            )

            value_label.setStyleSheet(
                "font-size: 23px; font-weight: bold; color: white;"
            )

            card_layout.addWidget(name_label)
            card_layout.addWidget(value_label)

            telemetry_layout.addLayout(card_layout)

        main_layout.addLayout(telemetry_layout)

        # Arm and Disarm buttons
        button_layout = QHBoxLayout()

        arm_button = QPushButton("ARM")
        disarm_button = QPushButton("DISARM")

        arm_button.setMinimumHeight(50)
        disarm_button.setMinimumHeight(50)

        button_layout.addWidget(arm_button)
        button_layout.addWidget(disarm_button)

        main_layout.addLayout(button_layout)

        # Dark background
        self.setStyleSheet("""
            QMainWindow {
                background-color: #101827;
            }

            QPushButton {
                background-color: #1E88E5;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #1565C0;
            }
        """)


# Application entry point
if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = ROVGroundStation()
    window.show()

    sys.exit(app.exec())

        