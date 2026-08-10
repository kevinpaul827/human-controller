from __future__ import annotations

import math

import psutil

GIBIBYTE = 1024**3


def _positive_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def _core_count(value):
    number = _positive_number(value)
    if number is None:
        return None
    return max(1, int(number))


def select_pose_model(ram_gb, physical_cores, logical_cores=None):
    memory = _positive_number(ram_gb)
    physical = _core_count(physical_cores)
    logical = _core_count(logical_cores)
    if memory is None:
        return "lite"
    if physical is not None:
        if memory >= 15 and physical >= 8:
            return "heavy"
        if memory >= 7 and physical >= 4:
            return "full"
        return "lite"
    if logical is not None:
        if memory >= 15 and logical >= 12:
            return "heavy"
        if memory >= 7 and logical >= 6:
            return "full"
    return "lite"


def device_pose_recommendation():
    try:
        raw_ram_gb = _positive_number(psutil.virtual_memory().total / GIBIBYTE)
        ram_gb = round(raw_ram_gb, 1) if raw_ram_gb is not None else None
    except (psutil.Error, AttributeError, OSError, TypeError, ValueError):
        raw_ram_gb = None
        ram_gb = None
    try:
        logical_cores = psutil.cpu_count(logical=True)
    except (psutil.Error, OSError, TypeError, ValueError):
        logical_cores = None
    try:
        physical_cores = psutil.cpu_count(logical=False)
    except (psutil.Error, OSError, TypeError, ValueError):
        physical_cores = None
    physical_cores = _core_count(physical_cores)
    logical_cores = _core_count(logical_cores)
    return {
        "poseModel": select_pose_model(
            raw_ram_gb,
            physical_cores,
            logical_cores,
        ),
        "ramGb": ram_gb,
        "physicalCpuCount": physical_cores,
        "logicalCpuCount": logical_cores,
    }
