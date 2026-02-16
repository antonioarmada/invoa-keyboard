from __future__ import annotations

from math import ceil

LETTERS = [chr(code) for code in range(ord("A"), ord("Z") + 1)]


def split_group(group: list[str]) -> tuple[list[str], list[str]]:
    if not group:
        return [], []
    left_size = int(ceil(len(group) / 2))
    return group[:left_size], group[left_size:]


def label_for_group(group: list[str]) -> str:
    if not group:
        return ""
    if len(group) == 1:
        return group[0]
    return f"{group[0]}-{group[-1]}"
