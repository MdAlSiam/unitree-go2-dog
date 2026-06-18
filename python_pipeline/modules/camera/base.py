from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from python_pipeline.pipeline.contracts import FrameSample


class CameraProviderBase(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self) -> Optional[FrameSample]:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError
