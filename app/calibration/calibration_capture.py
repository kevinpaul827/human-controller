from collections import deque
from enum import Enum
import math
from statistics import median


class CapturePhase(str, Enum):
    IDLE = "idle"
    COUNTDOWN = "countdown"
    WAITING = "waiting"
    RECORDING = "recording"
    CAPTURED = "captured"


def _valid_angles(angles):
    return {
        key: float(value)
        for key, value in (angles or {}).items()
        if value is not None and math.isfinite(float(value))
    }


def _wrapped_delta(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def _median_frame(frames):
    keys = {key for frame in frames for key in frame}
    out = {}
    for key in keys:
        values = [frame[key] for frame in frames if key in frame]
        ref = values[0]
        shifted = [ref + _wrapped_delta(v, ref) for v in values]
        out[key] = float(median(shifted))
    return out


def _largest_delta(current, reference):
    deltas = [
        abs(_wrapped_delta(current[key], reference[key]))
        for key in current.keys() & reference.keys()
    ]
    return max(deltas, default=0.0)


class CalibrationCaptureController:


    PREP_SECONDS = 3.0
    DEFAULT_RECORDING_SECONDS = 10.0
    MIN_RECORDING_SECONDS = 1.0
    MAX_RECORDING_SECONDS = 60.0

    START_DELTA_DEG = 8.0
    START_CONFIRM_FRAMES = 2
    MIN_TOTAL_MOVEMENT_DEG = 15.0
    END_HOLD_SECONDS = 1.0
    END_STABLE_RANGE_DEG = 5.0
    PRE_ROLL_FRAMES = 8

    def __init__(self):
        self.phase = CapturePhase.IDLE
        self.phase_started_at = 0.0
        self.recording_seconds = self.DEFAULT_RECORDING_SECONDS
        self.frames = []
        self._baseline_frames = []
        self._baseline = {}
        self._pre_roll = deque(maxlen=self.PRE_ROLL_FRAMES)
        self._start_confirmed_frames = 0
        self._stability_window = deque()

    @property
    def active(self):
        return self.phase in {
            CapturePhase.COUNTDOWN,
            CapturePhase.WAITING,
            CapturePhase.RECORDING,
        }

    def start(self, now, recording_seconds=DEFAULT_RECORDING_SECONDS):
        duration = float(recording_seconds)
        if not math.isfinite(duration):
            raise ValueError("Recording duration must be a number.")
        if not self.MIN_RECORDING_SECONDS <= duration <= self.MAX_RECORDING_SECONDS:
            raise ValueError(
                f"Recording duration must be between {self.MIN_RECORDING_SECONDS:g} "
                f"and {self.MAX_RECORDING_SECONDS:g} seconds."
            )
        self.phase = CapturePhase.COUNTDOWN
        self.phase_started_at = float(now)
        self.recording_seconds = duration
        self.frames = []
        self._baseline_frames = []
        self._baseline = {}
        self._pre_roll.clear()
        self._start_confirmed_frames = 0
        self._stability_window.clear()

    def cancel(self):
        self.phase = CapturePhase.IDLE
        self.phase_started_at = 0.0
        self.frames = []
        self._baseline_frames = []
        self._baseline = {}
        self._pre_roll.clear()
        self._start_confirmed_frames = 0
        self._stability_window.clear()

    def reset(self):
        self.cancel()

    def remaining_seconds(self, now):
        if self.phase == CapturePhase.COUNTDOWN:
            duration = self.PREP_SECONDS
        elif self.phase == CapturePhase.RECORDING:
            duration = self.recording_seconds
        else:
            return 0
        remaining = duration - (float(now) - self.phase_started_at)
        return max(0, math.ceil(remaining))

    def update(self, angles, now):

        now = float(now)
        valid_angles = _valid_angles(angles)

        if self.phase == CapturePhase.COUNTDOWN:
            if valid_angles:
                self._baseline_frames.append(valid_angles)
            if now - self.phase_started_at < self.PREP_SECONDS - 1e-6:
                return False

            self._baseline = _median_frame(self._baseline_frames)
            self.phase = CapturePhase.WAITING
            self.phase_started_at = now
            self._pre_roll.clear()
            if self._baseline:
                self._pre_roll.append(dict(self._baseline))
            return False

        if self.phase == CapturePhase.WAITING:
            if not valid_angles or not self._baseline:
                return False

            self._pre_roll.append(valid_angles)
            if _largest_delta(valid_angles, self._baseline) >= self.START_DELTA_DEG:
                self._start_confirmed_frames += 1
            else:
                self._start_confirmed_frames = 0

            if self._start_confirmed_frames < self.START_CONFIRM_FRAMES:
                return False

            self.phase = CapturePhase.RECORDING
            self.phase_started_at = now
            self.frames = [dict(frame) for frame in self._pre_roll]
            self._stability_window.clear()
            self._stability_window.append((now, valid_angles))
            return False

        if self.phase != CapturePhase.RECORDING:
            return False

        if valid_angles:
            self.frames.append(valid_angles)
            self._stability_window.append((now, valid_angles))
            cutoff = now - self.END_HOLD_SECONDS
            while self._stability_window and self._stability_window[0][0] < cutoff:
                self._stability_window.popleft()

        reached_limit = now - self.phase_started_at >= self.recording_seconds - 1e-6
        if reached_limit or self._has_stable_final_pose(now):
            self.phase = CapturePhase.CAPTURED
            return True

        return False

    def _has_stable_final_pose(self, now):
        if not self.frames or not self._baseline or len(self._stability_window) < 2:
            return False
        if self._largest_range(self.frames) < self.MIN_TOTAL_MOVEMENT_DEG:
            return False

        window_duration = now - self._stability_window[0][0]
        if window_duration < self.END_HOLD_SECONDS - 1e-6:
            return False
        return self._largest_range(
            [frame for _, frame in self._stability_window]
        ) <= self.END_STABLE_RANGE_DEG

    @staticmethod
    def _largest_range(frames):
        keys = {key for frame in frames for key in frame}
        ranges = []
        for key in keys:
            values = [frame[key] for frame in frames if key in frame]
            if len(values) < 2:
                continue
            unwrapped = [values[0]]
            for value in values[1:]:
                unwrapped.append(unwrapped[-1] + _wrapped_delta(value, unwrapped[-1]))
            ranges.append(max(unwrapped) - min(unwrapped))
        return max(ranges, default=0.0)
