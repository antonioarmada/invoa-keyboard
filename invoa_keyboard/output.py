from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OutputResult:
    ok: bool
    error: str | None = None


class GlobalKeyboardOutput:
    def __init__(self) -> None:
        try:
            from pynput.keyboard import Controller
        except Exception as exc:  # pragma: no cover - import failure is platform-specific
            self._controller = None
            self._import_error = str(exc)
        else:
            self._controller = Controller()
            self._import_error = None
        self._mac_trusted: bool | None = None

    def macos_accessibility_trusted(self) -> bool | None:
        if self._mac_trusted is not None:
            return self._mac_trusted
        try:
            import sys
            import ctypes
            from ctypes.util import find_library

            if sys.platform != "darwin":
                return None
            lib = find_library("ApplicationServices")
            if not lib:
                return None
            app_services = ctypes.cdll.LoadLibrary(lib)
            app_services.AXIsProcessTrusted.restype = ctypes.c_bool
            self._mac_trusted = bool(app_services.AXIsProcessTrusted())
            return self._mac_trusted
        except Exception:
            return None

    def send_letter(self, letter: str) -> OutputResult:
        if not self._controller:
            return OutputResult(False, self._import_error or "pynput no disponible")
        try:
            self._controller.type(letter)
        except Exception as exc:  # pragma: no cover
            return OutputResult(False, str(exc))
        return OutputResult(True, None)

    def send_text(self, text: str) -> OutputResult:
        if not text:
            return OutputResult(True, None)
        if not self._controller:
            return OutputResult(False, self._import_error or "pynput no disponible")
        try:
            self._controller.type(text)
        except Exception as exc:  # pragma: no cover
            return OutputResult(False, str(exc))
        return OutputResult(True, None)
