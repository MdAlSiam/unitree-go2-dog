from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable

from python_pipeline.activities.go_motion import GoBackwardActivity, GoForwardActivity
from python_pipeline.activities.see_and_say import SeeAndSayActivity
from python_pipeline.config.settings import load_settings
from python_pipeline.modules.camera.go2_camera import Go2CameraProvider
from python_pipeline.modules.speech.null_speech import NullSpeechProvider
from python_pipeline.modules.speech.system_speech import SystemSpeechProvider
from python_pipeline.modules.sport.go2_sport import Go2SportProvider
from python_pipeline.pipeline.contracts import Activity
from python_pipeline.pipeline.runner import PipelineRunner



def _prompt_activity_index(activity_names: list[str]) -> int:
    if not sys.stdin.isatty():
        return 0

    print("Select activity:")
    for idx, name in enumerate(activity_names):
        print(f"  {idx}. {name}")
    exit_index = len(activity_names)
    print(f"  {exit_index}. Exit")

    while True:
        try:
            raw = input("Enter activity number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return exit_index

        try:
            selected = int(raw)
        except ValueError:
            print("Invalid input. Enter a number.")
            continue

        if 0 <= selected <= exit_index:
            return selected

        print(f"Invalid choice. Enter a number between 0 and {exit_index}.")



def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )



def main() -> int:
    configure_logging()
    logger = logging.getLogger(__name__)
    settings = load_settings()

    if settings.speech_provider == "null":
        speech = NullSpeechProvider()
    else:
        speech = SystemSpeechProvider()

    # Build activity instances lazily so only the selected activity initializes its providers.
    activity_factories: list[tuple[str, Callable[[], Activity]]] = [
        (
            "See and Say",
            lambda: SeeAndSayActivity(
                camera=Go2CameraProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_video_bridge.so",
                ),
                speech=speech,
                poll_every_ticks=settings.camera_poll_every_ticks,
            ),
        ),
        (
            "Go Forward",
            lambda: GoForwardActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "Go Backward",
            lambda: GoBackwardActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
    ]

    activity_names = [name for name, _ in activity_factories]
    interactive_mode = sys.stdin.isatty()

    while True:
        selected_index = _prompt_activity_index(activity_names)
        if selected_index == len(activity_factories):
            logger.info("Exiting activity menu")
            break

        selected_name, selected_factory = activity_factories[selected_index]
        logger.info("Selected activity: %s", selected_name)
        activity = selected_factory()

        runner = PipelineRunner(activities=[activity], tick_hz=settings.tick_hz)
        run_max_ticks = settings.max_ticks
        if activity.name in {"go_forward", "go_backward"}:
            # These activities execute their full motion sequence in on_start().
            # One tick is enough before clean shutdown and return to the menu.
            run_max_ticks = 1

        try:
            runner.run(max_ticks=run_max_ticks)
        except KeyboardInterrupt:
            logger.info("Activity interrupted; returning to activity menu")

        # Non-interactive callers should run one selected activity and exit.
        if not interactive_mode:
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Run: PYTHONPATH=. python3 -m python_pipeline.main

"""
from python_pipeline.modules.speech.system_speech import SystemSpeechProvider
from python_pipeline.modules.sport.go2_sport import Go2SportProvider

speech = SystemSpeechProvider()
speech.start()

sport = Go2SportProvider(network_interface="", speech=speech)
sport.start()
sport.stand_up()
sport.move(0.2, 0.0, 0.0)
sport.stop_move()

sport.balance_stand()
sport.start_stand_guard(interval_s=1.0)

sport.stand_down()
sport.stop()

speech.stop()
"""
