import configparser
import hashlib
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.build_plugin_zip import (
    PLUGIN_PACKAGE_NAME,
    RUNTIME_FILES,
    build_plugin_zip,
    default_output_path,
    validated_runtime_file,
)


def test_plugin_zip_has_one_clean_installable_root(tmp_path: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    default_path = default_output_path(source_root)
    assert default_path.name == "Poprawka odwzorowawcza PL-2000-1.1.0.zip"
    output_path = build_plugin_zip(source_root, tmp_path / default_path.name)

    with ZipFile(output_path) as archive:
        names = archive.namelist()
        roots = {name.split("/", 1)[0] for name in names}

        assert roots == {PLUGIN_PACKAGE_NAME}
        assert names == [
            f"{PLUGIN_PACKAGE_NAME}/{relative_path}"
            for relative_path in sorted(RUNTIME_FILES)
        ]

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
        assert metadata["general"]["version"] == "1.1.0"
        assert metadata["general"]["email"] == (
            "github.com.amenity983@passfwd.com"
        )
        assert metadata["general"]["name"] == "Poprawka odwzorowawcza PL-2000"
        assert metadata["general"]["qgisminimumversion"] == "3.40"
        assert metadata["general"]["hasprocessingprovider"] == "yes"
        assert metadata["general"]["experimental"] == "False"

        assert archive.read(f"{PLUGIN_PACKAGE_NAME}/README.md").startswith(
            b"# Poprawka odwzorowawcza PL-2000\n"
        )
        polish = archive.read(f"{PLUGIN_PACKAGE_NAME}/README.md").decode()
        english = archive.read(f"{PLUGIN_PACKAGE_NAME}/README.en.md").decode()
        assert "[English](README.en.md)" in polish
        assert "[Polski](README.md)" in english
        assert english.startswith("# Poprawka odwzorowawcza PL-2000\n")
        assert "More info at GitHub repo." in (metadata["general"]["about"])
        assert "EN: Calculates" in metadata["general"]["description"]
        assert "PL: Oblicza" in metadata["general"]["description"]
        assert "PL\n" in metadata["general"]["about"]
        assert "\nEN\n" in metadata["general"]["about"]
        for info in archive.infolist():
            assert (info.external_attr >> 16) == 0o100644
            assert not any(
                part.startswith(".") for part in Path(info.filename).parts
            )
            assert Path(info.filename).suffix in (
                ".py",
                ".md",
                ".txt",
                ".png",
                ".svg",
                "",
            )

        icon_data = archive.read(f"{PLUGIN_PACKAGE_NAME}/resources/icon.png")
        assert icon_data[:8] == b"\x89PNG\r\n\x1a\n"
        assert int.from_bytes(icon_data[16:20], "big") == 64
        assert int.from_bytes(icon_data[20:24], "big") == 64

        for relative_path in RUNTIME_FILES:
            assert (
                archive.read(f"{PLUGIN_PACKAGE_NAME}/{relative_path}")
                == (source_root / relative_path).read_bytes()
            )


def test_plugin_zip_is_reproducible(tmp_path: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    first = build_plugin_zip(source_root, tmp_path / "first.zip")
    second = build_plugin_zip(source_root, tmp_path / "second.zip")

    assert (
        hashlib.sha256(first.read_bytes()).digest()
        == hashlib.sha256(second.read_bytes()).digest()
    )


def test_plugin_zip_rejects_unexpected_runtime_file(tmp_path: Path) -> None:
    source_root = _copied_source_root(tmp_path)
    unexpected_path = source_root / "resources" / "diagnostic.txt"
    unexpected_path.write_text("must not be published", encoding="utf-8")

    with pytest.raises(ValueError, match="not in the release manifest"):
        build_plugin_zip(source_root, tmp_path / "plugin.zip")

    assert not (tmp_path / "plugin.zip").exists()


def test_plugin_zip_rejects_runtime_file_symlink(tmp_path: Path) -> None:
    source_root = _copied_source_root(tmp_path)
    external_file = tmp_path / "private-key.txt"
    external_file.write_text("must not be published", encoding="utf-8")
    icon_path = source_root / "resources" / "icon.svg"
    icon_path.unlink()
    icon_path.symlink_to(external_file)

    with pytest.raises(ValueError, match="symlink is not allowed"):
        build_plugin_zip(source_root, tmp_path / "plugin.zip")

    assert not (tmp_path / "plugin.zip").exists()


def test_runtime_file_must_remain_inside_source_root(tmp_path: Path) -> None:
    source_root = _copied_source_root(tmp_path)
    external_file = tmp_path / "external.py"
    external_file.write_text("pass", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes source root"):
        validated_runtime_file(source_root, external_file)


def test_plugin_zip_rejects_missing_manifest_file(tmp_path: Path) -> None:
    source_root = _copied_source_root(tmp_path)
    (source_root / "resources" / "icon.svg").unlink()

    with pytest.raises(FileNotFoundError, match="missing runtime plugin file"):
        build_plugin_zip(source_root, tmp_path / "plugin.zip")

    assert not (tmp_path / "plugin.zip").exists()


def _copied_source_root(tmp_path: Path) -> Path:
    repository_root = Path(__file__).resolve().parents[2]
    source_root = tmp_path / "source"
    source_root.mkdir()
    for relative_path in RUNTIME_FILES:
        source_path = repository_root / relative_path
        target_path = source_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
    return source_root
