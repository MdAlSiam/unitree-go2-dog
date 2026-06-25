from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class PathPoint:
    time_from_start: float
    x: float
    y: float
    yaw: float
    vx: float
    vy: float
    vyaw: float


class SportProviderBase(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stand_up(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stand_down(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def balance_stand(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def move(self, vx: float, vy: float, vyaw: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def speed_level(self, level: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def damp(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def recovery_stand(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def sit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rise_sit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop_move(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def trajectory_follow(self, points: Sequence[PathPoint]) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError
