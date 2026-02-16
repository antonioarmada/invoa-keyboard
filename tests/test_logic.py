from invoa_keyboard.logic import label_for_group, split_group


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
