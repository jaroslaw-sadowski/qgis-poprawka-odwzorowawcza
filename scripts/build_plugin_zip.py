"""Build a deterministic, installable QGIS plugin ZIP archive."""

import argparse
import configparser
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional, Sequence
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

PLUGIN_PACKAGE_NAME = "qgis_poprawka_odwzorowawcza"
RUNTIME_ROOT_FILES = (
    "__init__.py",
    "compat.py",
    "LICENSE",
    "metadata.txt",
    "plugin.py",
    "README.md",
)
RUNTIME_DIRECTORIES = (
    "adapters",
    "core",
    "gui",
    "processing_provider",
    "resources",
)
EXCLUDED_FILE_SUFFIXES = (".pyc", ".pyo")


def runtime_files(source_root: Path) -> Sequence[Path]:
    """Return the sorted, explicit set of files required at runtime."""

    missing_directories = [
        source_root / directory_name
        for directory_name in RUNTIME_DIRECTORIES
        if not (source_root / directory_name).is_dir()
    ]
    if missing_directories:
        missing_names = ", ".join(str(path) for path in missing_directories)
        raise FileNotFoundError(f"missing runtime plugin directories: {missing_names}")

    files = [source_root / relative_path for relative_path in RUNTIME_ROOT_FILES]
    for directory_name in RUNTIME_DIRECTORIES:
        directory = source_root / directory_name
        files.extend(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in EXCLUDED_FILE_SUFFIXES
        )

    missing = [path for path in files if not path.is_file()]
    if missing:
        missing_names = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"missing runtime plugin files: {missing_names}")
    return tuple(sorted(set(files), key=lambda path: path.as_posix()))


def build_plugin_zip(source_root: Path, output_path: Path) -> Path:
    """Create a reproducible ZIP with exactly one plugin root directory."""

    source_root = source_root.resolve()
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_path, "w") as archive:
        for source_path in runtime_files(source_root):
            relative_path = source_path.relative_to(source_root)
            archive_path = PurePosixPath(PLUGIN_PACKAGE_NAME, *relative_path.parts)
            _write_file(archive, source_path, archive_path)
    return output_path


def default_output_path(source_root: Path) -> Path:
    """Return the versioned default archive path from metadata.txt."""

    metadata = configparser.ConfigParser()
    metadata.read(source_root / "metadata.txt", encoding="utf-8")
    version = metadata["general"]["version"]
    return source_root / "dist" / f"{PLUGIN_PACKAGE_NAME}-{version}.zip"


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


def _parse_arguments(arguments: Optional[Iterable[str]] = None) -> argparse.Namespace:
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
