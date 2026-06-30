"""Matcher interface"""

from __future__ import annotations

from typing import List, Protocol, Union, runtime_checkable

from ..core.angles import AngleVector
from ..core.types import GestureTemplate, MatchResult

AngleWindow = List[AngleVector]
MatchInput = Union[AngleVector, AngleWindow]


@runtime_checkable
class MatcherStrategy(Protocol):
    def score(self, current: MatchInput, template: GestureTemplate) -> float: ...

    def best_match(
        self, current: MatchInput, templates: List[GestureTemplate]
    ) -> MatchResult | None: ...
