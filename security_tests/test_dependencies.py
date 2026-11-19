from importlib.metadata import version


def test_jinja2_is_past_its_known_vulnerabilities():
    installed = tuple(int(part) for part in version("jinja2").split("."))
    assert installed >= (3, 1, 6)
