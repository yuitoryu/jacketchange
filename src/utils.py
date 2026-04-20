from pathlib import Path
import re
from typing import cast
from beartype import beartype
import xml.etree.ElementTree as ET
import json
from tqdm import tqdm
import shutil

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
    print(f'Analysis completed. Result has been written to {str(index_file_path / 'jacket.json')}.')
    
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
    print(f'Analysis completed. Result has been written to {str(index_file_path / 'difficulty.json')}.')
            
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
    
@beartype
def copy_jacket_to_other_difficulty(source_diff: int, target_diff: int, song_id: str, jacket_t_loc: dict[str, str], sdvx_path: Path) -> None:
    copy_regular_jacket_to_other_difficulty(source_diff, target_diff, song_id, sdvx_path)

@beartype
def copy_regular_jacket_to_other_difficulty(source_diff: int, target_diff: int, song_id: str, sdvx_path: Path) -> None:
    music_path = Path('data/music')
    song_path = find_song_folder(music_path, song_id)
    if song_path is None:
        raise Exception('Music data does not exist')
    
    basic_name = f'jk_{song_id}_'
    suffices = ['.png', '_b.png', '_s.png']
    for suffix in suffices:
        source_path = song_path / (basic_name + str(source_diff) + suffix)
        target_path = song_path / (basic_name + str(target_diff) + suffix)
        shutil.copy2(source_path, target_path)
    
@beartype
def copy_t_jacket_to_other_difficulty(source_diff: int, target_diff: int, song_id: str, jacket_t_loc: dict[str, str]) -> None:    
    ifs_id = jacket_t_loc[str(target_diff)]
    root = Path('data/ifs_unpacked')
    basic_name = f'jk_{song_id}_'
    suffix = '_t.png'
    source_path = root / ( basic_name + str(source_diff) + suffix )
    target_path = root / ( basic_name + str(target_diff) + suffix )
    shutil.copy2(source_path, target_path)