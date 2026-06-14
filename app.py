import sys
import os
import logging
from logging.handlers import RotatingFileHandler

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

def setup_logging():
    from config.constants import LOG_FILE_PATH, LOG_FORMAT, LOG_DATE_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def setup_exception_hook():
    logger = logging.getLogger('app')
    def exception_hook(exc_type, exc_value, exc_tb):
        logger.critical('Unhandled exception', exc_info=(exc_type, exc_value, exc_tb))
    sys.excepthook = exception_hook

def main():
    setup_logging()
    setup_exception_hook()
    logger = logging.getLogger('app')
    logger.info('Starting YouTube Media Downloader')
    
    # High DPI support
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setQuitOnLastWindowClosed(False)
    
    from config.constants import APP_NAME, APP_ORGANIZATION, ASSETS_DIR
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    
    # Set app icon
    icon_path = os.path.join(str(ASSETS_DIR), 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Apply saved theme
    from ui.styles.theme import ThemeManager
    from services.settings_manager import SettingsManager
    settings = SettingsManager.instance()
    ThemeManager.apply_theme(app, settings.get_theme())
    
    # Create and show main window
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    logger.info('Application window shown')
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
