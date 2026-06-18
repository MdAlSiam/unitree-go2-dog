from __future__ import annotations

import logging
from pathlib import Path

from python_pipeline.modules.camera.base import CameraProviderBase
from python_pipeline.modules.speech.base import SpeechProviderBase
from python_pipeline.pipeline.contracts import TickContext


class SeeAndSayActivity:
    name = "see_and_say"

    def __init__(
        self,
        camera: CameraProviderBase,
        speech: SpeechProviderBase,
        poll_every_ticks: int = 1,
        output_dir: Path | None = None,
    ) -> None:
        self._camera = camera
        self._speech = speech
        self._poll_every_ticks = max(1, poll_every_ticks)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._output_dir = output_dir or (Path(__file__).resolve().parents[1] / "output")

    def on_start(self) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._camera.start()
        self._speech.start()
        self._speech.say("Now I can see you.")

    def on_tick(self, context: TickContext) -> None:
        if context.tick_index % self._poll_every_ticks != 0:
            return

        frame = self._camera.read()
        if frame is None:
            self._logger.info("No frame available on tick %d", context.tick_index)
            return

        # image_path = self._output_dir / f"frame_{context.tick_index:04d}.jpg"
        image_path = self._output_dir / f"frame_live.jpg"
        image_path.write_bytes(frame.data)
        self._logger.info(
            "Saved frame tick=%d size=%d path=%s",
            context.tick_index,
            len(frame.data),
            image_path,
        )
        # self._speech.say(f"Hey")

    def on_stop(self) -> None:
        self._speech.say("See you again later.")
        self._speech.stop()
        self._camera.stop()
