from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable

from python_pipeline.activities.damp import DampActivity
from python_pipeline.activities.go_motion import GoBackwardActivity, GoForwardActivity
from python_pipeline.activities.see_and_say import SeeAndSayActivity
from python_pipeline.activities.sport_single_tests import (
    SportBackwardActivity,
    SportBalanceStandActivity,
    SportBackFlipActivity,
    SportContentActivity,
    SportDampActivity,
    SportDance1Activity,
    SportDance2Activity,
    SportDisableStandGuardActivity,
    SportEnableStandGuardActivity,
    SportForwardActivity,
    SportFrontFlipActivity,
    SportFrontJumpActivity,
    SportFrontPounceActivity,
    SportHandStandActivity,
    SportHeartActivity,
    SportHelloActivity,
    SportLeftFlipActivity,
    SportPoseActivity,
    SportPrepCalibrateActivity,
    SportRecoveryStandActivity,
    SportRiseSitActivity,
    SportRotateLeftActivity,
    SportRotateRightActivity,
    SportScrapeActivity,
    SportSitActivity,
    SportSpeedLevelActivity,
    SportStandUpActivity,
    SportStretchActivity,
)
from python_pipeline.activities.sport_voice_test import SportVoiceTestActivity
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
        (
            "Sport Voice Test (All-in-One)",
            lambda: SportVoiceTestActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_prep_calibrate",
            lambda: SportPrepCalibrateActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_stand_up",
            lambda: SportStandUpActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_balance_stand",
            lambda: SportBalanceStandActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_enable_stand_guard",
            lambda: SportEnableStandGuardActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_disable_stand_guard",
            lambda: SportDisableStandGuardActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_speed_level",
            lambda: SportSpeedLevelActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_rotate_left",
            lambda: SportRotateLeftActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_forward",
            lambda: SportForwardActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_backward",
            lambda: SportBackwardActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_rotate_right",
            lambda: SportRotateRightActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_damp",
            lambda: SportDampActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_recovery_stand",
            lambda: SportRecoveryStandActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_sit",
            lambda: SportSitActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_rise_sit",
            lambda: SportRiseSitActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_hello",
            lambda: SportHelloActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_content",
            lambda: SportContentActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_heart",
            lambda: SportHeartActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_pose",
            lambda: SportPoseActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_scrape",
            lambda: SportScrapeActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_dance1",
            lambda: SportDance1Activity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_dance2",
            lambda: SportDance2Activity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_front_flip",
            lambda: SportFrontFlipActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_back_flip",
            lambda: SportBackFlipActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_left_flip",
            lambda: SportLeftFlipActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_front_jump",
            lambda: SportFrontJumpActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_front_pounce",
            lambda: SportFrontPounceActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_hand_stand",
            lambda: SportHandStandActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "sport_stretch",
            lambda: SportStretchActivity(
                sport=Go2SportProvider(
                    network_interface=settings.network_interface,
                    bridge_path=Path(__file__).resolve().parent / "bin" / "libgo2_sport_bridge.so",
                ),
                speech=speech,
            ),
        ),
        (
            "Damp",
            lambda: DampActivity(
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

    # Check for command-line activity name: python3 main.py <activity_name>
    cli_activity_name = None
    if len(sys.argv) > 1:
        cli_activity_name = sys.argv[1].lower()
        interactive_mode = False
        # Find matching activity
        for idx, (name, _) in enumerate(activity_factories):
            if name.lower() == cli_activity_name or name.lower().split()[0] == cli_activity_name:
                selected_index = idx
                selected_name, selected_factory = activity_factories[selected_index]
                logger.info("CLI activity: %s", selected_name)
                activity = selected_factory()

                runner = PipelineRunner(activities=[activity], tick_hz=settings.tick_hz)
                run_max_ticks = 1  # CLI activities are one-shot

                try:
                    runner.run(max_ticks=run_max_ticks)
                except KeyboardInterrupt:
                    logger.info("Activity interrupted")

                return 0
        
        logger.error("Unknown activity: %s", cli_activity_name)
        print(f"Unknown activity: {cli_activity_name}")
        print(f"Available activities: {', '.join(name.lower() for name, _ in activity_factories)}")
        return 1

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
        if activity.name in {"go_forward", "go_backward", "sport_voice_test", "damp"} or activity.name.startswith("sport_"):
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
