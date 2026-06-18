from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol


@dataclass
class FrameSample:
    data: bytes
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TickContext:
    tick_index: int
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CameraProvider(Protocol):
    def start(self) -> None:
        ...

    def read(self) -> Optional[FrameSample]:
        ...

    def stop(self) -> None:
        ...


class SpeechProvider(Protocol):
    def start(self) -> None:
        ...

    def say(self, text: str) -> None:
        ...

    def stop(self) -> None:
        ...


class Activity(Protocol):
    name: str

    def on_start(self) -> None:
        ...

    def on_tick(self, context: TickContext) -> None:
        ...

    def on_stop(self) -> None:
        ...
