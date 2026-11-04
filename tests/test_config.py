"""Tests of the prusalink.ini parsing helpers"""
import pytest

from prusa.link.config import (  # type:ignore
    Config,
    FakeArgs,
    parse_camera_stream_url,
)


def test_camera_stream_url_empty_disables_the_stream():
    """No URL means no camera view"""
    assert parse_camera_stream_url("") is None


@pytest.mark.parametrize("value", [
    "http://192.168.1.103:8081/stream",
    "https://prusa.example.com/camera/stream",
    "/camera/stream",
])
def test_camera_stream_url_accepts_urls_and_paths(value):
    """Absolute http(s) URLs and absolute paths are kept as is"""
    assert parse_camera_stream_url(value) == value


@pytest.mark.parametrize("value", [
    "camera/stream",
    "192.168.1.103:8081/stream",
    "rtsp://192.168.1.103:8554/stream",
    "http:///stream",
    "javascript:alert(1)",
])
def test_camera_stream_url_rejects_other_values(value):
    """Anything an image element cannot load from is a configuration error"""
    with pytest.raises(ValueError, match="stream_url"):
        parse_camera_stream_url(value)


@pytest.mark.parametrize(("section", "expected"), [
    ("", None),
    ("[camera]\nstream_url =\n", None),
    ("[camera]\nstream_url = /camera/stream\n", "/camera/stream"),
])
def test_config_reads_camera_stream_url(tmp_path, section, expected):
    """The [camera] section ends up in cfg.camera.stream_url"""
    ini = tmp_path / "prusalink.ini"
    ini.write_text(section)
    assert Config(FakeArgs(str(ini))).camera.stream_url == expected
