import shutil
import subprocess
from pathlib import Path

from beartype import beartype
from tqdm import tqdm

from .utils import analyze_jacket_t_data, find_jacket_files, find_unpacked_ifs


class FolderStructureError(Exception):
    def __init__(self) -> None:
        self.message = "Invalid game folder structure."
        super().__init__(self.message)


@beartype
def copy_jk_ifs(sdvx_path: Path, copy_path: Path) -> list[Path]:
    graphics_path = sdvx_path / "data" / "graphics"
    files = find_jacket_files(graphics_path)

    copy_path.mkdir(parents=True, exist_ok=True)

    copied_files: list[Path] = []
    print("Start copying ifs files...")
    for source_file in tqdm(files):
        destination = copy_path / source_file.name
        shutil.copy2(source_file, destination)
        copied_files.append(destination)
    print("Copy completed.")
    return copied_files


@beartype
def unpack(ifs_file: Path, out_path: Path) -> None:
    out_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ifstools", "-y", str(ifs_file), "-o", str(out_path)],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=None,
        check=True,
    )


@beartype
def pack(ifs_folder: Path, out_path: Path) -> Path:
    out_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ifstools", "-y", str(ifs_folder), "-o", str(out_path)],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=None,
        check=True,
    )

    packed_file = out_path / f"{ifs_folder.name.removesuffix('_ifs')}.ifs"
    if not packed_file.is_file():
        raise FileNotFoundError(f"Packed IFS file was not created: {packed_file}")
    return packed_file


@beartype
def repack_all(unpacked_root: Path, out_path: Path) -> list[Path]:
    packed_files: list[Path] = []
    unpacked_folders = find_unpacked_ifs(unpacked_root)

    print("Start repacking ifs folders...")
    for folder in tqdm(unpacked_folders):
        packed_files.append(pack(folder, out_path))
    print("Repack completed.")
    return packed_files


@beartype
def apply_packed_ifs(data_storage: Path, sdvx_path: Path) -> None:
    unpacked_root = data_storage / "ifs_unpacked"
    packed_root = data_storage / "ifs_packed"
    graphics_path = sdvx_path / "data" / "graphics"

    packed_files = repack_all(unpacked_root, packed_root)

    print("Start copying packed ifs files back to the game folder...")
    for packed_file in tqdm(packed_files):
        shutil.copy2(packed_file, graphics_path / packed_file.name)
    print("Apply completed.")


@beartype
def copy_and_analyze_all_ifs(sdvx_path: Path, data_storage: Path) -> None:
    unpacked = data_storage / "ifs_unpacked"
    packed = data_storage / "ifs_packed"

    copied_path = copy_jk_ifs(sdvx_path, packed)

    print("Start unpacking ifs files...")
    for ifs_file in copied_path:
        print(f"Unpacking {ifs_file.name}...")
        unpack(ifs_file, unpacked)
    print("Unpack completed.")

    analyze_jacket_t_data(data_storage)
