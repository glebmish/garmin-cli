from garmin_cli.output import filter_fields, sanitize


def test_sanitize_strips_control_chars_in_strings():
    assert sanitize("hello\x01world\x07") == "helloworld"


def test_sanitize_preserves_tab_newline_cr():
    assert sanitize("a\tb\nc\rd") == "a\tb\nc\rd"


def test_sanitize_walks_dicts_and_lists():
    raw = {"a": "ok\x02", "b": [{"c": "x\x03"}], "n": 42}
    assert sanitize(raw) == {"a": "ok", "b": [{"c": "x"}], "n": 42}


def test_filter_fields_top_level():
    obj = {"a": 1, "b": 2, "c": 3}
    assert filter_fields(obj, ["a", "c"]) == {"a": 1, "c": 3}


def test_filter_fields_dotted_path():
    obj = {"outer": {"a": 1, "b": 2}, "x": 9}
    assert filter_fields(obj, ["outer.a", "x"]) == {"outer": {"a": 1}, "x": 9}


def test_filter_fields_descends_arrays():
    obj = {"items": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}
    assert filter_fields(obj, ["items.id"]) == {
        "items": [{"id": 1}, {"id": 2}]
    }


def test_filter_fields_missing_keys_dropped():
    assert filter_fields({"a": 1}, ["a", "missing"]) == {"a": 1}


def test_filter_fields_empty_returns_value():
    assert filter_fields({"a": 1}, []) == {"a": 1}
