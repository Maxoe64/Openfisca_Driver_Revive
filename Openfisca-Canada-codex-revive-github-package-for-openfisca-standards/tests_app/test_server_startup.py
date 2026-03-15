from unittest.mock import patch

from app import server


class DummyServer:
    pass


def test_resolve_server_falls_back_to_next_port():
    calls = []

    def fake_build(host, port):
        calls.append((host, port))
        if port == 5000:
            raise OSError("blocked")
        return DummyServer()

    with patch("app.server.build_server", side_effect=fake_build):
        instance, used_port = server.resolve_server("127.0.0.1", 5000, auto_port=True)

    assert isinstance(instance, DummyServer)
    assert used_port == 5050
    assert calls[0] == ("127.0.0.1", 5000)
    assert calls[1] == ("127.0.0.1", 5050)
