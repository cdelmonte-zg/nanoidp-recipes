"""The NanoIDP a recipe runs against.

Every recipe has its own settings.yaml and users.yaml next to its test. The
`idp` fixture starts a NanoIDP with those two files, on the port
settings.yaml names, and stops it when the recipe's tests are done; the next
recipe gets a NanoIDP of its own. Set NANOIDP_URL to use an instance that is
already running with the recipe's configuration; the fixture then starts
and stops nothing.

This file needs nothing else from the repository: copied next to one
recipe's files, it starts the NanoIDP of that recipe.
"""

import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest
import requests
import yaml

STARTUP_SECONDS = 30


@dataclass
class Instance:
    url: str
    # None when NANOIDP_URL names the instance: where it runs is not known
    home: Optional[Path] = None        # the server's working directory: its keys live here
    config_dir: Optional[Path] = None  # what a second process gets as NANOIDP_CONFIG_DIR


@pytest.fixture(scope="module")
def idp_instance(request, tmp_path_factory):
    given = os.environ.get("NANOIDP_URL")
    if given:
        yield Instance(url=given.rstrip("/"))
        return

    # A copy of the recipe's configuration in a temporary directory, which is
    # also the server's working directory: NanoIDP writes its signing keys
    # there and nothing lands next to the tests
    recipe = request.path.parent
    home = tmp_path_factory.mktemp("nanoidp")
    (home / "config").mkdir()
    for name in ("settings.yaml", "users.yaml"):
        shutil.copy(recipe / name, home / "config" / name)
    listening = yaml.safe_load((recipe / "settings.yaml").read_text(encoding="utf-8"))["server"]
    host, port = listening["host"], listening["port"]
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
        yield Instance(url=url, home=home, config_dir=home / "config")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


@pytest.fixture(scope="module")
def idp(idp_instance):
    """The base URL of the recipe's NanoIDP."""
    return idp_instance.url
