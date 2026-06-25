from __future__ import annotations

import logging
import time

from python_pipeline.modules.speech.base import SpeechProviderBase
from python_pipeline.modules.sport.base import SportProviderBase
from python_pipeline.pipeline.contracts import TickContext


class _BaseGoMotionActivity:
    name = "go_motion"

    def __init__(self, sport: SportProviderBase, speech: SpeechProviderBase) -> None:
        self._sport = sport
        self._speech = speech
        self._logger = logging.getLogger(self.__class__.__name__)

    def _announce(self, text: str) -> None:
        self._logger.info(text)
        self._speech.say(text)

    def _perform_sequence(self) -> None:
        raise NotImplementedError

    def on_start(self) -> None:
        self._speech.start()
        self._sport.start()
        self._sport.stand_up()
        time.sleep(2.0)

        self._sport.balance_stand()
        time.sleep(0.5)

        # Ensure stand guard is disabled before sending movement commands.
        self._sport.stop_stand_guard()

        self._perform_sequence()

        self._sport.balance_stand()
        self._sport.start_stand_guard(interval_s=1.0)

    def on_tick(self, context: TickContext) -> None:
        _ = context

    def on_stop(self) -> None:
        self._announce(f"Stopping {self.name} activity.")
        self._sport.stop()
        self._speech.stop()


class GoForwardActivity(_BaseGoMotionActivity):
    name = "go_forward"

    def _perform_sequence(self) -> None:
        self._announce("Going forward.")

        self._announce("Rotating left.")
        for _ in range(20):
            self._sport.move(0.0, 0.0, 0.2)
        time.sleep(1.0)
        self._sport.stop_move()

        self._announce("Moving forward.")
        for _ in range(40):
            self._sport.move(0.2, 0.0, 0.0)
        time.sleep(1.0)
        self._sport.stop_move()


class GoBackwardActivity(_BaseGoMotionActivity):
    name = "go_backward"

    def _perform_sequence(self) -> None:
        self._announce("Going backward.")

        self._announce("Moving backward.")
        for _ in range(40):
            self._sport.move(-0.2, 0.0, 0.0)
        time.sleep(1.0)
        self._sport.stop_move()

        self._announce("Rotating right.")
        for _ in range(20):
            self._sport.move(0.0, 0.0, -0.2)
        time.sleep(1.0)
        self._sport.stop_move()
