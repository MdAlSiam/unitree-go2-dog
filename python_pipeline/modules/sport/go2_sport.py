from __future__ import annotations

import ctypes
import logging
import threading
import time
from ctypes import POINTER, Structure, c_char_p, c_float, c_int
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .base import PathPoint, SportProviderBase
from python_pipeline.modules.speech.base import SpeechProviderBase


class _CPathPoint(Structure):
    _fields_ = [
        ("time_from_start", c_float),
        ("x", c_float),
        ("y", c_float),
        ("yaw", c_float),
        ("vx", c_float),
        ("vy", c_float),
        ("vyaw", c_float),
    ]


@dataclass(frozen=True)
class Go2PathPoint(PathPoint):
    pass


class Go2SportProvider(SportProviderBase):
    _MAX_LINEAR_VELOCITY = 0.5
    _MAX_YAW_RATE = 0.5
    _MOVE_COMMAND_BURST_COUNT = 5
    _MOVE_COMMAND_BURST_INTERVAL_S = 0.08
    _STOP_COMMAND_BURST_COUNT = 3
    _POSTURE_SETTLE_SECONDS = 1.5

    def __init__(
        self,
        network_interface: str = "",
        bridge_path: Path | None = None,
        speech: SpeechProviderBase | None = None,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._network_interface = network_interface
        self._bridge = self._load_bridge(bridge_path)
        self._speech = speech
        self._started = False
        self._stand_guard_thread: threading.Thread | None = None
        self._stand_guard_stop = threading.Event()
        self._last_posture_change_ts = 0.0

    def _load_bridge(self, bridge_path: Path | None) -> ctypes.CDLL:
        if bridge_path is None:
            bridge_path = Path(__file__).resolve().parents[2] / "bin" / "libgo2_sport_bridge.so"

        if not bridge_path.exists():
            raise FileNotFoundError(
                f"Go2 sport bridge library not found at {bridge_path}. Build the bridge first."
            )

        lib = ctypes.CDLL(str(bridge_path))
        lib.go2_sport_init.argtypes = [c_char_p]
        lib.go2_sport_init.restype = c_int

        lib.go2_sport_stand_up.argtypes = []
        lib.go2_sport_stand_up.restype = c_int

        lib.go2_sport_stand_down.argtypes = []
        lib.go2_sport_stand_down.restype = c_int

        lib.go2_sport_balance_stand.argtypes = []
        lib.go2_sport_balance_stand.restype = c_int

        lib.go2_sport_move.argtypes = [c_float, c_float, c_float]
        lib.go2_sport_move.restype = c_int

        lib.go2_sport_speed_level.argtypes = [c_int]
        lib.go2_sport_speed_level.restype = c_int

        lib.go2_sport_damp.argtypes = []
        lib.go2_sport_damp.restype = c_int

        lib.go2_sport_recovery_stand.argtypes = []
        lib.go2_sport_recovery_stand.restype = c_int

        lib.go2_sport_sit.argtypes = []
        lib.go2_sport_sit.restype = c_int

        lib.go2_sport_rise_sit.argtypes = []
        lib.go2_sport_rise_sit.restype = c_int

        lib.go2_sport_stop_move.argtypes = []
        lib.go2_sport_stop_move.restype = c_int

        lib.go2_sport_trajectory_follow.argtypes = [POINTER(_CPathPoint), c_int]
        lib.go2_sport_trajectory_follow.restype = c_int

        lib.go2_sport_hello.argtypes = []
        lib.go2_sport_hello.restype = c_int

        lib.go2_sport_content.argtypes = []
        lib.go2_sport_content.restype = c_int

        lib.go2_sport_heart.argtypes = []
        lib.go2_sport_heart.restype = c_int

        lib.go2_sport_pose.argtypes = [c_int]
        lib.go2_sport_pose.restype = c_int

        lib.go2_sport_scrape.argtypes = []
        lib.go2_sport_scrape.restype = c_int

        lib.go2_sport_dance1.argtypes = []
        lib.go2_sport_dance1.restype = c_int

        lib.go2_sport_dance2.argtypes = []
        lib.go2_sport_dance2.restype = c_int

        lib.go2_sport_front_flip.argtypes = []
        lib.go2_sport_front_flip.restype = c_int

        lib.go2_sport_back_flip.argtypes = []
        lib.go2_sport_back_flip.restype = c_int

        lib.go2_sport_left_flip.argtypes = []
        lib.go2_sport_left_flip.restype = c_int

        lib.go2_sport_front_jump.argtypes = []
        lib.go2_sport_front_jump.restype = c_int

        lib.go2_sport_front_pounce.argtypes = []
        lib.go2_sport_front_pounce.restype = c_int

        lib.go2_sport_hand_stand.argtypes = [c_int]
        lib.go2_sport_hand_stand.restype = c_int

        lib.go2_sport_stretch.argtypes = []
        lib.go2_sport_stretch.restype = c_int

        lib.go2_sport_shutdown.argtypes = []
        lib.go2_sport_shutdown.restype = None

        return lib

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError("Sport provider not started")

    def _call(self, api_name: str, ret_code: int) -> None:
        if ret_code != 0:
            raise RuntimeError(f"{api_name} failed with code {ret_code}")

    def _notify(self, message: str) -> None:
        if self._speech is None:
            return

        try:
            self._speech.say(message)
        except Exception as exc:  # pragma: no cover - speech should not block motion
            self._logger.warning("Speech notification failed: %s", exc)

    def _disable_guard_for_action(self, action_name: str) -> None:
        if self._stand_guard_thread is not None:
            self._logger.info("Disabling stand guard before '%s' action", action_name)
            self.stop_stand_guard()

    def _stand_guard_loop(self, interval_s: float) -> None:
        while not self._stand_guard_stop.wait(interval_s):
            if not self._started:
                return

            try:
                self._call("go2_sport_balance_stand", self._bridge.go2_sport_balance_stand())
            except Exception as exc:  # pragma: no cover - best effort safety loop
                self._logger.warning("Stand guard refresh failed: %s", exc)

    def start_stand_guard(self, interval_s: float = 1.0) -> None:
        self._ensure_started()
        if interval_s <= 0:
            raise ValueError("interval_s must be > 0")

        self.stop_stand_guard()
        self._stand_guard_stop.clear()
        self._stand_guard_thread = threading.Thread(
            target=self._stand_guard_loop,
            args=(float(interval_s),),
            name="go2-stand-guard",
            daemon=True,
        )
        self._stand_guard_thread.start()
        self._logger.info("Stand guard started (interval_s=%.2f)", interval_s)
        self._notify("Stand guard enabled.")

    def stop_stand_guard(self) -> None:
        if self._stand_guard_thread is None:
            return

        self._stand_guard_stop.set()
        self._stand_guard_thread.join(timeout=2.0)
        self._stand_guard_thread = None
        self._logger.info("Stand guard stopped")
        self._notify("Stand guard disabled.")

    def start(self) -> None:
        if self._started:
            return

        encoded_if = self._network_interface.encode("utf-8")
        ret = self._bridge.go2_sport_init(c_char_p(encoded_if))
        self._call("go2_sport_init", ret)
        self._started = True
        self._logger.info("Go2 sport provider started")
        self._notify("Sport control ready.")

    def stand_up(self) -> None:
        self._ensure_started()
        self._call("go2_sport_stand_up", self._bridge.go2_sport_stand_up())
        self._last_posture_change_ts = time.monotonic()
        self._notify("Standing up.")

    def stand_down(self) -> None:
        self._ensure_started()
        self._call("go2_sport_stand_down", self._bridge.go2_sport_stand_down())
        self._last_posture_change_ts = time.monotonic()
        self._notify("Standing down.")

    def balance_stand(self) -> None:
        self._ensure_started()
        self._call("go2_sport_balance_stand", self._bridge.go2_sport_balance_stand())
        self._last_posture_change_ts = time.monotonic()
        self._notify("Balance stand.")

    def speed_level(self, level: int) -> None:
        self._ensure_started()
        self._call("go2_sport_speed_level", self._bridge.go2_sport_speed_level(c_int(int(level))))

    def move(self, vx: float, vy: float, vyaw: float) -> None:
        self._ensure_started()
        self._disable_guard_for_action("move")

        since_posture = time.monotonic() - self._last_posture_change_ts
        if self._last_posture_change_ts > 0 and since_posture < self._POSTURE_SETTLE_SECONDS:
            time.sleep(self._POSTURE_SETTLE_SECONDS - since_posture)

        # Prepare locomotion mode before sending velocity commands.
        self._call("go2_sport_balance_stand", self._bridge.go2_sport_balance_stand())
        self.speed_level(1)

        clamped_vx = max(-self._MAX_LINEAR_VELOCITY, min(self._MAX_LINEAR_VELOCITY, float(vx)))
        clamped_vy = max(-self._MAX_LINEAR_VELOCITY, min(self._MAX_LINEAR_VELOCITY, float(vy)))
        clamped_vyaw = max(-self._MAX_YAW_RATE, min(self._MAX_YAW_RATE, float(vyaw)))

        if (clamped_vx, clamped_vy, clamped_vyaw) != (float(vx), float(vy), float(vyaw)):
            self._logger.warning(
                "Clamped move command from (vx=%s, vy=%s, vyaw=%s) to (vx=%s, vy=%s, vyaw=%s)",
                vx,
                vy,
                vyaw,
                clamped_vx,
                clamped_vy,
                clamped_vyaw,
            )

        for i in range(self._MOVE_COMMAND_BURST_COUNT):
            self._call(
                "go2_sport_move",
                self._bridge.go2_sport_move(
                    c_float(clamped_vx), c_float(clamped_vy), c_float(clamped_vyaw)
                ),
            )
            if i + 1 < self._MOVE_COMMAND_BURST_COUNT:
                time.sleep(self._MOVE_COMMAND_BURST_INTERVAL_S)

        self._notify(f"Moving with vx {clamped_vx}, vy {clamped_vy}, vyaw {clamped_vyaw}.")

    def damp(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("damp")
        self._call("go2_sport_damp", self._bridge.go2_sport_damp())
        self._notify("Damp mode.")

    def recovery_stand(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("recovery_stand")
        self._call("go2_sport_recovery_stand", self._bridge.go2_sport_recovery_stand())
        self._last_posture_change_ts = time.monotonic()
        self._notify("Recovery stand.")

    def sit(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("sit")
        self._call("go2_sport_sit", self._bridge.go2_sport_sit())
        self._last_posture_change_ts = time.monotonic()
        self._notify("Sitting.")

    def rise_sit(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("rise_sit")
        self._call("go2_sport_rise_sit", self._bridge.go2_sport_rise_sit())
        self._last_posture_change_ts = time.monotonic()
        self._notify("Rising from sit.")

    def stop_move(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("stop_move")
        for i in range(self._STOP_COMMAND_BURST_COUNT):
            self._call("go2_sport_stop_move", self._bridge.go2_sport_stop_move())
            if i + 1 < self._STOP_COMMAND_BURST_COUNT:
                time.sleep(self._MOVE_COMMAND_BURST_INTERVAL_S)
        self._notify("Stopping move.")

    def trajectory_follow(self, points: Sequence[PathPoint]) -> None:
        self._ensure_started()
        self._disable_guard_for_action("trajectory_follow")
        if not points:
            raise ValueError("trajectory points must not be empty")

        c_points = (_CPathPoint * len(points))(
            *[
                _CPathPoint(
                    time_from_start=float(p.time_from_start),
                    x=float(p.x),
                    y=float(p.y),
                    yaw=float(p.yaw),
                    vx=float(p.vx),
                    vy=float(p.vy),
                    vyaw=float(p.vyaw),
                )
                for p in points
            ]
        )
        self._call(
            "go2_sport_trajectory_follow",
            self._bridge.go2_sport_trajectory_follow(c_points, c_int(len(points))),
        )
        self._notify("Following trajectory.")

    def stop(self) -> None:
        if not self._started:
            return

        self.stop_stand_guard()

        # Best-effort command neutralization before tearing down the SDK client.
        try:
            for _ in range(self._STOP_COMMAND_BURST_COUNT):
                self._bridge.go2_sport_stop_move()
                time.sleep(self._MOVE_COMMAND_BURST_INTERVAL_S)
        except Exception as exc:
            self._logger.warning("Best-effort stop_move during shutdown failed: %s", exc)

        self._bridge.go2_sport_shutdown()
        self._started = False
        self._logger.info("Go2 sport provider stopped")
        self._notify("Sport control stopped.")

    def hello(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("hello")
        self._call("go2_sport_hello", self._bridge.go2_sport_hello())
        self._notify("Hello gesture.")

    def content(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("content")
        self._call("go2_sport_content", self._bridge.go2_sport_content())
        self._notify("Content pose.")

    def heart(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("heart")
        self._call("go2_sport_heart", self._bridge.go2_sport_heart())
        self._notify("Heart gesture.")

    def pose(self, flag: bool = True) -> None:
        self._ensure_started()
        self._disable_guard_for_action("pose")
        self._call("go2_sport_pose", self._bridge.go2_sport_pose(c_int(1 if flag else 0)))
        self._notify("Pose gesture.")

    def scrape(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("scrape")
        self._call("go2_sport_scrape", self._bridge.go2_sport_scrape())
        self._notify("Scrape gesture.")

    def dance1(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("dance1")
        self._call("go2_sport_dance1", self._bridge.go2_sport_dance1())
        self._notify("Dance sequence 1.")

    def dance2(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("dance2")
        self._call("go2_sport_dance2", self._bridge.go2_sport_dance2())
        self._notify("Dance sequence 2.")

    def front_flip(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("front_flip")
        self._call("go2_sport_front_flip", self._bridge.go2_sport_front_flip())
        self._notify("Front flip.")

    def back_flip(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("back_flip")
        self._call("go2_sport_back_flip", self._bridge.go2_sport_back_flip())
        self._notify("Back flip.")

    def left_flip(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("left_flip")
        self._call("go2_sport_left_flip", self._bridge.go2_sport_left_flip())
        self._notify("Left flip.")

    def front_jump(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("front_jump")
        self._call("go2_sport_front_jump", self._bridge.go2_sport_front_jump())
        self._notify("Front jump.")

    def front_pounce(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("front_pounce")
        self._call("go2_sport_front_pounce", self._bridge.go2_sport_front_pounce())
        self._notify("Front pounce.")

    def hand_stand(self, flag: bool = True) -> None:
        self._ensure_started()
        self._disable_guard_for_action("hand_stand")
        self._call("go2_sport_hand_stand", self._bridge.go2_sport_hand_stand(c_int(1 if flag else 0)))
        self._notify("Handstand pose.")

    def stretch(self) -> None:
        self._ensure_started()
        self._disable_guard_for_action("stretch")
        self._call("go2_sport_stretch", self._bridge.go2_sport_stretch())
        self._notify("Stretch.")
