from __future__ import annotations

import ctypes
import logging
from ctypes import c_char_p, c_int, c_uint8, c_void_p, POINTER, byref
from pathlib import Path
from typing import Optional

from python_pipeline.pipeline.contracts import FrameSample

from .base import CameraProviderBase


class Go2CameraProvider(CameraProviderBase):
    def __init__(self, network_interface: str = "", bridge_path: Optional[Path] = None) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._network_interface = network_interface
        self._bridge = self._load_bridge(bridge_path)
        self._started = False

    def _load_bridge(self, bridge_path: Optional[Path]) -> ctypes.CDLL:
        if bridge_path is None:
            bridge_path = (
                Path(__file__).resolve().parents[2]
                / "bin"
                / "libgo2_video_bridge.so"
            )

        if not bridge_path.exists():
            raise FileNotFoundError(
                f"Go2 bridge library not found at {bridge_path}. Build the bridge first."
            )

        lib = ctypes.CDLL(str(bridge_path))
        lib.go2_video_init.argtypes = [c_char_p]
        lib.go2_video_init.restype = c_int

        lib.go2_video_get_frame.argtypes = [POINTER(c_void_p), POINTER(c_int)]
        lib.go2_video_get_frame.restype = c_int

        lib.go2_video_free_frame.argtypes = [POINTER(c_uint8)]
        lib.go2_video_free_frame.restype = None

        lib.go2_video_shutdown.argtypes = []
        lib.go2_video_shutdown.restype = None
        return lib

    def start(self) -> None:
        if self._started:
            return
        encoded_if = self._network_interface.encode("utf-8")
        ret = self._bridge.go2_video_init(c_char_p(encoded_if))
        if ret != 0:
            raise RuntimeError(f"Failed to initialize Go2 camera bridge, error code {ret}")
        self._started = True
        self._logger.info("Go2 camera provider started")

    def read(self) -> Optional[FrameSample]:
        if not self._started:
            raise RuntimeError("Camera provider not started")

        frame_ptr = c_void_p()
        frame_size = c_int()

        ret = self._bridge.go2_video_get_frame(byref(frame_ptr), byref(frame_size))
        if ret != 0:
            self._logger.warning("Camera frame read failed with code %d", ret)
            return None

        if not frame_ptr.value or frame_size.value <= 0:
            return None

        try:
            data = ctypes.string_at(frame_ptr.value, frame_size.value)
        finally:
            self._bridge.go2_video_free_frame(ctypes.cast(frame_ptr, POINTER(c_uint8)))

        return FrameSample(data=data, metadata={"size": frame_size.value})

    def stop(self) -> None:
        if not self._started:
            return
        self._bridge.go2_video_shutdown()
        self._started = False
        self._logger.info("Go2 camera provider stopped")
