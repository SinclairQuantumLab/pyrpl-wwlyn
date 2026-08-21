"""Verify that a built wheel contains the supported PyRPL distribution."""

from email.parser import BytesParser
from pathlib import Path
import sys
import tomllib
from zipfile import ZipFile


REQUIRED_FILES = {
    "pyrpl/__init__.py",
    "pyrpl/config/global_config.yml",
    "pyrpl/fpga/red_pitaya.bin",
    "pyrpl/fpga/red_pitaya.dtbo",
}


def verify_wheel(wheel_path):
    wheel_path = Path(wheel_path).resolve()
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]

    with ZipFile(wheel_path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_FILES.difference(names)
        assert not missing, f"Wheel is missing required files: {sorted(missing)}"
        assert not any(name.startswith("src/pyrpl_change") for name in names)

        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        entry_name = next(
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        )
        metadata = BytesParser().parsebytes(archive.read(metadata_name))
        entries = archive.read(entry_name).decode("utf-8")

        assert metadata["Name"] == project["name"]
        assert metadata["Version"] == project["version"]
        assert metadata["Requires-Python"] == project["requires-python"]
        assert metadata["License-Expression"] == project["license"]
        assert "paramiko>=4,<6" in metadata.get_all("Requires-Dist", [])
        assert "sinclair-pyrpl-wwlyn = pyrpl.__main__:main" in entries
        assert any(
            name.endswith(".dist-info/licenses/LICENSE") for name in names
        )

    print(f"Verified wheel: {wheel_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_wheel.py WHEEL")
    verify_wheel(sys.argv[1])
