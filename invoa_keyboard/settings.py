from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_COLORS: dict[str, str] = {
    "bg": "#000000",
    "fg": "#FFFFFF",
    "hover": "#333333",
    "highlight": "#FFD400",
}

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
INT_RE = re.compile(r"^-?[0-9]+$")
FLOAT_RE = re.compile(r"^-?[0-9]+\.[0-9]+$")

DEFAULT_SETTINGS_TEMPLATE = """# Version del esquema de configuracion para futuras migraciones
config_version: 1

app:
  # Idioma de la interfaz (actualmente informativo)
  language: "es"
  # Distribucion de letras (hoy: A-Z)
  layout: "A-Z"

interaction:
  # Cantidad de grupos por nivel de seleccion (2 a 10)
  group_count: 2
  # Tiempo (ms) para considerar click largo (deshacer)
  long_click_ms: 2000
  # Habilita deshacer con click largo
  undo_on_long_click: true
  # Limite minimo permitido para click largo
  min_long_click_ms: 500
  # Limite maximo permitido para click largo
  max_long_click_ms: 5000

ui:
  # Escala general de texto y controles
  font_scale: 1.0
  # Muestra la tira del alfabeto resaltada
  show_alphabet_strip: true
  show_actions:
    # Mostrar boton borrar ultimo caracter
    backspace: true
    # Mostrar boton enviar al sistema
    send: true
    # Mostrar boton de voz (TTS)
    speak: true
  colors:
    # Fondo principal
    bg: "#000000"
    # Color principal de texto/bordes
    fg: "#FFFFFF"
    # Color hover en botones
    hover: "#333333"
    # Color de resaltado general
    highlight: "#FFD400"

typing:
  # Quitar espacios al inicio/fin antes de enviar
  trim_before_send: true
  # Limpiar buffer luego de enviar
  clear_after_send: true
  # Bloques maximos visibles en el visor
  max_visible_blocks: 500

output:
  # Habilita escritura global al sistema operativo
  enabled: true
  # Modo de salida (global hoy; otros a futuro)
  mode: "global"

speech:
  # Habilita sintesis de voz
  enabled: true
  # Detecta automaticamente motor del SO
  auto_detect_engine: true
  # Motor de voz (system por defecto)
  engine: "system"
  # Voz especifica (null = por defecto del sistema)
  voice: null
  # Velocidad de habla (1.0 normal)
  rate: 1.0

window:
  # Iniciar en pantalla completa
  start_fullscreen: false
  # Iniciar minimizado (modo burbuja)
  start_minimized: false
  # Mantener siempre encima de otras ventanas
  always_on_top: true
  # Intervalo (ms) para reforzar always_on_top
  on_top_refresh_ms: 1500
  # Ventana sin bordes del sistema
  frameless: true
  # No tomar foco del teclado al mostrarse
  ignore_focus: true
  # Permitir mover ventana
  movable: true
  # Permitir redimensionar ventana
  resizable: true

accessibility:
  # Mostrar aviso en macOS si faltan permisos
  show_macos_permission_prompt: true

experimental:
  # Perfiles de configuracion (futuro)
  profiles_enabled: false
  # Telemetria (futuro)
  telemetry_enabled: false
"""


@dataclass
class AppSettings:
    language: str = "es"
    layout: str = "A-Z"


@dataclass
class InteractionSettings:
    group_count: int = 2
    long_click_ms: int = 2000
    undo_on_long_click: bool = True
    min_long_click_ms: int = 500
    max_long_click_ms: int = 5000


@dataclass
class UIActionSettings:
    backspace: bool = True
    send: bool = True
    speak: bool = True


@dataclass
class UISettings:
    font_scale: float = 1.0
    show_alphabet_strip: bool = True
    show_actions: UIActionSettings = field(default_factory=UIActionSettings)
    colors: dict[str, str] = field(default_factory=lambda: DEFAULT_COLORS.copy())


@dataclass
class TypingSettings:
    trim_before_send: bool = True
    clear_after_send: bool = True
    max_visible_blocks: int = 500


