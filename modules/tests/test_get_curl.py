import os
import shutil
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import get_curl


def _check_curl_available():
    try:
        subprocess.run(["curl", "--version"], capture_output=True, check=True)
    except Exception:
        pytest.skip("curl not available")


def _serve_file_url(source_path):
    return "file://" + str(source_path.resolve())


def _make_module_mock(tmp_path, force, dest_path, tmp_dest=None, timeout=5, retries=1):
    module = MagicMock()
    module.params = {
        "url": "",
        "dest": str(dest_path),
        "tmp_dest": str(tmp_dest) if tmp_dest else None,
        "headers": None,
        "force": force,
        "timeout": timeout,
        "retries": retries,
    }
    module.check_mode = False
    module.tmpdir = str(tmp_path)
    module.exit_json.side_effect = SystemExit(0)
    module.fail_json.side_effect = SystemExit(1)
    module.load_file_common_arguments.return_value = {}
    module.set_fs_attributes_if_different.return_value = False
    module.atomic_move.side_effect = shutil.copy2
    return module


class TestForceEarlyExit:
    def test_skips_download_when_file_exists_and_not_forced(self, tmp_path, monkeypatch):
        dest = tmp_path / "testfile"
        dest.write_text("original content")

        module = _make_module_mock(tmp_path, force=False, dest_path=dest)
        monkeypatch.setattr("get_curl.AnsibleModule", lambda *a, **kw: module)

        with pytest.raises(SystemExit) as exc:
            get_curl.run_module()

        assert exc.value.code == 0
        module.exit_json.assert_called_once_with(
            msg="File already exists", dest=str(dest), url="", changed=False
        )
        assert dest.read_text() == "original content"
        module.atomic_move.assert_not_called()

    def test_updates_attributes_when_file_exists_and_not_forced(self, tmp_path, monkeypatch):
        dest = tmp_path / "testfile"
        dest.write_text("original content")

        module = _make_module_mock(tmp_path, force=False, dest_path=dest)
        module.load_file_common_arguments.return_value = {"mode": "0644"}
        module.set_fs_attributes_if_different.return_value = True
        monkeypatch.setattr("get_curl.AnsibleModule", lambda *a, **kw: module)

        with pytest.raises(SystemExit) as exc:
            get_curl.run_module()

        assert exc.value.code == 0
        (msg, kw) = module.exit_json.call_args
        assert "updated attributes" in kw["msg"]
        assert kw["changed"] is True
        assert dest.read_text() == "original content"
        module.atomic_move.assert_not_called()


class TestRealDownload:
    def test_downloads_when_file_does_not_exist(self, tmp_path, monkeypatch):
        _check_curl_available()
        source = tmp_path / "source-file"
        source.write_text("hello from curl")
        dest = tmp_path / "downloaded-file"

        module = _make_module_mock(tmp_path, force=False, dest_path=dest, tmp_dest=tmp_path)
        module.params["url"] = _serve_file_url(source)
        monkeypatch.setattr("get_curl.AnsibleModule", lambda *a, **kw: module)

        with pytest.raises(SystemExit) as exc:
            get_curl.run_module()

        assert exc.value.code == 0
        assert dest.read_text() == "hello from curl"

    def test_downloads_when_file_does_not_exist_with_force(self, tmp_path, monkeypatch):
        _check_curl_available()
        source = tmp_path / "source-file"
        source.write_text("forced download content")
        dest = tmp_path / "downloaded-file"

        module = _make_module_mock(tmp_path, force=True, dest_path=dest, tmp_dest=tmp_path)
        module.params["url"] = _serve_file_url(source)
        monkeypatch.setattr("get_curl.AnsibleModule", lambda *a, **kw: module)

        with pytest.raises(SystemExit) as exc:
            get_curl.run_module()

        assert exc.value.code == 0
        assert dest.read_text() == "forced download content"

    def test_overwrites_when_file_exists_and_forced(self, tmp_path, monkeypatch):
        _check_curl_available()
        source = tmp_path / "source-file"
        source.write_text("fresh content")
        dest = tmp_path / "overwrite-target"
        dest.write_text("stale content")

        module = _make_module_mock(tmp_path, force=True, dest_path=dest, tmp_dest=tmp_path)
        module.params["url"] = _serve_file_url(source)
        monkeypatch.setattr("get_curl.AnsibleModule", lambda *a, **kw: module)

        with pytest.raises(SystemExit) as exc:
            get_curl.run_module()

        assert exc.value.code == 0
        module.exit_json.assert_called_once_with(
            msg="File downloaded successfully", dest=str(dest), url=_serve_file_url(source), changed=True
        )
        assert dest.read_text() == "fresh content"

    def test_preserves_when_file_exists_and_not_forced(self, tmp_path, monkeypatch):
        _check_curl_available()
        source = tmp_path / "source-file"
        source.write_text("should not be downloaded")
        dest = tmp_path / "preserve-target"
        dest.write_text("precious content")

        module = _make_module_mock(tmp_path, force=False, dest_path=dest, tmp_dest=tmp_path)
        module.params["url"] = _serve_file_url(source)
        monkeypatch.setattr("get_curl.AnsibleModule", lambda *a, **kw: module)

        with pytest.raises(SystemExit) as exc:
            get_curl.run_module()

        assert exc.value.code == 0
        assert dest.read_text() == "precious content"


class TestForceDefaults:
    def test_force_defaults_to_false(self, tmp_path, monkeypatch):
        dest = tmp_path / "default-force"
        dest.write_text("exists")

        captured_spec = {}
        module = None

        def spy_ansible_module(*args, **kwargs):
            nonlocal module
            captured_spec.update(kwargs.get("argument_spec", {}))
            module = _make_module_mock(tmp_path, force=False, dest_path=dest)
            return module

        monkeypatch.setattr("get_curl.AnsibleModule", spy_ansible_module)

        with pytest.raises(SystemExit) as exc:
            get_curl.run_module()

        assert exc.value.code == 0
        assert captured_spec["force"]["default"] is False
        module.exit_json.assert_called_once_with(
            msg="File already exists", dest=str(dest), url="", changed=False
        )
