from __future__ import annotations

import logging

from .base import SpeechProviderBase


class NullSpeechProvider(SpeechProviderBase):
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def start(self) -> None:
        self._logger.info("Null speech provider started")

    def say(self, text: str) -> None:
        self._logger.info("Speech intent (placeholder): %s", text)

    def stop(self) -> None:
        self._logger.info("Null speech provider stopped")