@dataclass
class OutputSettings:
    enabled: bool = True
    mode: str = "global"


@dataclass
class SpeechSettings:
    enabled: bool = True
    auto_detect_engine: bool = True
    engine: str = "system"
    voice: str | None = None
    rate: float = 1.0


@dataclass
class WindowSettings:
    start_fullscreen: bool = False
    start_minimized: bool = False
    always_on_top: bool = True
    on_top_refresh_ms: int = 1500
    frameless: bool = True
    ignore_focus: bool = True
    movable: bool = True
    resizable: bool = True


@dataclass
class AccessibilitySettings:
    show_macos_permission_prompt: bool = True


@dataclass
class ExperimentalSettings:
    profiles_enabled: bool = False
    telemetry_enabled: bool = False


@dataclass
class Settings:
    config_version: int = 1
    app: AppSettings = field(default_factory=AppSettings)
    interaction: InteractionSettings = field(default_factory=InteractionSettings)
    ui: UISettings = field(default_factory=UISettings)
    typing: TypingSettings = field(default_factory=TypingSettings)
    output: OutputSettings = field(default_factory=OutputSettings)
    speech: SpeechSettings = field(default_factory=SpeechSettings)
    window: WindowSettings = field(default_factory=WindowSettings)
    accessibility: AccessibilitySettings = field(default_factory=AccessibilitySettings)
    experimental: ExperimentalSettings = field(default_factory=ExperimentalSettings)

    def resolved_colors(self) -> dict[str, str]:
        merged = DEFAULT_COLORS.copy()
        merged.update({k: v for k, v in self.ui.colors.items() if isinstance(v, str)})
        return merged


def default_settings() -> Settings:
    return Settings(
        config_version=1,
        app=AppSettings(),
        interaction=InteractionSettings(),
        ui=UISettings(show_actions=UIActionSettings(), colors=DEFAULT_COLORS.copy()),
        typing=TypingSettings(),
        output=OutputSettings(),
        speech=SpeechSettings(),
        window=WindowSettings(),
        accessibility=AccessibilitySettings(),
        experimental=ExperimentalSettings(),
    )


def settings_path() -> Path:
    return PROJECT_ROOT / "settings.yml"


