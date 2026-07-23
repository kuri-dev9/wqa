from parser.json_parser import JsonLeafParser


def test_nested_json_is_flattened_with_paths() -> None:
    body = {"data": {"users": [{"name": "Kim", "email": "kim@example.com"}]}}

    leaves = JsonLeafParser().parse(body)

    assert [(leaf.path, leaf.value) for leaf in leaves] == [
        ("data.users[0].name", "Kim"),
        ("data.users[0].email", "kim@example.com"),
    ]


def test_root_scalar_and_empty_containers_are_leaves() -> None:
    parser = JsonLeafParser()

    assert [(leaf.path, leaf.value) for leaf in parser.parse("hello")] == [("$", "hello")]
    assert [(leaf.path, leaf.value) for leaf in parser.parse([])] == [("$", [])]
