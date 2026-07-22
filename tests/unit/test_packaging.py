import configparser
import hashlib
from pathlib import Path
from zipfile import ZipFile

from scripts.build_plugin_zip import PLUGIN_PACKAGE_NAME, build_plugin_zip


def test_plugin_zip_has_one_clean_installable_root(tmp_path: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    output_path = build_plugin_zip(source_root, tmp_path / "plugin.zip")

    with ZipFile(output_path) as archive:
        names = archive.namelist()
        roots = {name.split("/", 1)[0] for name in names}

        assert roots == {PLUGIN_PACKAGE_NAME}
        for required_name in (
            "__init__.py",
            "LICENSE",
            "metadata.txt",
            "plugin.py",
            "resources/icon.svg",
        ):
            assert f"{PLUGIN_PACKAGE_NAME}/{required_name}" in names

        assert not any("/__pycache__/" in name for name in names)
        assert not any(name.endswith((".pyc", ".pyo")) for name in names)
        assert not any(
            f"/{excluded}/" in name
            for name in names
            for excluded in (
                "docs",
                "legacy",
                "tests",
                ".git",
            )
        )

        metadata = configparser.ConfigParser()
        metadata.read_string(
            archive.read(f"{PLUGIN_PACKAGE_NAME}/metadata.txt").decode("utf-8")
        )
        assert metadata["general"]["qgisminimumversion"] == "3.40"
        assert metadata["general"]["hasprocessingprovider"] == "yes"


def test_plugin_zip_is_reproducible(tmp_path: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    first = build_plugin_zip(source_root, tmp_path / "first.zip")
    second = build_plugin_zip(source_root, tmp_path / "second.zip")

    assert (
        hashlib.sha256(first.read_bytes()).digest()
        == hashlib.sha256(second.read_bytes()).digest()
    )
