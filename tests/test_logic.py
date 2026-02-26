from invoa_keyboard.logic import label_for_group, split_group, split_into_groups


def test_split_group_even():
    left, right = split_group(["A", "B", "C", "D"])
    assert left == ["A", "B"]
    assert right == ["C", "D"]


def test_split_group_odd():
    left, right = split_group(["A", "B", "C", "D", "E"])
    assert left == ["A", "B", "C"]
    assert right == ["D", "E"]


def test_label_for_group():
    assert label_for_group(["A"]) == "A"
    assert label_for_group(["A", "B", "C"]) == "A·C"


def test_split_into_groups_balanced() -> None:
    groups = split_into_groups(["A", "B", "C", "D", "E", "F", "G"], 3)
    assert groups == [["A", "B", "C"], ["D", "E"], ["F", "G"]]


def test_split_into_groups_for_multiple_counts() -> None:
    letters = [chr(code) for code in range(ord("A"), ord("J") + 1)]
    assert split_into_groups(letters, 2) == [["A", "B", "C", "D", "E"], ["F", "G", "H", "I", "J"]]
    assert split_into_groups(letters, 4) == [["A", "B", "C"], ["D", "E", "F"], ["G", "H"], ["I", "J"]]
    assert split_into_groups(letters, 5) == [["A", "B"], ["C", "D"], ["E", "F"], ["G", "H"], ["I", "J"]]
    assert split_into_groups(letters, 10) == [
        ["A"],
        ["B"],
        ["C"],
        ["D"],
        ["E"],
        ["F"],
        ["G"],
        ["H"],
        ["I"],
        ["J"],
    ]


def test_split_into_groups_clamped_range() -> None:
    groups_low = split_into_groups(["A", "B", "C", "D"], 1)
    groups_high = split_into_groups(["A", "B", "C"], 99)
    assert groups_low == [["A", "B"], ["C", "D"]]
    assert groups_high == [["A"], ["B"], ["C"]]
