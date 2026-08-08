"""Matcher interface"""

from __future__ import annotations

import time
from typing import Callable, List, Optional, Protocol, Union, runtime_checkable

from ..core.angles import AngleVector
from ..core.types import GestureTemplate, MatchResult

AngleWindow = List[AngleVector]
MatchInput = Union[AngleVector, AngleWindow]


def best_of(
    score: Callable[[GestureTemplate], float],
    templates: List[GestureTemplate],
    timestamp: Optional[float] = None,
) -> Optional[MatchResult]:
    """Highest-scoring template, or None when ``templates`` is empty.

    Shared by every matcher: only the per-template scoring differs between them.
    """
    ts = time.time() if timestamp is None else timestamp
    best: Optional[MatchResult] = None
    for template in templates:
        s = score(template)
        if best is None or s > best.score:
            best = MatchResult(gesture_id=template.gesture_id, score=s, timestamp=ts)
    return best


@runtime_checkable
class MatcherStrategy(Protocol):
    def score(self, current: MatchInput, template: GestureTemplate) -> float: ...

    def best_match(
        self, current: MatchInput, templates: List[GestureTemplate]
    ) -> MatchResult | None: ...
