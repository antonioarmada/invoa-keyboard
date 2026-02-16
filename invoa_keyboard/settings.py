from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from platformdirs import user_config_path


@dataclass
class Settings:
    long_click_ms: int = 2000
    font_scale: float = 1.0
    colors: dict[str, str] | None = None
    layout: str = "A-Z"
    output_mode: str = "global"

    def resolved_colors(self) -> dict[str, str]:
        defaults = {
            "bg": "#000000",
            "fg": "#FFFFFF",
            "hover": "#333333",
            "highlight": "#FFD400",
            "left_bg": "#00B7FF",
            "right_bg": "#FF8A00",
        }
        if not self.colors:
            return defaults
        merged = defaults.copy()
        merged.update({k: v for k, v in self.colors.items() if isinstance(v, str)})
        return merged


def default_settings() -> Settings:
    return Settings(
        colors={
            "bg": "#000000",
            "fg": "#FFFFFF",
            "hover": "#333333",
            "highlight": "#FFD400",
            "left_bg": "#00B7FF",
            "right_bg": "#FF8A00",
        }
    )


def settings_path() -> Path:
    return user_config_path("InvoaKeyboard") / "settings.json"


def load_settings(config_path: str | None = None) -> Settings:
    path = Path(config_path) if config_path else settings_path()
    defaults = default_settings()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        save_settings(defaults, path)
        return defaults

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return defaults

    return Settings(
        long_click_ms=int(raw.get("long_click_ms", defaults.long_click_ms)),
        font_scale=float(raw.get("font_scale", defaults.font_scale)),
        colors=raw.get("colors", defaults.colors),
        layout=str(raw.get("layout", defaults.layout)),
        output_mode=str(raw.get("output_mode", defaults.output_mode)),
    )


def save_settings(settings: Settings, path: Path | None = None) -> None:
    target = path or settings_path()
    payload: dict[str, Any] = {
        "long_click_ms": settings.long_click_ms,
        "font_scale": settings.font_scale,
        "colors": settings.colors or {},
        "layout": settings.layout,
        "output_mode": settings.output_mode,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
