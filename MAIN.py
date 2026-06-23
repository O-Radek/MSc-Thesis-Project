from PySide6.QtWidgets import QApplication
from GUI_WORK import MainWindow

app = QApplication([])
window = MainWindow()

screen_geometry = QApplication.primaryScreen().availableGeometry() # get the available geometry of the primary screen
window.resize(screen_geometry.width(), screen_geometry.height())

window.show()
app.exec()