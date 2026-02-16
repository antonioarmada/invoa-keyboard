from __future__ import annotations

import platform
import subprocess
import threading


class SpeechOutput:
    def speak(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        system = platform.system().lower()
        if system == "darwin":
            self._run_async(["say", text])
            return
        if system == "windows":
            command = (
                "Add-Type -AssemblyName System.Speech;"
                "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "$speak.Speak([Console]::In.ReadToEnd());"
            )
            self._run_async(["powershell", "-Command", command], text)
            return
        if system == "linux":
            self._run_async(["espeak", text])
            return

    def _run_async(self, args: list[str], stdin_text: str | None = None) -> None:
        def _worker() -> None:
            try:
                if stdin_text is None:
                    subprocess.Popen(args)
                else:
                    subprocess.Popen(args, stdin=subprocess.PIPE).communicate(stdin_text.encode("utf-8"))
            except Exception:
                return

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
