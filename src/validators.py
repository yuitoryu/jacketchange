from pathlib import Path

from beartype import beartype


@beartype
def sdvx_folder_checker(sdvx_path: Path) -> bool:
    """Check whether a path looks like an SDVX contents folder."""

    data = sdvx_path / "data"
    graphics = data / "graphics"
    music = data / "music"
    if graphics.exists() and music.exists():
        return True
    return False


@beartype
def craft_id(id: str) -> str:
    """Normalize a numeric song ID to the four-digit jacket ID format."""

    if not id.isnumeric() or int(id) >= 10000 or int(id) <= 0:
        raise ValueError("Song ID must be a positive integer below 10000!")
    return "0" * (4 - len(id)) + id
