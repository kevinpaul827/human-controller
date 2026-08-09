import sys
from types import ModuleType
from unittest.mock import MagicMock


def install_pyside6_stub() -> None:
    for module_name in list(sys.modules):
        if module_name == "PySide6" or module_name.startswith("PySide6."):
            sys.modules.pop(module_name, None)

    pyside6_module = ModuleType("PySide6")
    qtcore_module = ModuleType("PySide6.QtCore")
    qtgui_module = ModuleType("PySide6.QtGui")
    qtmultimedia_module = ModuleType("PySide6.QtMultimedia")
    qtwebchannel_module = ModuleType("PySide6.QtWebChannel")
    qtwebengine_module = ModuleType("PySide6.QtWebEngineWidgets")
    qtmultimediawidgets_module = ModuleType("PySide6.QtMultimediaWidgets")
    qtwidgets_module = ModuleType("PySide6.QtWidgets")

    qtcore_module.Qt = type(
        "Qt",
        (),
        {
            "WidgetAttribute": type(
                "WidgetAttribute",
                (),
                {
                    "WA_TransparentForMouseEvents": object(),
                    "WA_TranslucentBackground": object(),
                },
            )
        },
    )
    qtcore_module.QLineF = type("QLineF", (), {})
    qtcore_module.QPointF = type("QPointF", (), {})
    qtcore_module.QRectF = type("QRectF", (), {})
    qtcore_module.QUrl = type(
        "QUrl",
        (),
        {
            "__init__": lambda self, value=None: None,
            "fromLocalFile": staticmethod(lambda path: path),
        },
    )
    qtcore_module.QCameraPermission = type("QCameraPermission", (), {})
    qtcore_module.QCoreApplication = type("QCoreApplication", (), {})
    qtcore_module.QElapsedTimer = type("QElapsedTimer", (), {})
    qtcore_module.QObject = type("QObject", (), {})
    qtcore_module.Signal = lambda *args, **kwargs: MagicMock()
    qtcore_module.Slot = lambda *args, **kwargs: (lambda func: func)
    qtcore_module.QThread = type("QThread", (), {})
    qtgui_module.QColor = type("QColor", (), {})
    qtgui_module.QDesktopServices = type("QDesktopServices", (), {})
    qtgui_module.QImage = type("QImage", (), {})
    qtgui_module.QPainter = type("QPainter", (), {})
    qtgui_module.QPen = type("QPen", (), {})
    qtmultimedia_module.QCamera = type("QCamera", (), {})
    qtmultimedia_module.QMediaCaptureSession = type("QMediaCaptureSession", (), {})
    qtmultimedia_module.QMediaDevices = type("QMediaDevices", (), {})
    qtmultimedia_module.QVideoFrame = type("QVideoFrame", (), {})
    qtmultimedia_module.QVideoSink = type("QVideoSink", (), {})
    qtwebchannel_module.QWebChannel = type("QWebChannel", (), {})
    qtwebengine_module.QWebEngineView = type("QWebEngineView", (), {})
    qtmultimediawidgets_module.QVideoWidget = type("QVideoWidget", (), {})
    qtwidgets_module.QApplication = type("QApplication", (), {})
    qtwidgets_module.QMessageBox = type(
        "QMessageBox",
        (),
        {"critical": staticmethod(lambda *args, **kwargs: None)},
    )
    qtwidgets_module.QMainWindow = type("QMainWindow", (), {})
    qtwidgets_module.QWidget = type("QWidget", (), {})

    sys.modules.setdefault("PySide6", pyside6_module)
    sys.modules["PySide6.QtCore"] = qtcore_module
    sys.modules["PySide6.QtGui"] = qtgui_module
    sys.modules["PySide6.QtMultimedia"] = qtmultimedia_module
    sys.modules["PySide6.QtWebChannel"] = qtwebchannel_module
    sys.modules["PySide6.QtWebEngineWidgets"] = qtwebengine_module
    sys.modules["PySide6.QtMultimediaWidgets"] = qtmultimediawidgets_module
    sys.modules["PySide6.QtWidgets"] = qtwidgets_module


def install_pose_processor_stub() -> None:
    pose_processor_module = ModuleType("app.core.pose_processor")
    pose_processor_module.PoseProcessor = type("PoseProcessor", (), {})
    sys.modules["app.core.pose_processor"] = pose_processor_module


def install_overlay_constants_stub() -> None:
    overlay_constants_module = ModuleType("app.ui.overlay_constants")
    overlay_constants_module.MIN_VISIBILITY = 0.5
    overlay_constants_module.POSE_CONNECTIONS = []
    overlay_constants_module.connections_for_angle_joints = lambda _joints: set()
    overlay_constants_module.landmarks_for_angle_joints = lambda _joints: set()
    sys.modules["app.ui.overlay_constants"] = overlay_constants_module


def install_picture_in_picture_stub() -> None:
    picture_in_picture_module = ModuleType("app.ui.picture_in_picture_window")
    picture_in_picture_module.PictureInPictureWindow = type(
        "PictureInPictureWindow", (), {}
    )
    sys.modules["app.ui.picture_in_picture_window"] = picture_in_picture_module


def ensure_qt_and_ui_stubs() -> None:
    try:
        from PySide6.QtCore import QElapsedTimer, QThread, Qt, QUrl  # noqa: F401
        from PySide6.QtGui import QDesktopServices, QImage  # noqa: F401
        from PySide6.QtMultimedia import (  # noqa: F401
            QCamera,
            QMediaCaptureSession,
            QMediaDevices,
            QVideoFrame,
        )
        from PySide6.QtMultimediaWidgets import QVideoWidget  # noqa: F401
        from PySide6.QtWebChannel import QWebChannel  # noqa: F401
        from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
        from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox  # noqa: F401
    except Exception:
        install_pyside6_stub()

    install_pose_processor_stub()
    install_overlay_constants_stub()
    install_picture_in_picture_stub()


def import_main_modules_with_stubs():
    app_modules_before = {
        name: module
        for name, module in sys.modules.items()
        if name == "app" or name.startswith("app.")
    }
    app_package = sys.modules.get("app")
    app_attributes_before = (
        dict(vars(app_package)) if app_package is not None else {}
    )

    ensure_qt_and_ui_stubs()

    from app import main
    from app.ui import main_window

    for module_name in list(sys.modules):
        if (
            module_name == "app" or module_name.startswith("app.")
        ) and module_name not in app_modules_before:
            sys.modules.pop(module_name, None)
    for module_name, module in app_modules_before.items():
        sys.modules[module_name] = module
    if app_package is not None:
        for attribute in list(vars(app_package)):
            if attribute not in app_attributes_before:
                delattr(app_package, attribute)
        for attribute, value in app_attributes_before.items():
            setattr(app_package, attribute, value)

    return main, main_window
