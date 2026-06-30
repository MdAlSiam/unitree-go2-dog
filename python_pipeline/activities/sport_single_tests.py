from __future__ import annotations

import logging
import time

from python_pipeline.modules.speech.base import SpeechProviderBase
from python_pipeline.modules.sport.base import SportProviderBase
from python_pipeline.pipeline.contracts import TickContext


class _BaseSportSingleTestActivity:
    _POSTURE_SETTLE_S = 2.0
    _OBSERVE_S = 4.0
    _MOTION_TEST_S = 6.0
    _MOTION_COMMAND_PERIOD_S = 0.35

    name = "sport_single_test"

    def __init__(self, sport: SportProviderBase, speech: SpeechProviderBase) -> None:
        self._sport = sport
        self._speech = speech
        self._logger = logging.getLogger(self.__class__.__name__)

    def _announce(self, text: str) -> None:
        self._logger.info(text)
        self._speech.say(text)

    def _prepare_standing(self) -> None:
        self._announce("Standing up for test setup.")
        self._sport.stand_up()
        time.sleep(self._POSTURE_SETTLE_S)
        self._sport.balance_stand()
        time.sleep(0.8)

    def _observe(self, seconds: float | None = None) -> None:
        time.sleep(self._OBSERVE_S if seconds is None else max(0.0, float(seconds)))

    def _run_motion_for(self, vx: float, vy: float, vyaw: float, duration_s: float | None = None) -> None:
        end_ts = time.monotonic() + (self._MOTION_TEST_S if duration_s is None else max(0.0, duration_s))
        while time.monotonic() < end_ts:
            self._sport.move(vx, vy, vyaw)
            time.sleep(self._MOTION_COMMAND_PERIOD_S)
        self._sport.stop_move()
        self._observe(1.0)

    def _execute_test(self) -> None:
        raise NotImplementedError

    def on_start(self) -> None:
        self._speech.start()
        try:
            self._sport.start()
            self._execute_test()
        except RuntimeError as exc:
            # Some firmware/mode combinations reject advanced gestures (for example code 3104).
            self._logger.error("%s failed: %s", self.name, exc)
            self._announce(f"{self.name} failed: {exc}")

    def on_tick(self, context: TickContext) -> None:
        _ = context

    def on_stop(self) -> None:
        self._announce(f"Stopping {self.name} activity.")
        self._sport.stop()
        self._speech.stop()


class SportPrepCalibrateActivity(_BaseSportSingleTestActivity):
    name = "sport_prep_calibrate"

    def _execute_test(self) -> None:
        self._announce("Running pre test stabilization routine.")
        self._announce("Step one standing up.")
        self._sport.stand_up()
        self._observe(3.0)

        self._announce("Step two balance stand.")
        self._sport.balance_stand()
        self._observe(4.0)

        self._announce("Step three recovery stand refresh.")
        self._sport.recovery_stand()
        self._observe(4.0)

        self._announce("Step four final balance hold.")
        self._sport.balance_stand()
        self._observe(5.0)


class SportStandUpActivity(_BaseSportSingleTestActivity):
    name = "sport_stand_up"

    def _execute_test(self) -> None:
        self._announce("Testing stand up.")
        self._sport.stand_up()
        self._observe()


class SportBalanceStandActivity(_BaseSportSingleTestActivity):
    name = "sport_balance_stand"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing balance stand.")
        self._sport.balance_stand()
        self._observe()


class SportEnableStandGuardActivity(_BaseSportSingleTestActivity):
    name = "sport_enable_stand_guard"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing stand guard enable.")
        self._sport.start_stand_guard(interval_s=1.0)
        self._observe(6.0)
        self._sport.stop_stand_guard()


class SportDisableStandGuardActivity(_BaseSportSingleTestActivity):
    name = "sport_disable_stand_guard"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Enabling stand guard before disable test.")
        self._sport.start_stand_guard(interval_s=1.0)
        self._observe(2.0)
        self._announce("Testing stand guard disable.")
        self._sport.stop_stand_guard()
        self._observe()


class SportSpeedLevelActivity(_BaseSportSingleTestActivity):
    name = "sport_speed_level"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing speed level one.")
        self._sport.speed_level(1)
        self._run_motion_for(vx=0.2, vy=0.0, vyaw=0.0, duration_s=4.5)


class SportRotateLeftActivity(_BaseSportSingleTestActivity):
    name = "sport_rotate_left"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing rotate left motion.")
        self._run_motion_for(vx=0.0, vy=0.0, vyaw=0.2)


