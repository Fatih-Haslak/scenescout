import io
import json

import pytest

from scenescout import __main__ as cli


class Probe:
    occupied = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def settimeout(self, value):
        pass

    def connect_ex(self, address):
        return 0 if self.occupied else 1


def test_launch_options_configure_local_server(monkeypatch):
    monkeypatch.setattr(cli.socket, "socket", Probe)
    monkeypatch.setenv("SCENESCOUT_DEVICE", "auto")
    monkeypatch.setenv("SCENESCOUT_BATCH_SIZE", "2")
    calls = []
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    cli.main(["--device", "cpu", "--batch-size", "4", "--port", "8877"])
    assert cli.os.environ["SCENESCOUT_DEVICE"] == "cpu"
    assert cli.os.environ["SCENESCOUT_BATCH_SIZE"] == "4"
    assert calls[0][1]["host"] == "127.0.0.1"
    assert calls[0][1]["port"] == 8877


def test_second_launch_reuses_existing_scenescout(monkeypatch):
    monkeypatch.setattr(Probe, "occupied", True)
    monkeypatch.setattr(cli.socket, "socket", Probe)
    monkeypatch.setattr(
        cli.urllib.request,
        "urlopen",
        lambda *args, **kwargs: io.BytesIO(
            json.dumps(
                {
                    "mode": "visual_frames",
                    "model": {"model": "google/embeddinggemma-2"},
                    "library_id": cli.library_id(),
                }
            ).encode()
        ),
    )
    opened = []
    monkeypatch.setattr(cli.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: pytest.fail("duplicate server"))
    cli.main(["--open-browser"])
    assert opened == ["http://127.0.0.1:8765"]


@pytest.mark.parametrize("args", [["--port", "0"], ["--port", "70000"], ["--batch-size", "17"]])
def test_invalid_launch_options(args):
    with pytest.raises(SystemExit) as error:
        cli.main(args)
    assert error.value.code == 2


@pytest.mark.parametrize("identity", [None, "another-library"])
def test_second_launch_rejects_old_or_different_library(monkeypatch, identity):
    monkeypatch.setattr(Probe, "occupied", True)
    monkeypatch.setattr(cli.socket, "socket", Probe)
    payload = {"mode": "visual_frames", "model": {"model": "google/embeddinggemma-2"}}
    if identity is not None:
        payload["library_id"] = identity
    monkeypatch.setattr(
        cli.urllib.request,
        "urlopen",
        lambda *args, **kwargs: io.BytesIO(json.dumps(payload).encode()),
    )
    monkeypatch.setattr(cli.webbrowser, "open", lambda url: pytest.fail("wrong library opened"))
    with pytest.raises(SystemExit) as error:
        cli.main(["--open-browser"])
    assert error.value.code == 2


def test_occupied_port_does_not_open_another_application(monkeypatch):
    monkeypatch.setattr(Probe, "occupied", True)
    monkeypatch.setattr(cli.socket, "socket", Probe)
    monkeypatch.setattr(
        cli.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(b'{"mode":"other"}')
    )
    monkeypatch.setattr(cli.webbrowser, "open", lambda url: pytest.fail("unrelated app opened"))
    with pytest.raises(SystemExit) as error:
        cli.main(["--open-browser"])
    assert error.value.code == 2
