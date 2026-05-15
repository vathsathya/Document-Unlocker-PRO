import sys
import multiprocessing
import atexit
import os

# Suppress Qt font warnings on Linux
os.environ["QT_LOGGING_RULES"] = "qt.text.font.db.warning=false"

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from src.ui.main_window import MainWindow
from src.engine.recovery import shutdown_executor

def main():
    # Essential for PyInstaller + Multiprocessing
    multiprocessing.freeze_support()
    
    if getattr(sys, 'frozen', False):
        multiprocessing.set_executable(sys.executable)
    
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
        
    app = QApplication(sys.argv)
    app.setApplicationName("DocumentUnlockerPRO")

    # Single Instance Lock
    socket_name = "DocumentUnlockerPRO_SingleInstance"
    socket = QLocalSocket()
    socket.connectToServer(socket_name)
    if socket.waitForConnected(500):
        # Already running
        print("Another instance is already running.")
        sys.exit(0)
    
    # Not running, start server
    server = QLocalServer()
    server.listen(socket_name)
    
    window = MainWindow()
    window.show()
    
    # Register cleanup
    atexit.register(shutdown_executor)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
