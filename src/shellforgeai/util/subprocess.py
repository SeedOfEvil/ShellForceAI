import subprocess
import time
from dataclasses import dataclass


@dataclass
class CommandResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int


def run_command(command: list[str], timeout: int = 15) -> CommandResult:
    start = time.time()
    try:
        r = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return CommandResult(command, 127, "", f"command not found: {command[0]}", 0)
    except subprocess.TimeoutExpired:
        return CommandResult(
            command, 124, "", "command timed out", int((time.time() - start) * 1000)
        )
    return CommandResult(
        command, r.returncode, r.stdout, r.stderr, int((time.time() - start) * 1000)
    )
