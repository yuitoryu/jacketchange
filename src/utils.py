from pathlib import Path
import re
from typing import cast
from beartype import beartype
import xml.etree.ElementTree as ET
import json
from tqdm import tqdm
import shutil
import copy
from .imgprocess import resize

class SongNotExistError(Exception):
    def __init__(self, song_id: str):
        self.message = f'ID {song_id} does not exist.'
        super().__init__(self.message)

@beartype
def find_jacket_files(graphics_path:  Path) -> list[Path]:
    pattern = re.compile(r"^s_jacket(?!00)[0-9]{2}\.ifs$")
    return [
        f
        for f in graphics_path.iterdir()
        if f.is_file() and pattern.match(f.name)
    ]

@beartype    
def find_unpacked_ifs(unpacked_path: Path) -> list[Path]:
    pattern = re.compile(r"^s_jacket(?!00)[0-9]{2}_ifs$")
    return [
        f
        for f in unpacked_path.iterdir()
        if f.is_dir() and pattern.match(f.name)
    ]

@beartype
def analyze_jacket_t_data(data: Path) -> None:
    index_dict : dict[str, dict[int, str]] = dict()
    
    unpacked = data / 'ifs_unpacked'
    index_file_path = data / 'index'
    index_file_path.mkdir(parents=True, exist_ok=True)
    fp = open(index_file_path / 'jacket.json', 'w')
    
    print('Start analyzing jacket_t usage...')
    for fd in tqdm(find_unpacked_ifs(unpacked)):
        # 获取当前文件夹id
        pattern = re.compile(r"^s_jacket(?!00)([0-9]{2})_ifs$")
        folder_id = cast(re.Match, pattern.fullmatch(fd.name)).group(1)
        
        # 读取xml文件获取所有曲绘文件名
        xml_path = fd / 'tex' / 'texturelist.xml'
        names = get_image_names(xml_path)
        
        # 提取id和难度信息并写入infos
        infos = extract_info(names)
        write_index(infos, index_dict, folder_id)

    json.dump(index_dict, fp, indent=4, ensure_ascii=False, sort_keys=True)
    fp.close()
    print(f"Analysis completed. Result has been written to {index_file_path / 'jacket.json'}.")
    
@beartype
def extract_info(names: list[str]) -> list[tuple[str, str]]:
    pattern = re.compile(r"^jk_(\d{4})_([1-6])_t$")
    lst = []
    append = lst.append
    
    for name in names:
        m = pattern.fullmatch(name)
        if not m:
            continue

        append((m.group(1), m.group(2)))
        
    return lst

@beartype
def write_index(infos: list[tuple[str, str]], index_dict : dict[str, dict[int, str]], folder_id: str) -> None:
    for info in infos:
        id, diff = info
        index_dict.setdefault(id, {})[int(diff)] = folder_id
        
@beartype
def get_image_names(xml_path: Path) -> list[str]:
    xml_path = Path(xml_path)
    root = ET.parse(xml_path).getroot()

    return[
        name
        for image in root.iter("image")
        if (name := image.get("name")) is not None
    ]

@beartype
def analyze_all_song_difficulty(sdvx_path: Path, data_storage: Path) -> None:
    music_folder = sdvx_path / 'data/music'
    pattern = re.compile(r"^(?P<id>[0-8][0-9]{3})(?:_[^_]+){2,}$")
    diff_pattern = re.compile(r"^.+(?P<tag>1n|2a|3e|4i|5m|6u)\.vox$")
    
    # Set up index file for recording difficulties of songs
    index_file_path = data_storage / 'index'
    index_file_path.mkdir(parents=True, exist_ok=True)
    record: dict[str, list[int]] = dict()
    fp = open(index_file_path / 'difficulty.json', 'w')
    

    # 遍历所有歌曲解析难度
    print('Start analyzing difficuly data...')
    for music in tqdm(music_folder.iterdir()):
        if not music.is_dir():
            continue
        match = pattern.match(music.name)
        if match:
            id = match.group('id')
            fetch_diff_list(music, id, diff_pattern, record)
            
    # 写入index.json
    json.dump(record, fp, indent=4, ensure_ascii=False, sort_keys=True)
    fp.close()
    print(f"Analysis completed. Result has been written to {index_file_path / 'difficulty.json'}.")
            
@beartype            
def fetch_diff_list(music: Path, id: str, pattern: re.Pattern[str], record: dict[str, list[int]]) -> None:
    lst = []
    for file in music.iterdir():
        if not file.is_file():
            continue
        match = pattern.match(file.name)
        if match:
            lst.append(match.group('tag'))
    record[id] = [int(s[0]) for s in lst]

