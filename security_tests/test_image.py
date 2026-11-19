from pathlib import Path

DOCKERFILE = Path(__file__).parent.parent / "Dockerfile"


def test_the_image_is_slim_and_does_not_run_as_root():
    lines = DOCKERFILE.read_text().splitlines()
    assert "slim" in next(line for line in lines if line.startswith("FROM"))
    assert any(line.startswith("USER ") and line != "USER root" for line in lines)
