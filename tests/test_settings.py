from __future__ import annotations

from pathlib import Path

from invoa_keyboard.settings import default_settings, load_settings


def test_creates_default_yaml_if_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yml"

    settings = load_settings(str(config_path))

    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")
    assert "# Version del esquema de configuracion" in content
    assert "group_count: 2" in content
    assert "left_bg" not in content
    assert "right_bg" not in content
    defaults = default_settings()
    assert settings.interaction.group_count == 2
    assert settings.interaction.long_click_ms == defaults.interaction.long_click_ms
    assert settings.ui.colors["bg"] == defaults.ui.colors["bg"]


def test_generated_template_can_be_reloaded(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yml"
    load_settings(str(config_path))

    settings = load_settings(str(config_path))

    assert settings.config_version == 1
    assert settings.ui.colors["bg"] == "#000000"


def test_loads_valid_yaml_with_nested_sections(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
config_version: 2
app:
  language: "es"
  layout: "A-Z"
interaction:
  group_count: 5
  long_click_ms: 1800
  undo_on_long_click: false
  min_long_click_ms: 700
  max_long_click_ms: 2200
ui:
  font_scale: 1.3
  show_alphabet_strip: false
  show_actions:
    backspace: false
    send: true
    speak: false
  colors:
    bg: "#112233"
    fg: "#F0F0F0"
typing:
  trim_before_send: false
  clear_after_send: false
  max_visible_blocks: 250
output:
  enabled: false
  mode: "global"
speech:
  enabled: false
  auto_detect_engine: true
  engine: "system"
  voice: null
  rate: 1.2
window:
  start_fullscreen: true
  start_minimized: false
  always_on_top: false
  on_top_refresh_ms: 500
  frameless: true
  ignore_focus: true
  movable: false
  resizable: false
accessibility:
  show_macos_permission_prompt: false
experimental:
  profiles_enabled: true
  telemetry_enabled: true
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(str(config_path))

    assert settings.config_version == 2
    assert settings.interaction.group_count == 5
    assert settings.interaction.long_click_ms == 1800
    assert settings.interaction.undo_on_long_click is False
    assert settings.ui.font_scale == 1.3
    assert settings.ui.show_alphabet_strip is False
    assert settings.ui.show_actions.backspace is False
    assert settings.ui.show_actions.send is True
    assert settings.ui.show_actions.speak is False
    assert settings.ui.colors["bg"] == "#112233"
    assert settings.typing.clear_after_send is False
    assert settings.output.enabled is False
    assert settings.speech.enabled is False
    assert settings.window.start_fullscreen is True
    assert settings.window.movable is False
    assert settings.accessibility.show_macos_permission_prompt is False
    assert settings.experimental.profiles_enabled is True


def test_invalid_yaml_falls_back_and_rewrites_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text("invalid: [", encoding="utf-8")

    settings = load_settings(str(config_path))

    defaults = default_settings()
    assert settings.ui.font_scale == defaults.ui.font_scale
    rewritten = config_path.read_text(encoding="utf-8")
    assert "config_version: 1" in rewritten
    assert "# Version del esquema de configuracion" in rewritten


def test_clamps_and_validation_rules(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
interaction:
  group_count: 99
  min_long_click_ms: 1000
  max_long_click_ms: 1200
  long_click_ms: 9999
ui:
  font_scale: 9.0
  colors:
    bg: "not-a-color"
    left_bg: "#00B7FF"
window:
  on_top_refresh_ms: 10
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(str(config_path))

    assert settings.interaction.group_count == 10
    assert settings.interaction.long_click_ms == 1200
    assert settings.ui.font_scale == 2.5
    assert settings.ui.colors["bg"] == "#000000"
    assert "left_bg" not in settings.ui.colors
    assert settings.window.on_top_refresh_ms == 250


def test_group_count_clamps_low(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
interaction:
  group_count: 0
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(str(config_path))

    assert settings.interaction.group_count == 2


def test_toggles_are_applied(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        """
ui:
  show_alphabet_strip: false
  show_actions:
    backspace: false
    send: false
    speak: true
typing:
  trim_before_send: false
  clear_after_send: false
output:
  enabled: false
speech:
  enabled: false
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(str(config_path))

    assert settings.ui.show_alphabet_strip is False
    assert settings.ui.show_actions.backspace is False
    assert settings.ui.show_actions.send is False
    assert settings.ui.show_actions.speak is True
    assert settings.typing.trim_before_send is False
    assert settings.typing.clear_after_send is False
    assert settings.output.enabled is False
    assert settings.speech.enabled is False
