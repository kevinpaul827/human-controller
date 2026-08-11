"""picture_in_picture.py

Creates picture-in-picture window for specific
platform.
"""
import sys


def create_picture_in_picture():
    if sys.platform == "darwin":
        from .macos.pip_process import MacOSPictureInPictureProxy

        return MacOSPictureInPictureProxy()

    from ..ui.picture_in_picture_window import PictureInPictureWindow

    return PictureInPictureWindow()
