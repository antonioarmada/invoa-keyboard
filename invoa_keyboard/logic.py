from __future__ import annotations

LETTERS = [chr(code) for code in range(ord("A"), ord("Z") + 1)]


def split_into_groups(group: list[str], group_count: int) -> list[list[str]]:
    if not group:
        return []
    effective_count = min(max(2, int(group_count)), 10, len(group))
    base_size, remainder = divmod(len(group), effective_count)
    groups: list[list[str]] = []
    start = 0
    for index in range(effective_count):
        size = base_size + (1 if index < remainder else 0)
        if size <= 0:
            continue
        end = start + size
        groups.append(group[start:end])
        start = end
    return groups


def split_group(group: list[str]) -> tuple[list[str], list[str]]:
    groups = split_into_groups(group, 2)
    if not groups:
        return [], []
    if len(groups) == 1:
        return groups[0], []
    return groups[0], groups[1]


def label_for_group(group: list[str]) -> str:
    if not group:
        return ""
    if len(group) == 1:
        return group[0]
    return f"{group[0]}·{group[-1]}"
