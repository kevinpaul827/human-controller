import sys


def create_picture_in_picture():
    if sys.platform == "darwin":
        from .platforms.macos.pip_process import MacOSPictureInPictureProxy

        return MacOSPictureInPictureProxy()

    from .picture_in_picture_window import PictureInPictureWindow

    return PictureInPictureWindow()
