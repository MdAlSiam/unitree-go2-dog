from __future__ import annotations

import logging
import time
from typing import Iterable

from .contracts import Activity, TickContext


class PipelineRunner:
    def __init__(self, activities: Iterable[Activity], tick_hz: float = 1.0) -> None:
        if tick_hz <= 0:
            raise ValueError("tick_hz must be > 0")
        self._activities = list(activities)
        self._tick_hz = tick_hz
        self._tick_period = 1.0 / tick_hz
        self._logger = logging.getLogger(self.__class__.__name__)

    def run(self, max_ticks: int = 10) -> None:
        if max_ticks <= 0:
            raise ValueError("max_ticks must be > 0")

        self._logger.info("Starting pipeline with %d activities", len(self._activities))
        for activity in self._activities:
            self._logger.info("Starting activity: %s", activity.name)
            activity.on_start()

        try:
            for tick in range(max_ticks):
                started = time.perf_counter()
                ctx = TickContext(tick_index=tick)
                for activity in self._activities:
                    activity.on_tick(ctx)
                elapsed = time.perf_counter() - started
                remaining = self._tick_period - elapsed
                if remaining > 0:
                    time.sleep(remaining)
        finally:
            for activity in reversed(self._activities):
                self._logger.info("Stopping activity: %s", activity.name)
                activity.on_stop()
            self._logger.info("Pipeline finished")
