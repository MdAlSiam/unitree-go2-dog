from __future__ import annotations

import logging
import sys
from pathlib import Path

from python_pipeline.activities.see_and_say import SeeAndSayActivity
from python_pipeline.config.settings import load_settings
from python_pipeline.modules.camera.go2_camera import Go2CameraProvider
from python_pipeline.modules.speech.null_speech import NullSpeechProvider
from python_pipeline.modules.speech.system_speech import SystemSpeechProvider
from python_pipeline.pipeline.runner import PipelineRunner



def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )



def main() -> int:
    configure_logging()
    settings = load_settings()

    # Python package root is python_pipeline, shared bridge binary lives in python_pipeline/bin.
    bridge_path = Path(__file__).resolve().parent / "bin" / "libgo2_video_bridge.so"

    camera = Go2CameraProvider(
        network_interface=settings.network_interface,
        bridge_path=bridge_path,
    )
    if settings.speech_provider == "null":
        speech = NullSpeechProvider()
    else:
        speech = SystemSpeechProvider()

    activity = SeeAndSayActivity(
        camera=camera,
        speech=speech,
        poll_every_ticks=settings.camera_poll_every_ticks,
    )

    runner = PipelineRunner(activities=[activity], tick_hz=settings.tick_hz)
    runner.run(max_ticks=settings.max_ticks)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Run: PYTHONPATH=. python3 -m python_pipeline.main
