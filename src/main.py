import sys

from PyQt5.QtWidgets import QApplication

from theme import APP_STYLESHEET
from ui import MainWindow

try:
    import resources  # noqa: F401
except ImportError:
    print("提示: 未找到 resources.py，窗口图标可能无法显示。")
    print("可运行: pyrcc5 src/resources.qrc -o src/resources.py")


def main():
    if sys.platform.startswith('win'):
        from multiprocessing import freeze_support
        freeze_support()

    app = QApplication(sys.argv)
    app.setApplicationName("AB Video Deduplicator")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
