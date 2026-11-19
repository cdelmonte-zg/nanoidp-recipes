"""One NanoIDP for the test session.

Every recipe takes the `idp` fixture and gets the base URL of a running
NanoIDP. By default the fixture starts one itself, from a configuration that
`nanoidp init` writes into a temporary directory, on a free port, and stops
it at the end. Set NANOIDP_URL to run the recipes against an instance you
started yourself; the fixture then starts and stops nothing.
"""

import os
import socket
import subprocess
import sys
import time

import pytest
import requests

STARTUP_SECONDS = 30


def _free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="session")
def idp(tmp_path_factory):
    given = os.environ.get("NANOIDP_URL")
    if given:
        yield given.rstrip("/")
        return

    # The working directory is the temporary one: NanoIDP resolves its keys
    # directory against it, so nothing is written into this checkout
    home = tmp_path_factory.mktemp("nanoidp")
    subprocess.run(
        [sys.executable, "-m", "nanoidp", "init", "config"],
        cwd=home, check=True, capture_output=True,
    )
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
        yield url
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
