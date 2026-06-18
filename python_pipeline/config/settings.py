from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineSettings:
    network_interface: str = ""
    tick_hz: float = 0.5
    max_ticks: int = 10
    camera_poll_every_ticks: int = 1
    speech_provider: str = "system"



def load_settings() -> PipelineSettings:
    network_interface = os.getenv("GO2_NETWORK_INTERFACE", "")
    tick_hz = float(os.getenv("PIPELINE_TICK_HZ", "0.5"))
    max_ticks = int(os.getenv("PIPELINE_MAX_TICKS", "10"))
    camera_poll_every_ticks = int(os.getenv("CAMERA_POLL_EVERY_TICKS", "1"))
    speech_provider = os.getenv("PIPELINE_SPEECH_PROVIDER", "system").strip().lower()

    return PipelineSettings(
        network_interface=network_interface,
        tick_hz=tick_hz,
        max_ticks=max_ticks,
        camera_poll_every_ticks=max(1, camera_poll_every_ticks),
        speech_provider=speech_provider,
    )
