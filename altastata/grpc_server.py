import argparse
import os
import shlex
import signal
import subprocess
import sys

from .java_runtime import (
    build_grpc_subprocess_env,
    resolve_local_grpc_startup_command,
)


def _stop_process(process: subprocess.Popen, *, grace_s: float = 5.0) -> int:
    """Terminate the Java gateway process group, escalating to SIGKILL."""
    if process.poll() is not None:
        return process.returncode or 0

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        process.terminate()

    try:
        return process.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        process.kill()

    try:
        return process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        return 130


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Start AltaStata gRPC server from Python package runtime."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved startup command and exit.",
    )
    args = parser.parse_args(argv)

    command, working_dir = resolve_local_grpc_startup_command()
    if args.dry_run:
        print("cwd:", working_dir or ".")
        print("command:", shlex.join(command))
        return 0

    # Own the process group so Ctrl+C hits this Python launcher (not Java
    # directly). We then shut the whole group down cleanly.
    process = subprocess.Popen(
        command,
        cwd=working_dir,
        env=build_grpc_subprocess_env(),
        start_new_session=True,
    )
    try:
        return process.wait()
    except KeyboardInterrupt:
        return _stop_process(process)


if __name__ == "__main__":
    sys.exit(main())
