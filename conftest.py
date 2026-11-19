"""The NanoIDP the recipes run against.

Every recipe takes the `idp` fixture and gets the base URL of a running
NanoIDP. By default the fixture starts one itself, from a configuration that
`nanoidp init` writes into a temporary directory, on a free port, and stops
it at the end. Set NANOIDP_URL to run the recipes against an instance you
started yourself; the fixture then starts and stops nothing.

A recipe that needs a second process on the same state, such as the MCP
server, takes `shared_idp` instead: a NanoIDP of its own whose runtime
store is a SQLite file.
"""

import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests

STARTUP_SECONDS = 30

SHARED_STORE = """
runtime:
  store: sqlite
  path: ../state/runtime.db
"""


@dataclass
class Instance:
    url: str
    home: Path        # the working directory of the server: its keys live here
    config_dir: Path  # what a second process is given as NANOIDP_CONFIG_DIR


def _free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _running(home, settings=""):
    """Start a NanoIDP in `home` and yield it; stop it afterwards. `settings`
    is appended to the settings.yaml that `nanoidp init` writes."""
    # The working directory is the temporary one: NanoIDP resolves its keys
    # directory against it, so nothing is written into this checkout
    subprocess.run(
        [sys.executable, "-m", "nanoidp", "init", "config"],
        cwd=home, check=True, capture_output=True,
    )
    if settings:
        with open(home / "config" / "settings.yaml", "a", encoding="utf-8") as file:
            file.write(settings)
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    log_path = home / "nanoidp.log"
    with open(log_path, "w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "nanoidp", "--config", "config", "--port", str(port)],
            cwd=home, stdout=log, stderr=subprocess.STDOUT,
        )
    try:
        deadline = time.monotonic() + STARTUP_SECONDS
        while True:
            if server.poll() is not None:
                pytest.fail(f"NanoIDP exited at startup:\n{log_path.read_text(encoding='utf-8')}")
            try:
                if requests.get(f"{url}/api/health", timeout=2).status_code == 200:
                    break
            except requests.ConnectionError:
                pass
            if time.monotonic() > deadline:
                pytest.fail(
                    f"NanoIDP did not answer within {STARTUP_SECONDS} s:\n"
                    f"{log_path.read_text(encoding='utf-8')}"
                )
            time.sleep(0.2)
        yield Instance(url=url, home=home, config_dir=home / "config")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


@pytest.fixture(scope="session")
def idp(tmp_path_factory):
    given = os.environ.get("NANOIDP_URL")
    if given:
        yield given.rstrip("/")
        return
    for instance in _running(tmp_path_factory.mktemp("nanoidp")):
        yield instance.url


@pytest.fixture(scope="session")
def shared_idp(tmp_path_factory):
    """A NanoIDP with a shared runtime store, always started here: a second
    process needs its configuration directory, which NANOIDP_URL cannot give."""
    yield from _running(tmp_path_factory.mktemp("nanoidp-shared"), settings=SHARED_STORE)
