from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Sequence

from .base import SpeechProviderBase


class SystemSpeechProvider(SpeechProviderBase):
    def __init__(self, preferred_commands: Sequence[str] | None = None) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._preferred_commands = tuple(preferred_commands or ("spd-say", "espeak-ng", "espeak"))
        self._command: str | None = None

    def start(self) -> None:
        for candidate in self._preferred_commands:
            if shutil.which(candidate):
                self._command = candidate
                self._logger.info("System speech provider started using '%s'", candidate)
                return
        self._command = None
        self._logger.warning(
            "No system TTS command found. Install one of: %s",
            ", ".join(self._preferred_commands),
        )

    def say(self, text: str) -> None:
        if not text:
            return
        if self._command is None:
            self._logger.info("Speech fallback (no TTS command available): %s", text)
            return

        try:
            if self._command == "spd-say":
                subprocess.Popen([self._command, text])
            else:
                subprocess.Popen([self._command, text])
        except Exception as exc:  # pragma: no cover
            self._logger.warning("TTS command failed: %s", exc)

    def stop(self) -> None:
        self._logger.info("System speech provider stopped")
