"""JVM heap defaults and local AltaStata gateway process launch.

Owns uber-jar / Console SPA discovery and ``java``/Gradle subprocess
startup so :mod:`altastata.grpc_client` stays focused on the RPC session.
"""

from __future__ import annotations

import os
import platform
import subprocess
import threading
from importlib.resources import files as package_files
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# Keep in sync with altastata-services/build.gradle and altastata-services Dockerfiles.
# Rule of thumb: container RAM >= Xmx + ~1.5 GiB for OpsExecutors thread stacks.
DEFAULT_JAVA_MEMORY_OPTS = [
    "-Xms1g",
    "-Xmx4g",
    "-XX:ThreadStackSize=256k",
]


def resolve_java_memory_opts() -> List[str]:
    """Heap/stack flags to pass on the ``java`` command line.

    Local ``pip install`` runs usually have no Java tuning env, so embed the
    defaults on the argv. When ``JAVA_TOOL_OPTIONS`` or ``JAVA_OPTS`` already
    set ``-Xmx`` (typical in Docker compose / k8s), return ``[]`` so the
    environment is the single source of truth and compose overrides work.
    """
    combined = " ".join(
        (
            os.environ.get("JAVA_TOOL_OPTIONS", ""),
            os.environ.get("JAVA_OPTS", ""),
        )
    )
    if "-Xmx" in combined:
        return []
    return list(DEFAULT_JAVA_MEMORY_OPTS)


def _bundled_data_path(*parts: str) -> Optional[Path]:
    """Absolute path to packaged data under ``altastata/``, or ``None``.

    Uses :mod:`importlib.resources` (not deprecated ``pkg_resources``). Prefer
    a durable on-disk path — the Java subprocess needs the jar/UI for its
    whole lifetime, so we avoid temporary ``as_file`` extractions.
    """
    try:
        node = package_files("altastata")
        for part in parts:
            node = node.joinpath(part)
    except ModuleNotFoundError:
        return None

    try:
        path = Path(os.fspath(node))
    except TypeError:
        import altastata as _pkg

        origin = getattr(_pkg, "__file__", None)
        if not origin:
            return None
        path = Path(origin).resolve().parent.joinpath(*parts)

    if path.exists():
        return path.resolve()
    return None


def find_bundled_grpc_uber_jar() -> Optional[str]:
    """
    Locate the bundled gateway uber jar under ``altastata/lib``.

    Preference order:
      1. ``altastata-services-*-uber.jar`` — unified gateway (Micronaut + gRPC + S3).
      2. ``altastata-grpc-*-uber.jar`` — legacy gRPC-only gateway.
    """
    jar_dir = _bundled_data_path("lib")
    if jar_dir is None or not jar_dir.is_dir():
        return None

    services = sorted(
        str(p)
        for p in jar_dir.iterdir()
        if p.name.startswith("altastata-services-") and p.name.endswith("-uber.jar")
    )
    if services:
        return services[-1]

    legacy = sorted(
        str(p)
        for p in jar_dir.iterdir()
        if p.name.startswith("altastata-grpc-") and p.name.endswith("-uber.jar")
    )
    if not legacy:
        return None
    return legacy[-1]


def grpc_main_class_for_jar(bundled_uber_jar: str) -> str:
    """Pick the right Java main class for the given uber jar filename."""
    name = os.path.basename(bundled_uber_jar)
    if name.startswith("altastata-services-"):
        return "com.altastata.services.AltaStataServicesApplication"
    return "com.altastata.grpc.GrpcApplication"


def build_bundled_grpc_classpath(bundled_uber_jar: str) -> str:
    """
    Build classpath for packaged gRPC server.

    Uses all jars under altastata/lib so we can support the Hadoop-style build
    where Bouncy Castle remains in separate signed jars (excluded from uber).
    """
    jar_dir = Path(bundled_uber_jar).resolve().parent
    jars = sorted(str(p) for p in jar_dir.iterdir() if p.suffix == ".jar")
    # Prefer signed BC jars before uber if both are present.
    bc_jars = [
        p for p in jars if os.path.basename(p).startswith(("bcprov", "bcpkix", "bcutil"))
    ]
    others = [p for p in jars if p not in bc_jars and p != os.path.abspath(bundled_uber_jar)]
    ordered = bc_jars + others + [os.path.abspath(bundled_uber_jar)]
    return (";" if platform.system() == "Windows" else ":").join(ordered)


def find_bundled_console_ui_dir() -> Optional[str]:
    """
    Resolve the AltaStata Console SPA bundle that ships next to the gRPC jar.

    Returns the absolute path to ``altastata/lib/altastata-console-static`` if
    it exists and contains an ``index.html``, otherwise None.
    """
    ui_dir = _bundled_data_path("lib", "altastata-console-static")
    if ui_dir is None or not ui_dir.is_dir():
        return None
    if not (ui_dir / "index.html").is_file():
        return None
    return str(ui_dir)