def _to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _clamp_float(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _section(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if isinstance(value, dict):
        return value
    if value is not None:
        logger.warning("Settings section '%s' ignored because it is not a map", key)
    return {}


def _warn_unknown_keys(section_name: str, raw: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(raw.keys()) - allowed)
    for key in unknown:
        logger.warning("Unknown settings key: %s.%s", section_name, key)


def _validate_colors(raw_colors: dict[str, Any], defaults: dict[str, str]) -> dict[str, str]:
    merged = defaults.copy()
    for key, value in raw_colors.items():
        if key not in defaults:
            logger.warning("Unknown settings key: ui.colors.%s", key)
            continue
        if isinstance(value, str) and HEX_COLOR_RE.fullmatch(value):
            merged[key] = value
        else:
            logger.warning("Invalid color for ui.colors.%s, using default", key)
    return merged


def _settings_to_dict(settings: Settings) -> dict[str, Any]:
    app = settings.app
    interaction = settings.interaction
    ui = settings.ui
    actions = ui.show_actions
    typing = settings.typing
    output = settings.output
    speech = settings.speech
    window = settings.window
    accessibility = settings.accessibility
    experimental = settings.experimental

    return {
        "config_version": settings.config_version,
        "app": {
            "language": app.language,
            "layout": app.layout,
        },
        "interaction": {
            "group_count": interaction.group_count,
            "long_click_ms": interaction.long_click_ms,
            "undo_on_long_click": interaction.undo_on_long_click,
            "min_long_click_ms": interaction.min_long_click_ms,
            "max_long_click_ms": interaction.max_long_click_ms,
        },
        "ui": {
            "font_scale": ui.font_scale,
            "show_alphabet_strip": ui.show_alphabet_strip,
            "show_actions": {
                "backspace": actions.backspace,
                "send": actions.send,
                "speak": actions.speak,
            },
            "colors": settings.resolved_colors(),
        },
        "typing": {
            "trim_before_send": typing.trim_before_send,
            "clear_after_send": typing.clear_after_send,
            "max_visible_blocks": typing.max_visible_blocks,
        },
        "output": {
            "enabled": output.enabled,
            "mode": output.mode,
        },
        "speech": {
            "enabled": speech.enabled,
            "auto_detect_engine": speech.auto_detect_engine,
            "engine": speech.engine,
            "voice": speech.voice,
            "rate": speech.rate,
        },
        "window": {
            "start_fullscreen": window.start_fullscreen,
            "start_minimized": window.start_minimized,
            "always_on_top": window.always_on_top,
            "on_top_refresh_ms": window.on_top_refresh_ms,
            "frameless": window.frameless,
            "ignore_focus": window.ignore_focus,
            "movable": window.movable,
            "resizable": window.resizable,
        },
        "accessibility": {
            "show_macos_permission_prompt": accessibility.show_macos_permission_prompt,
        },
        "experimental": {
            "profiles_enabled": experimental.profiles_enabled,
            "telemetry_enabled": experimental.telemetry_enabled,
        },
    }


def _strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    chars: list[str] = []
    for ch in value:
        if escaped:
            chars.append(ch)
            escaped = False
            continue
        if ch == "\\":
            chars.append(ch)
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            chars.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            chars.append(ch)
            continue
        if ch == "#" and not in_single and not in_double:
            break
        chars.append(ch)
    return "".join(chars).rstrip()


def _parse_scalar(value: str) -> Any:
    if value.startswith("[") or value.startswith("{"):
        raise ValueError("Unsupported YAML sequence/object inline value")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if INT_RE.fullmatch(value):
        return int(value)
    if FLOAT_RE.fullmatch(value):
        return float(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        inner = value[1:-1]
        if value[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner
    return value


def _parse_yaml_map(content: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for index, raw_line in enumerate(content.splitlines(), start=1):
        if not raw_line.strip():
            continue

        line = _strip_inline_comment(raw_line)
        if not line.strip():
            continue

        if "\t" in line:
            raise ValueError(f"Tabs are not allowed in YAML indentation (line {index})")

        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError(f"Indentation must use 2 spaces (line {index})")

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"Invalid indentation structure (line {index})")

        stripped = line.strip()
        if ":" not in stripped:
            raise ValueError(f"Expected key/value mapping (line {index})")
        key, rest = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Missing key in mapping (line {index})")

        value = rest.strip()
        parent = stack[-1][1]
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
            continue

        parent[key] = _parse_scalar(value)

    return root


def _scalar_to_yaml(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _dump_yaml_map(data: dict[str, Any], indent: int = 0) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dump_yaml_map(value, indent + 2))
            continue
        lines.append(f"{prefix}{key}: {_scalar_to_yaml(value)}")
    return "\n".join(lines)


def save_settings(settings: Settings, path: Path | None = None) -> None:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _settings_to_dict(settings)
    yaml_text = _dump_yaml_map(payload) + "\n"
    target.write_text(yaml_text, encoding="utf-8")


def _write_default_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_SETTINGS_TEMPLATE, encoding="utf-8")


def load_settings(config_path: str | None = None) -> Settings:
    path = Path(config_path) if config_path else settings_path()
    defaults = default_settings()

    if not path.exists():
        _write_default_template(path)
        return defaults

    try:
        parsed = _parse_yaml_map(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _write_default_template(path)
        return defaults

    if not isinstance(parsed, dict):
        _write_default_template(path)
        return defaults

    raw: dict[str, Any] = parsed
    _warn_unknown_keys(
        "root",
        raw,
        {
            "config_version",
            "app",
            "interaction",
            "ui",
            "typing",
            "output",
            "speech",
            "window",
            "accessibility",
            "experimental",
        },
    )

    app_raw = _section(raw, "app")
    _warn_unknown_keys("app", app_raw, {"language", "layout"})
    app = AppSettings(
        language=str(app_raw.get("language", defaults.app.language)),
        layout=str(app_raw.get("layout", defaults.app.layout)),
    )

    interaction_raw = _section(raw, "interaction")
    _warn_unknown_keys(
        "interaction",
        interaction_raw,
        {"group_count", "long_click_ms", "undo_on_long_click", "min_long_click_ms", "max_long_click_ms"},
    )
    group_count = _clamp_int(
        _to_int(interaction_raw.get("group_count", defaults.interaction.group_count), defaults.interaction.group_count),
        2,
        10,
    )
    min_long_click_ms = _to_int(
        interaction_raw.get("min_long_click_ms", defaults.interaction.min_long_click_ms),
        defaults.interaction.min_long_click_ms,
    )
    min_long_click_ms = max(1, min_long_click_ms)
    max_long_click_ms = _to_int(
        interaction_raw.get("max_long_click_ms", defaults.interaction.max_long_click_ms),
        defaults.interaction.max_long_click_ms,
    )
    max_long_click_ms = max(min_long_click_ms, max_long_click_ms)
    long_click_ms = _to_int(
        interaction_raw.get("long_click_ms", defaults.interaction.long_click_ms),
        defaults.interaction.long_click_ms,
    )
    long_click_ms = _clamp_int(long_click_ms, min_long_click_ms, max_long_click_ms)
    interaction = InteractionSettings(
        group_count=group_count,
        long_click_ms=long_click_ms,
        undo_on_long_click=_to_bool(
            interaction_raw.get("undo_on_long_click", defaults.interaction.undo_on_long_click),
            defaults.interaction.undo_on_long_click,
        ),
        min_long_click_ms=min_long_click_ms,
        max_long_click_ms=max_long_click_ms,
    )

    ui_raw = _section(raw, "ui")
    _warn_unknown_keys("ui", ui_raw, {"font_scale", "show_alphabet_strip", "show_actions", "colors"})
    show_actions_raw = ui_raw.get("show_actions")
    if not isinstance(show_actions_raw, dict):
        show_actions_raw = {}
    _warn_unknown_keys("ui.show_actions", show_actions_raw, {"backspace", "send", "speak"})
    default_show_actions = defaults.ui.show_actions
    show_actions = UIActionSettings(
        backspace=_to_bool(show_actions_raw.get("backspace", default_show_actions.backspace), default_show_actions.backspace),
        send=_to_bool(show_actions_raw.get("send", default_show_actions.send), default_show_actions.send),
        speak=_to_bool(show_actions_raw.get("speak", default_show_actions.speak), default_show_actions.speak),
    )

    colors_raw = ui_raw.get("colors")
    if not isinstance(colors_raw, dict):
        colors_raw = {}
    colors = _validate_colors(colors_raw, DEFAULT_COLORS)

    font_scale = _to_float(ui_raw.get("font_scale", defaults.ui.font_scale), defaults.ui.font_scale)
    font_scale = _clamp_float(font_scale, 0.5, 2.5)

    ui = UISettings(
        font_scale=font_scale,
        show_alphabet_strip=_to_bool(
            ui_raw.get("show_alphabet_strip", defaults.ui.show_alphabet_strip), defaults.ui.show_alphabet_strip
        ),
        show_actions=show_actions,
        colors=colors,
    )

    typing_raw = _section(raw, "typing")
    _warn_unknown_keys("typing", typing_raw, {"trim_before_send", "clear_after_send", "max_visible_blocks"})
    typing = TypingSettings(
        trim_before_send=_to_bool(
            typing_raw.get("trim_before_send", defaults.typing.trim_before_send), defaults.typing.trim_before_send
        ),
        clear_after_send=_to_bool(
            typing_raw.get("clear_after_send", defaults.typing.clear_after_send), defaults.typing.clear_after_send
        ),
        max_visible_blocks=max(
            1,
            _to_int(typing_raw.get("max_visible_blocks", defaults.typing.max_visible_blocks), defaults.typing.max_visible_blocks),
        ),
    )

    output_raw = _section(raw, "output")
    _warn_unknown_keys("output", output_raw, {"enabled", "mode"})
    output = OutputSettings(
        enabled=_to_bool(output_raw.get("enabled", defaults.output.enabled), defaults.output.enabled),
        mode=str(output_raw.get("mode", defaults.output.mode)),
    )

    speech_raw = _section(raw, "speech")
    _warn_unknown_keys("speech", speech_raw, {"enabled", "auto_detect_engine", "engine", "voice", "rate"})
    speech = SpeechSettings(
        enabled=_to_bool(speech_raw.get("enabled", defaults.speech.enabled), defaults.speech.enabled),
        auto_detect_engine=_to_bool(
            speech_raw.get("auto_detect_engine", defaults.speech.auto_detect_engine), defaults.speech.auto_detect_engine
        ),
        engine=str(speech_raw.get("engine", defaults.speech.engine)),
        voice=None if speech_raw.get("voice") is None else str(speech_raw.get("voice")),
        rate=_clamp_float(_to_float(speech_raw.get("rate", defaults.speech.rate), defaults.speech.rate), 0.5, 2.0),
    )

    window_raw = _section(raw, "window")
    _warn_unknown_keys(
        "window",
        window_raw,
        {
            "start_fullscreen",
            "start_minimized",
            "always_on_top",
            "on_top_refresh_ms",
            "frameless",
            "ignore_focus",
            "movable",
            "resizable",
        },
    )
    on_top_refresh_ms = _to_int(
        window_raw.get("on_top_refresh_ms", defaults.window.on_top_refresh_ms), defaults.window.on_top_refresh_ms
    )
    on_top_refresh_ms = max(250, on_top_refresh_ms)
    window = WindowSettings(
        start_fullscreen=_to_bool(
            window_raw.get("start_fullscreen", defaults.window.start_fullscreen), defaults.window.start_fullscreen
        ),
        start_minimized=_to_bool(
            window_raw.get("start_minimized", defaults.window.start_minimized), defaults.window.start_minimized
        ),
        always_on_top=_to_bool(
            window_raw.get("always_on_top", defaults.window.always_on_top), defaults.window.always_on_top
        ),
        on_top_refresh_ms=on_top_refresh_ms,
        frameless=_to_bool(window_raw.get("frameless", defaults.window.frameless), defaults.window.frameless),
        ignore_focus=_to_bool(
            window_raw.get("ignore_focus", defaults.window.ignore_focus), defaults.window.ignore_focus
        ),
        movable=_to_bool(window_raw.get("movable", defaults.window.movable), defaults.window.movable),
        resizable=_to_bool(window_raw.get("resizable", defaults.window.resizable), defaults.window.resizable),
    )

    accessibility_raw = _section(raw, "accessibility")
    _warn_unknown_keys("accessibility", accessibility_raw, {"show_macos_permission_prompt"})
    accessibility = AccessibilitySettings(
        show_macos_permission_prompt=_to_bool(
            accessibility_raw.get(
                "show_macos_permission_prompt",
                defaults.accessibility.show_macos_permission_prompt,
            ),
            defaults.accessibility.show_macos_permission_prompt,
        )
    )

    experimental_raw = _section(raw, "experimental")
    _warn_unknown_keys("experimental", experimental_raw, {"profiles_enabled", "telemetry_enabled"})
    experimental = ExperimentalSettings(
        profiles_enabled=_to_bool(
            experimental_raw.get("profiles_enabled", defaults.experimental.profiles_enabled),
            defaults.experimental.profiles_enabled,
        ),
        telemetry_enabled=_to_bool(
            experimental_raw.get("telemetry_enabled", defaults.experimental.telemetry_enabled),
            defaults.experimental.telemetry_enabled,
        ),
    )

    config_version = max(1, _to_int(raw.get("config_version", defaults.config_version), defaults.config_version))

    return Settings(
        config_version=config_version,
        app=app,
        interaction=interaction,
        ui=ui,
        typing=typing,
        output=output,
        speech=speech,
        window=window,
        accessibility=accessibility,
        experimental=experimental,
    )
