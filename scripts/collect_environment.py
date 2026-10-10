#!/usr/bin/env python3

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TOOLS = {
    "git": ["git", "--version"],
    "docker": ["docker", "--version"],
    "node": ["node", "--version"],
    "terraform": ["terraform", "version"],
}


def get_tool_info(command):
    """Return whether a tool exists and its version output."""
    executable = shutil.which(command[0])

    if executable is None:
        return {
            "available": False,
            "version": None,
        }

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        output = (result.stdout or result.stderr).strip()

        return {
            "available": True,
            "version": output.splitlines()[0] if output else None,
            "exit_code": result.returncode,
        }

    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "available": True,
            "version": None,
            "error": str(exc),
        }


def collect_environment():
    """Collect runner environment details."""
    tools = {
        name: get_tool_info(command)
        for name, command in TOOLS.items()
    }

    docker_info = {
        "daemon_available": False,
    }

    if tools["docker"]["available"]:
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            docker_info = {
                "daemon_available": (
                    result.returncode == 0
                    and bool(result.stdout.strip())
                ),
                "server_version": result.stdout.strip() or None,
            }
        except (OSError, subprocess.TimeoutExpired):
            pass

    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "runner": {
            "name": os.getenv("RUNNER_NAME"),
            "os": os.getenv("RUNNER_OS", platform.system()),
            "architecture": os.getenv(
                "RUNNER_ARCH", platform.machine()
            ),
            "workspace": os.getenv("GITHUB_WORKSPACE", str(ROOT)),
            "temp_directory": os.getenv(
                "RUNNER_TEMP", tempfile.gettempdir()
            ),
        },
        "system": {
            "system": platform.system(),
            "release": platform.release(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
        },
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "tools": tools,
        "docker": docker_info,
    }


def main():
    output_path = ROOT / "reports" / "environment.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = collect_environment()

    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
