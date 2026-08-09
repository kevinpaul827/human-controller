import math

import pytest

from backend.matching_engine.core.angles import AngleKey
from backend.matching_engine.core.types import (
    MOTION_TYPE,
    SCHEMA_VERSION,
    GestureTemplate,
)


def test_template_uses_typed_trajectory_and_serializes_schema():
    template = GestureTemplate(
        name="Wave",
        active_joints=[AngleKey.L_ELBOW],
        trajectory=[{"L_ELBOW": 90.0}],
    )

    assert template.trajectory == [{AngleKey.L_ELBOW: 90.0}]
    payload = template.to_dict()
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["type"] == MOTION_TYPE
    assert payload["trajectory"] == [{"L_ELBOW": 90.0}]
    assert GestureTemplate.from_dict(payload) == template


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fps": 0},
        {"fps": 1.5},
        {"trajectory": [{AngleKey.L_ELBOW: math.inf}]},
    ],
)
def test_invalid_template_values_are_rejected(kwargs):
    with pytest.raises(ValueError):
        GestureTemplate(name="Wave", **kwargs)


def test_unsupported_schema_version_is_rejected():
    with pytest.raises(ValueError, match="schema version"):
        GestureTemplate.from_dict(
            {
                "schema_version": SCHEMA_VERSION + 1,
                "gesture_id": "wave",
                "name": "Wave",
            }
        )


def test_state_template_payload_is_rejected():
    with pytest.raises(ValueError, match="motion"):
        GestureTemplate.from_dict(
            {
                "gesture_id": "wave",
                "name": "Wave",
                "type": "state",
            }
        )
