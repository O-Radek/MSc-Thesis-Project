from PySide6.QtWidgets import QApplication
from GUI_WORK import MainWindow

def main():
    app = QApplication([])

    window = MainWindow(app)

    # Resize the application to fill the available screen.
    screen_geometry = QApplication.primaryScreen().availableGeometry()
    window.resize(
        screen_geometry.width(),
        screen_geometry.height()
    )

    window.show()
    app.exec()

if __name__ == "__main__":
    main()