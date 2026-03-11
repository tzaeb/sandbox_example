"""
Sandboxed bash for the agent.

Executes commands inside a hardened Docker container managed by
docker-compose. Uses the "long-running container + exec" pattern:

  - `docker compose up -d` starts the sandbox service once.
  - Each `execute()` call does `docker compose exec` into the running container.
  - Container is torn down on interpreter exit via `docker compose down`.
"""

import atexit
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

COMPOSE_FILE = Path(__file__).parent / "docker-compose.yml"
SERVICE_NAME = "sandbox"
WORKDIR = os.environ.get("SANDBOX_WORKDIR", "/tmp/sandbox_workspace")


class Sandbox:
    """Runs bash commands inside a docker-compose-managed sandbox container."""

    def __init__(self):
        self._running = False

    def _compose(self, *args: str, check: bool = True, **kwargs) -> subprocess.CompletedProcess:
        cmd = ["docker", "compose", "-f", str(COMPOSE_FILE)]
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=True, text=True, check=check, **kwargs)

    def _ensure_running(self):
        if self._running:
            result = self._compose("ps", "-q", SERVICE_NAME, check=False)
            if result.stdout.strip():
                return
            self._running = False

        Path(WORKDIR).mkdir(parents=True, exist_ok=True)
        self._compose("up", "-d", "--build", SERVICE_NAME)
        self._running = True
        atexit.register(self._cleanup)

    def _cleanup(self):
        if self._running:
            self._compose("down", "-t", "3", check=False)
            self._running = False

    def execute(self, command: str) -> str:
        """Execute a bash command inside the sandbox."""
        try:
            self._ensure_running()
        except subprocess.CalledProcessError as e:
            detail = e.stderr.strip() if e.stderr else str(e)
            return f"[ERROR]\nFailed to start sandbox: {detail}"
        except FileNotFoundError as e:
            return f"[ERROR]\nFailed to start sandbox: {e}"

        result = self._compose(
            "exec", "-T", SERVICE_NAME,
            "sh", "-c", command,
            check=False,
        )

        stdout = result.stdout
        stderr = result.stderr

        output = ""
        if stdout:
            output += stdout
        if stderr:
            output += f"\n[STDERR]\n{stderr}"

        return output.strip() if output.strip() else "(no output)"
