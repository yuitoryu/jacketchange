from pathlib import Path
import re

from beartype import beartype


@beartype
def find_jacket_files(graphics_path: Path) -> list[Path]:
    """Find packed jacket IFS files in a graphics folder."""

    pattern = re.compile(r"^s_jacket(?!00)[0-9]{2}\.ifs$")
    return [
        f
        for f in graphics_path.iterdir()
        if f.is_file() and pattern.match(f.name)
    ]


@beartype
def find_unpacked_ifs(unpacked_path: Path) -> list[Path]:
    """Find unpacked jacket IFS directories in a workspace."""

    pattern = re.compile(r"^s_jacket(?!00)[0-9]{2}_ifs$")
    return [
        f
        for f in unpacked_path.iterdir()
        if f.is_dir() and pattern.match(f.name)
    ]
