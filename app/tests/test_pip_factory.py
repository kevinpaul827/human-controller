import unittest
from unittest.mock import MagicMock, patch

import app.platforms.picture_in_picture as pip_factory


class PictureInPictureFactoryTests(unittest.TestCase):
    @patch("app.ui.picture_in_picture_window.PictureInPictureWindow")
    def test_windows_uses_existing_in_process_window(self, window_class):
        window = MagicMock()
        window_class.return_value = window

        with patch.object(pip_factory.sys, "platform", "win32"):
            self.assertIs(pip_factory.create_picture_in_picture(), window)

        window_class.assert_called_once_with()

    @patch("app.platforms.macos.pip_process.MacOSPictureInPictureProxy")
    def test_macos_uses_helper_process_proxy(self, proxy_class):
        proxy = MagicMock()
        proxy_class.return_value = proxy

        with patch.object(pip_factory.sys, "platform", "darwin"):
            self.assertIs(pip_factory.create_picture_in_picture(), proxy)

        proxy_class.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
