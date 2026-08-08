import math
from unittest.mock import Mock

import numpy as np
import pytest

from backend.camera_service.camera_feed import CameraFeed


def _capture(*, opened: bool = True, read_result=None):
    capture = Mock()
    capture.isOpened.return_value = opened
    capture.read.return_value = read_result or (
        True,
        np.zeros((2, 2, 3), dtype=np.uint8),
    )
    return capture


def test_open_failure_releases_capture_and_can_be_retried():
    failed = _capture(opened=False)
    opened = _capture()
    factory = Mock(side_effect=[failed, opened])
    clock = Mock(return_value=10.0)
    feed = CameraFeed(capture_factory=factory, clock=clock)

    assert feed.open() is False
    failed.release.assert_called_once_with()
    assert feed.feed is None
    assert feed.open() is True
    assert factory.call_count == 2


def test_open_is_idempotent_while_capture_is_active():
    capture = _capture()
    factory = Mock(return_value=capture)
    feed = CameraFeed(capture_factory=factory, clock=Mock(return_value=5.0))

    assert feed.open() is True
    assert feed.open() is True

    factory.assert_called_once_with(0)


def test_read_throttles_output_and_returns_elapsed_timestamp():
    capture = _capture()
    clock = Mock(side_effect=[0.0, 0.1, 0.11, 0.15])
    feed = CameraFeed(
        target_fps=30,
        capture_factory=Mock(return_value=capture),
        clock=clock,
    )
    assert feed.open() is True

    first_ok, first_frame, first_timestamp = feed.read()
    second_ok, second_frame, second_timestamp = feed.read()
    third_ok, third_frame, third_timestamp = feed.read()

    assert first_ok is True
    assert first_frame is capture.read.return_value[1]
    assert 99 <= first_timestamp <= 100
    assert (second_ok, second_frame, second_timestamp) == (True, None, 0)
    assert third_ok is True
    assert third_frame is capture.read.return_value[1]
    assert 149 <= third_timestamp <= 150


def test_read_and_close_handle_unavailable_capture():
    feed = CameraFeed(capture_factory=Mock(), clock=Mock())

    assert feed.read() == (False, None, 0)
    feed.close()

    capture = _capture(read_result=(False, None))
    feed = CameraFeed(
        capture_factory=Mock(return_value=capture),
        clock=Mock(return_value=1.0),
    )
    feed.open()
    assert feed.read() == (False, None, 0)
    feed.close()
    capture.release.assert_called_once_with()
    assert feed.feed is None


@pytest.mark.parametrize("target_fps", [0, -1, math.nan, math.inf])
def test_invalid_target_fps_is_rejected(target_fps):
    with pytest.raises(ValueError, match="Target FPS"):
        CameraFeed(target_fps=target_fps)
