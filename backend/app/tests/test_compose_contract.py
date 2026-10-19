import subprocess
from pathlib import Path


def test_compose_declares_required_services():
    project_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        ["docker", "compose", "config", "--services"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    required_services = {"db", "redis", "minio", "backend", "worker", "frontend"}
    assert required_services <= set(result.stdout.splitlines())
