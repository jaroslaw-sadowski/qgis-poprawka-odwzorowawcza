"""Build a deterministic, installable QGIS plugin ZIP archive."""

import argparse
import configparser
import stat
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional, Sequence
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

PLUGIN_PACKAGE_NAME = "qgis_poprawka_odwzorowawcza"
RUNTIME_FILES = (
    "__init__.py",
    "adapters/__init__.py",
    "adapters/geometry.py",
    "adapters/repair.py",
    "adapters/zones.py",
    "compat.py",
    "core/__init__.py",
    "core/calculation.py",
    "core/errors.py",
    "core/models.py",
    "gui/__init__.py",
    "gui/about_dialog.py",
    "gui/dialog.py",
    "gui/theme.py",
    "LICENSE",
    "metadata.txt",
    "plugin.py",
    "processing_provider/__init__.py",
    "processing_provider/area_algorithm.py",
    "processing_provider/provider.py",
    "README.md",
    "README.en.md",
    "resources/icon.png",
    "resources/icon.svg",
    "user_messages.py",
)
RUNTIME_DIRECTORIES = (
    "adapters",
    "core",
    "gui",
    "processing_provider",
    "resources",
)
IGNORED_GENERATED_SUFFIXES = (".pyc", ".pyo")


def runtime_files(source_root: Path) -> Sequence[Path]:
    """Return validated files from the explicit release manifest."""

    resolved_root = source_root.resolve(strict=True)
    if not resolved_root.is_dir():
        raise NotADirectoryError(
            f"source root is not a directory: {source_root}"
        )

    missing_directories = [
        resolved_root / directory_name
        for directory_name in RUNTIME_DIRECTORIES
        if not (resolved_root / directory_name).is_dir()
    ]
    if missing_directories:
        missing_names = ", ".join(str(path) for path in missing_directories)
        raise FileNotFoundError(
            f"missing runtime plugin directories: {missing_names}"
        )

    expected_relative_paths = {
        Path(relative_path) for relative_path in RUNTIME_FILES
    }
    _reject_unexpected_runtime_entries(
        resolved_root,
        expected_relative_paths,
    )

    files = []
    for relative_path in expected_relative_paths:
        candidate = resolved_root / relative_path
        try:
            files.append(validated_runtime_file(resolved_root, candidate))
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"missing runtime plugin file: {candidate}"
            ) from error

    return tuple(
        sorted(
            files,
            key=lambda path: path.relative_to(resolved_root).as_posix(),
        )
    )


def validated_runtime_file(source_root: Path, candidate: Path) -> Path:
    """Return a regular manifest file contained in a symlink-free root."""

    resolved_root = source_root.resolve(strict=True)
    try:
        relative_candidate = candidate.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"runtime file escapes source root: {candidate}"
        ) from error

    current_path = resolved_root
    for path_part in relative_candidate.parts:
        current_path /= path_part
        if current_path.is_symlink():
            raise ValueError(f"runtime symlink is not allowed: {current_path}")

    resolved_candidate = candidate.resolve(strict=True)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"runtime file escapes source root: {candidate}"
        ) from error

    if not stat.S_ISREG(resolved_candidate.stat().st_mode):
        raise ValueError(f"runtime entry is not a regular file: {candidate}")
    return resolved_candidate


def _reject_unexpected_runtime_entries(
    source_root: Path,
    expected_relative_paths: set,
) -> None:
    for directory_name in RUNTIME_DIRECTORIES:
        directory = source_root / directory_name
        if directory.is_symlink():
            raise ValueError(f"runtime symlink is not allowed: {directory}")

        for candidate in directory.rglob("*"):
            relative_path = candidate.relative_to(source_root)
            if candidate.is_symlink():
                raise ValueError(
                    f"runtime symlink is not allowed: {candidate}"
                )
            if candidate.is_dir() or _is_ignored_generated_path(relative_path):
                continue
            if relative_path not in expected_relative_paths:
                raise ValueError(
                    f"unexpected runtime file is not in the release "
                    f"manifest: {candidate}"
                )


def _is_ignored_generated_path(relative_path: Path) -> bool:
    return (
        "__pycache__" in relative_path.parts
        or relative_path.suffix in IGNORED_GENERATED_SUFFIXES
    )


def build_plugin_zip(source_root: Path, output_path: Path) -> Path:
    """Create a reproducible ZIP with exactly one plugin root directory."""

    source_root = source_root.resolve(strict=True)
    output_path = output_path.resolve()
    files = runtime_files(source_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_path, "w") as archive:
        for source_path in files:
            relative_path = source_path.relative_to(source_root)
            archive_path = PurePosixPath(
                PLUGIN_PACKAGE_NAME, *relative_path.parts
            )
            _write_file(archive, source_path, archive_path)
    return output_path


def default_output_path(source_root: Path) -> Path:
    """Return the versioned default archive path from metadata.txt."""

    metadata = configparser.ConfigParser()
    metadata.read(source_root / "metadata.txt", encoding="utf-8")
    version = metadata["general"]["version"]
    name = metadata["general"]["name"]
    return source_root / "dist" / f"{name}-{version}.zip"


def _write_file(
    archive: ZipFile,
    source_path: Path,
    archive_path: PurePosixPath,
) -> None:
    info = ZipInfo(str(archive_path))
    info.date_time = (1980, 1, 1, 0, 0, 0)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, source_path.read_bytes())


def _parse_arguments(
    arguments: Optional[Iterable[str]] = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Ścieżka wynikowego ZIP; domyślnie katalog dist/.",
    )
    return parser.parse_args(arguments)


def main(arguments: Optional[Iterable[str]] = None) -> int:
    source_root = Path(__file__).resolve().parents[1]
    parsed_arguments = _parse_arguments(arguments)
    output_path = parsed_arguments.output or default_output_path(source_root)
    built_path = build_plugin_zip(source_root, output_path)
    print(built_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