def default_mycloud_dir() -> Optional[str]:
    env_dir = os.environ.get("ALTASTATA_MYCLOUD_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir

    # altastata/java_runtime.py → repo sibling ../../mycloud when developing
    # from a checkout of altastata-python-package next to mycloud.
    repo_candidate = Path(__file__).resolve().parents[2] / "mycloud"
    if repo_candidate.is_dir():
        return str(repo_candidate)
    return None


def build_grpc_subprocess_env() -> Dict[str, str]:
    """
    Environment for ``subprocess.Popen`` when launching the Java gateway.

    Inherits the parent environment, then exports ``ALTASTATA_WEB_UI_DIR``
    pointing at the bundled SPA when present (unless the caller already set
    the variable — including empty to disable the UI).
    """
    env = os.environ.copy()
    if not env.get("ALTASTATA_WEB_UI_DIR"):
        ui_dir = find_bundled_console_ui_dir()
        if ui_dir is not None:
            env["ALTASTATA_WEB_UI_DIR"] = ui_dir
            print(f"Bundled AltaStata Console UI: {ui_dir}")
    return env


def _use_maven_classpath() -> bool:
    """Opt-in prototype: assemble gateway -cp from GAV lock + mavenLocal/Central.

    Enable with ``ALTASTATA_USE_MAVEN_CLASSPATH=1``. Default remains uber jar /
    Gradle fallback so existing installs and tests are unchanged.
    """
    flag = os.environ.get("ALTASTATA_USE_MAVEN_CLASSPATH", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def resolve_maven_gateway_command() -> Tuple[List[str], Optional[str]]:
    """Build ``java -cp … AltaStataServicesApplication`` via :mod:`maven_resolve`."""
    from altastata.maven_resolve import resolve_classpath, summarize_resolve

    result = resolve_classpath()
    print(f"Maven classpath resolve: {summarize_resolve(result)}")
    command = [
        "java",
        *resolve_java_memory_opts(),
        "-cp",
        result.classpath,
        result.main_class,
    ]
    return command, None


def resolve_local_grpc_startup_command(
    grpc_server_command: Optional[Sequence[str]] = None,
    working_dir: Optional[str] = None,
) -> Tuple[List[str], Optional[str]]:
    resolved_working_dir = working_dir
    if grpc_server_command is None:
        if _use_maven_classpath():
            return resolve_maven_gateway_command()
        bundled_uber_jar = find_bundled_grpc_uber_jar()
        if bundled_uber_jar is not None:
            classpath = build_bundled_grpc_classpath(bundled_uber_jar)
            main_class = grpc_main_class_for_jar(bundled_uber_jar)
            grpc_server_command = [
                "java",
                *resolve_java_memory_opts(),
                "-cp",
                classpath,
                main_class,
            ]
            if resolved_working_dir is None:
                resolved_working_dir = os.path.dirname(bundled_uber_jar)
        else:
            grpc_server_command = ["./gradlew", ":altastata-services:run"]
            if resolved_working_dir is None:
                resolved_working_dir = default_mycloud_dir()

    command = list(grpc_server_command)
    if resolved_working_dir is None and command[:2] == [
        "./gradlew",
        ":altastata-services:run",
    ]:
        raise RuntimeError(
            "Unable to locate bundled altastata-services runtime jar and unable to determine mycloud "
            "directory for Gradle fallback. Package altastata-services-*-uber.jar under altastata/lib, "
            "or pass grpc_server_command/grpc_server_working_dir, or set ALTASTATA_MYCLOUD_DIR."
        )
    return command, resolved_working_dir


def _start_stream_thread(pipe, label: str) -> None:
    if pipe is None:
        return

    def _reader():
        try:
            with pipe:
                for line in iter(pipe.readline, b""):
                    txt = line.decode("utf-8", errors="replace").rstrip()
                    if txt:
                        print(f"[{label}] {txt}")
        except Exception:
            # Keep startup robust even if output streaming fails.
            pass

    threading.Thread(target=_reader, daemon=True).start()


def start_local_grpc_service(
    grpc_server_command: Optional[Sequence[str]] = None,
    working_dir: Optional[str] = None,
):
    """Spawn the local Java gateway (bundled uber jar or Gradle fallback)."""
    resolved_command, resolved_working_dir = resolve_local_grpc_startup_command(
        grpc_server_command=grpc_server_command,
        working_dir=working_dir,
    )
    print(
        "Starting gRPC server command:",
        " ".join(resolved_command),
        f"(cwd={resolved_working_dir or os.getcwd()})",
    )

    stream_logs = os.environ.get("ALTASTATA_GRPC_LOG_STREAM", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    process = subprocess.Popen(
        list(resolved_command),
        cwd=resolved_working_dir,
        env=build_grpc_subprocess_env(),
        stdout=subprocess.PIPE if stream_logs else subprocess.DEVNULL,
        stderr=subprocess.PIPE if stream_logs else subprocess.DEVNULL,
    )
    if stream_logs:
        _start_stream_thread(process.stdout, "grpc-stdout")
        _start_stream_thread(process.stderr, "grpc-stderr")
    return process


# Underscore aliases so existing call sites / tests can keep a familiar name
# while the public helpers above use clearer names without the leading `_`.
_find_bundled_grpc_uber_jar = find_bundled_grpc_uber_jar
_build_bundled_grpc_classpath = build_bundled_grpc_classpath
_find_bundled_console_ui_dir = find_bundled_console_ui_dir
_default_mycloud_dir = default_mycloud_dir
_build_grpc_subprocess_env = build_grpc_subprocess_env
_resolve_local_grpc_startup_command = resolve_local_grpc_startup_command
_start_local_grpc_service = start_local_grpc_service
_grpc_main_class_for_jar = grpc_main_class_for_jar
