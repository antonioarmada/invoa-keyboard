from __future__ import annotations

import platform
import subprocess
import threading


class SpeechOutput:
    def speak(self, text: str, loud: bool = False) -> None:
        text = text.strip()
        if not text:
            return
        system = platform.system().lower()
        if system == "darwin":
            if loud:
                self._run_async(["say", "-r", "220", text])
            else:
                self._run_async(["say", text])
            return
        if system == "windows":
            volume = 100 if loud else 80
            rate = 1 if loud else 0
            command = (
                "Add-Type -AssemblyName System.Speech;"
                "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                f"$speak.Volume={volume};"
                f"$speak.Rate={rate};"
                "$speak.Speak([Console]::In.ReadToEnd());"
            )
            self._run_async(["powershell", "-Command", command], text)
            return
        if system == "linux":
            amplitude = "200" if loud else "120"
            self._run_async(["espeak", "-a", amplitude, text])
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
