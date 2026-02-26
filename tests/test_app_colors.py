from __future__ import annotations

from invoa_keyboard.app import _contrast_ratio, _hex_to_rgb, generate_group_colors


def test_generate_group_colors_count() -> None:
    colors = generate_group_colors(5, "#000000")
    assert len(colors) == 5


def test_generate_group_colors_contrast_black_bg() -> None:
    bg = _hex_to_rgb("#000000")
    colors = generate_group_colors(10, "#000000")
    assert len(colors) == 10
    for color in colors:
        ratio = _contrast_ratio(_hex_to_rgb(color), bg)
        assert ratio >= 7.0


def test_generate_group_colors_contrast_white_bg() -> None:
    bg = _hex_to_rgb("#FFFFFF")
    colors = generate_group_colors(10, "#FFFFFF")
    assert len(colors) == 10
    for color in colors:
        ratio = _contrast_ratio(_hex_to_rgb(color), bg)
        assert ratio >= 7.0