def find_song_folder(music_path: Path, song_id: str) -> Path | None:
    pattern = re.compile(rf"^{song_id}(?:_[^_]+){{2,}}$")
    for fd in music_path.iterdir():
        match = pattern.match(fd.name)
        if match:
            return fd
    raise 

@beartype
def ensure_song_folder_copied(song_id: str, sdvx_path: Path, data_storage: Path) -> Path:
    source_music_path = sdvx_path / 'data' / 'music'
    source_song_path = find_song_folder(source_music_path, song_id)
    if source_song_path is None:
        raise FileNotFoundError(f'Music data does not exist for song {song_id}')

    copied_music_path = data_storage / 'music'
    copied_music_path.mkdir(parents=True, exist_ok=True)
    copied_song_path = copied_music_path / source_song_path.name

    if not copied_song_path.exists():
        shutil.copytree(source_song_path, copied_song_path)

    return copied_song_path
    
@beartype
def copy_jacket_to_other_difficulty(
    source_diff: int,
    target_diff: int,
    song_id: str,
    jacket_t_loc: dict[str, str],
    sdvx_path: Path,
    data_storage: Path,
) -> None:
    song_path = ensure_song_folder_copied(song_id, sdvx_path, data_storage)
    copy_regular_jacket_to_other_difficulty(source_diff, target_diff, song_id, song_path)
    copy_t_jacket_to_other_difficulty(
        source_diff,
        target_diff,
        song_id,
        jacket_t_loc,
        data_storage,
    )

@beartype
def copy_regular_jacket_to_other_difficulty(source_diff: int, target_diff: int, song_id: str, song_path: Path) -> None:
    basic_name = f'jk_{song_id}_'
    suffices = ['.png', '_b.png', '_s.png']
    for suffix in suffices:
        source_path = song_path / (basic_name + str(source_diff) + suffix)
        target_path = song_path / (basic_name + str(target_diff) + suffix)
        shutil.copy2(source_path, target_path)
    
@beartype
def copy_t_jacket_to_other_difficulty(
    source_diff: int,
    target_diff: int,
    song_id: str,
    jacket_t_loc: dict[str, str],
    data_storage: Path,
) -> None:
    ifs_id = jacket_t_loc[str(source_diff)]
    root = data_storage / 'ifs_unpacked' / f's_jacket{ifs_id}_ifs' / 'tex'
    basic_name = f'jk_{song_id}_'
    suffix = '_t.png'
    source_path = root / ( basic_name + str(source_diff) + suffix )
    target_path = root / ( basic_name + str(target_diff) + suffix )
    shutil.copy2(source_path, target_path)
    
    xml_path = root / 'texturelist.xml'
    copy_image_node_in_xml(xml_path, source_path, target_path)

@beartype
def copy_image_node_in_xml(xml_path: Path, source_path: Path, target_path: Path) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    source_name = source_path.stem
    target_name = target_path.stem

    source_image = None
    target_image = None
    for image in root.iter("image"):
        if image.get("name") == source_name:
            source_image = image
        if image.get("name") == target_name:
            target_image = image

    if source_image is None:
        raise ValueError(f"Cannot find image node: {source_name}")

    if target_image is not None:
        if target_name != source_name and rects_equal(source_image, target_image):
            assign_new_image_rect(root, source_image, target_image)
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        return

    new_image = copy.deepcopy(source_image)
    new_image.set("name", target_name)
    assign_new_image_rect(root, source_image, new_image)

    parent = next((elem for elem in root.iter() if source_image in list(elem)), None)
    if parent is None:
        raise ValueError(f"Cannot find parent node for image: {source_name}")

    children = list(parent)
    idx = children.index(source_image)
    parent.insert(idx + 1, new_image)

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)


def parse_rect(node: ET.Element, tag_name: str) -> tuple[int, int, int, int]:
    rect_node = node.find(tag_name)
    if rect_node is None or rect_node.text is None:
        raise ValueError(f"Cannot find {tag_name} for image node {node.get('name')}")
    values = [int(value) for value in rect_node.text.split()]
    if len(values) != 4:
        raise ValueError(f"Invalid {tag_name} value for image node {node.get('name')}")
    return values[0], values[1], values[2], values[3]


def write_rect(node: ET.Element, tag_name: str, rect: tuple[int, int, int, int]) -> None:
    rect_node = node.find(tag_name)
    if rect_node is None:
        raise ValueError(f"Cannot find {tag_name} for image node {node.get('name')}")
    rect_node.text = f"{rect[0]} {rect[1]} {rect[2]} {rect[3]}"