class SportForwardActivity(_BaseSportSingleTestActivity):
    name = "sport_forward"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing forward motion.")
        self._run_motion_for(vx=0.35, vy=0.0, vyaw=0.0)


class SportBackwardActivity(_BaseSportSingleTestActivity):
    name = "sport_backward"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing backward motion.")
        self._run_motion_for(vx=-0.35, vy=0.0, vyaw=0.0)


class SportRotateRightActivity(_BaseSportSingleTestActivity):
    name = "sport_rotate_right"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing rotate right motion.")
        self._run_motion_for(vx=0.0, vy=0.0, vyaw=-0.2)


class SportDampActivity(_BaseSportSingleTestActivity):
    name = "sport_damp"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing damp mode.")
        self._sport.damp()
        self._observe()


class SportRecoveryStandActivity(_BaseSportSingleTestActivity):
    name = "sport_recovery_stand"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing recovery stand.")
        self._sport.recovery_stand()
        self._observe()


class SportSitActivity(_BaseSportSingleTestActivity):
    name = "sport_sit"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing sit.")
        self._sport.sit()
        self._observe()


class SportRiseSitActivity(_BaseSportSingleTestActivity):
    name = "sport_rise_sit"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._sport.sit()
        self._observe(2.0)
        self._announce("Testing rise sit.")
        self._sport.rise_sit()
        self._observe()


class SportHelloActivity(_BaseSportSingleTestActivity):
    name = "sport_hello"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing hello gesture.")
        self._sport.hello()
        self._observe()


class SportContentActivity(_BaseSportSingleTestActivity):
    name = "sport_content"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing content pose.")
        self._sport.content()
        self._observe()


class SportHeartActivity(_BaseSportSingleTestActivity):
    name = "sport_heart"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing heart gesture.")
        self._sport.heart()
        self._observe()


class SportPoseActivity(_BaseSportSingleTestActivity):
    name = "sport_pose"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing pose gesture.")
        self._sport.pose(flag=True)
        self._observe()


class SportScrapeActivity(_BaseSportSingleTestActivity):
    name = "sport_scrape"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing scrape gesture.")
        self._sport.scrape()
        self._observe()


class SportDance1Activity(_BaseSportSingleTestActivity):
    name = "sport_dance1"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing dance sequence one.")
        self._sport.dance1()
        self._observe(8.0)


class SportDance2Activity(_BaseSportSingleTestActivity):
    name = "sport_dance2"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing dance sequence two.")
        self._sport.dance2()
        self._observe(8.0)


class SportFrontFlipActivity(_BaseSportSingleTestActivity):
    name = "sport_front_flip"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing front flip.")
        self._sport.front_flip()
        self._observe(8.0)


class SportBackFlipActivity(_BaseSportSingleTestActivity):
    name = "sport_back_flip"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing back flip.")
        self._sport.back_flip()
        self._observe(8.0)


class SportLeftFlipActivity(_BaseSportSingleTestActivity):
    name = "sport_left_flip"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing left flip.")
        self._sport.left_flip()
        self._observe(8.0)


class SportFrontJumpActivity(_BaseSportSingleTestActivity):
    name = "sport_front_jump"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing front jump.")
        self._sport.front_jump()
        self._observe()


class SportFrontPounceActivity(_BaseSportSingleTestActivity):
    name = "sport_front_pounce"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing front pounce.")
        self._sport.front_pounce()
        self._observe()


class SportHandStandActivity(_BaseSportSingleTestActivity):
    name = "sport_hand_stand"
    _HAND_STAND_HOLD_S = 30.0
    _HAND_STAND_EXIT_BURST = 5
    _HAND_STAND_EXIT_INTERVAL_S = 0.35

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing handstand pose.")
        self._sport.hand_stand(flag=True)
        self._observe(self._HAND_STAND_HOLD_S)
        self._announce("Exiting handstand pose.")
        for i in range(self._HAND_STAND_EXIT_BURST):
            self._sport.hand_stand(flag=False)
            if i + 1 < self._HAND_STAND_EXIT_BURST:
                time.sleep(self._HAND_STAND_EXIT_INTERVAL_S)

        # Some firmware builds need an explicit recovery sequence after handstand.
        self._sport.stop_move()
        self._sport.stand_up()
        self._observe(2.0)
        self._announce("Returning to stand up mode.")
        self._sport.balance_stand()
        self._observe(1.0)


class SportStretchActivity(_BaseSportSingleTestActivity):
    name = "sport_stretch"

    def _execute_test(self) -> None:
        self._prepare_standing()
        self._announce("Testing stretch.")
        self._sport.stretch()
        self._observe()