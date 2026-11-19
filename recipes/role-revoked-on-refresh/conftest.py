"""The NanoIDP this recipe runs against.

The `idp` fixture starts one with the settings.yaml and users.yaml next to
this file, on the port settings.yaml names, and stops it at the end. Set
NANOIDP_URL to use an instance that is already running with that
configuration; the fixture then starts and stops nothing.
"""

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
import yaml

HERE = Path(__file__).parent
STARTUP_SECONDS = 30


@pytest.fixture(scope="session")
def idp(tmp_path_factory):
    given = os.environ.get("NANOIDP_URL")
    if given:
        yield given.rstrip("/")
        return

    # A copy of the configuration in a temporary directory, which is also the
    # server's working directory: NanoIDP writes its signing keys there and
    # nothing lands next to the tests
    home = tmp_path_factory.mktemp("nanoidp")
    (home / "config").mkdir()
    for name in ("settings.yaml", "users.yaml"):
        shutil.copy(HERE / name, home / "config" / name)
    server_settings = yaml.safe_load((HERE / "settings.yaml").read_text(encoding="utf-8"))["server"]
    host, port = server_settings["host"], server_settings["port"]
    url = f"http://{host}:{port}"

    # Refuse a port another process holds: the readiness check below would
    # be answered by that process instead of this NanoIDP
    with socket.socket() as probe:
        if probe.connect_ex((host, port)) == 0:
            pytest.fail(
                f"port {port} is in use: change server.port and oauth.issuer in settings.yaml, "
                "or set NANOIDP_URL to the NanoIDP that is running there"
            )

    log_path = home / "nanoidp.log"
    with open(log_path, "w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "nanoidp", "--config", "config"],
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