def rects_equal(source_node: ET.Element, target_node: ET.Element) -> bool:
    return (
        parse_rect(source_node, "uvrect") == parse_rect(target_node, "uvrect")
        and parse_rect(source_node, "imgrect") == parse_rect(target_node, "imgrect")
    )


def find_image_by_name(root: ET.Element, image_name: str) -> ET.Element | None:
    for image in root.iter("image"):
        if image.get("name") == image_name:
            return image
    return None


def has_duplicate_rect(root: ET.Element, target_image: ET.Element) -> bool:
    target_rect = parse_rect(target_image, "imgrect")
    target_name = target_image.get("name")
    for image in root.iter("image"):
        if image is target_image or image.get("name") == target_name:
            continue
        if parse_rect(image, "imgrect") == target_rect:
            return True
    return False


def ensure_unique_image_rect(xml_path: Path, image_name: str) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    target_image = find_image_by_name(root, image_name)
    if target_image is None:
        raise ValueError(f"Cannot find image node: {image_name}")

    if has_duplicate_rect(root, target_image):
        assign_new_image_rect(root, target_image, target_image)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)


def ensure_song_image_rects_unique(xml_path: Path, song_id: str) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    pattern = re.compile(rf"^jk_{song_id}_[1-6]_t$")
    updated = False

    seen_rects: set[tuple[int, int, int, int]] = set()
    for image in root.iter("image"):
        name = image.get("name")
        if name is None or not pattern.fullmatch(name):
            continue

        current_rect = parse_rect(image, "imgrect")
        if current_rect in seen_rects:
            assign_new_image_rect(root, image, image)
            updated = True
            current_rect = parse_rect(image, "imgrect")
        seen_rects.add(current_rect)

    if updated:
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)


def assign_new_image_rect(root: ET.Element, source_image: ET.Element, target_image: ET.Element) -> None:
    source_imgrect = parse_rect(source_image, "imgrect")
    width = source_imgrect[1] - source_imgrect[0]
    height = source_imgrect[3] - source_imgrect[2]
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid imgrect size for image node {source_image.get('name')}")

    occupied: set[tuple[int, int, int, int]] = set()
    max_x2 = source_imgrect[1]
    max_y2 = source_imgrect[3]
    for image in root.iter("image"):
        imgrect = parse_rect(image, "imgrect")
        occupied.add(imgrect)
        max_x2 = max(max_x2, imgrect[1])
        max_y2 = max(max_y2, imgrect[3])

    max_x2 += width
    max_y2 += height

    for y in range(0, max_y2 + 1, height):
        for x in range(0, max_x2 + 1, width):
            candidate = (x, x + width, y, y + height)
            if candidate not in occupied:
                write_rect(target_image, "uvrect", candidate)
                write_rect(target_image, "imgrect", candidate)
                return

    raise ValueError(f"Unable to allocate a new atlas rect for {target_image.get('name')}")

@beartype
def sdvx_folder_checker(sdvx_path: Path) -> bool:
    data = sdvx_path / 'data'
    graphics = data / 'graphics'
    music = data / 'music'
    if graphics.exists() and music.exists():
        return True
    return False

@beartype
def replace_jacket(
    song_id: str,
    diff: int,
    pic_path: Path,
    sdvx_path: Path,
    data_storage: Path,
    ifs_id: str,
) -> None:
    imgs = resize(pic_path, allow_morphism=False) # [regular, big, small, transfer]
    root_name = f'jk_{song_id}_{diff}'
    song_folder = ensure_song_folder_copied(
        song_id=song_id,
        sdvx_path=sdvx_path,
        data_storage=data_storage,
    )
    
    suffices = ['', '_b', '_s'] # transfer另外处理
    for i, suffix in enumerate(suffices):
        name = root_name + suffix + '.png'
        imgs[i].save( song_folder / name)
        
    t_name = root_name + '_t.png'
    final_path = data_storage / 'ifs_unpacked' / f's_jacket{ifs_id}_ifs' / 'tex' / t_name
    imgs[-1].save(final_path)
    texturelist_path = final_path.parent / "texturelist.xml"
    ensure_unique_image_rect(texturelist_path, final_path.stem)
    ensure_song_image_rects_unique(texturelist_path, song_id)
        
@beartype
def craft_id(id: str) -> str:
    if not id.isnumeric() or int(id) >= 10000 or int(id) <= 0:
        raise ValueError("Song ID must be a positive integer below 10000!")
    return "0" * (4 - len(id)) + id

@beartype
def update_song_folders(sdvx_path: Path, data_path: Path):
    music_path = sdvx_path / 'data' / 'music'
    for fd in (data_path / 'music').iterdir():
        if not fd.is_dir():
           continue
        shutil.copytree(fd, music_path / fd.name, dirs_exist_ok=True)
