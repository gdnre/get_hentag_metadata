import io
import re
import os
import shutil
import hashlib

regex_ehviewer_filename_start = r'^\d+- *'
compress_extension = (r'.zip', r'.7z', r'.rar')
long_path = '\\\\?\\'


def get_rename_dir_name(original_name: str) -> str | None:  # 获取去除ehview下载的文件夹前面的id的文件名
    """
    返回ehviewer文件去除前缀后的文件名
    :param original_name: 原始文件名
    :return: 如果有匹配的前缀， 返回去除前缀的文件名，如果没有，返回None
    """
    if re.match(regex_ehviewer_filename_start, original_name, flags=0):
        return re.sub(regex_ehviewer_filename_start, '', original_name, count=1, flags=0)
    return None


def compress_file(file_path, target_dir, rename_file=None, extension_name='zip', dry_run: bool = False):
    """
    压缩单个文件夹，不能压缩文件
    :param file_path: 要压缩的文件夹绝对路径
    :param target_dir: 要压缩到的目标路径
    :param rename_file: 压缩文件名，不输入则为文件夹名，不包含扩展名
    :param extension_name: 压缩文件的扩展名
    :param dry_run: true为不实际执行压缩
    :return:
    """
    if os.path.isdir(file_path):
        if rename_file:
            file_name = rename_file
        else:
            file_name = os.path.basename(file_path)
        final_name = os.path.join(target_dir, file_name)
        return shutil.make_archive(final_name, extension_name, file_path, dry_run=dry_run)
    else:
        print('压缩文件夹失败，源文件夹路径错误')


def is_pic_dir(dir_path):
    """
    判断文件夹内是否'有且只有'非压缩文件，用来判断是否要对文件夹执行压缩
    """
    if not os.path.isdir(dir_path):
        return False
    for root, dirs, files in os.walk(dir_path):
        if (not dirs) and files and (not any(s.endswith(compress_extension) for s in files)):
            return True
        return False  # 只循环1次


def is_compress_file(file_path):
    if os.path.isfile(file_path) and file_path.endswith(compress_extension):
        return 1


def compress_manga_dir_to(manga_dir, target_dir, create_if_not_exist=False):
    """
    将文件夹格式的文件打包并放到目标目录
    :param manga_dir: 要处理的文件夹，包含漫画的文件夹所在的文件夹，自动处理子文件夹
    :param target_dir: 要存放到的目标路径
    :param create_if_not_exist: 目标路径不存在是否自动创建
    :return:
    """
    success_num = 0
    if not os.path.isdir(target_dir):
        if not create_if_not_exist:
            print(f'[{target_dir}]不存在或不为文件夹')
            return
        os.makedirs(target_dir, exist_ok=True)

    if os.path.isdir(manga_dir):
        i = 0
        for root, dirs, files in os.walk(manga_dir):
            if is_pic_dir(root):
                i += 1
                dir_name = os.path.basename(root)
                target_name = get_rename_dir_name(dir_name)
                target_path = compress_file(root, target_dir, target_name, dry_run=True)
                if os.path.exists(target_path):
                    print(i, f'文件已存在>>>{target_path}')
                    continue
                print(i, f'开始压缩>>>{dir_name}', end='')
                compress_file(root, target_dir, target_name)
                success_num += 1
                print(f' 压缩并存储文件成功>>>{target_path}')
        print(f'成功处理并压缩文件数量：{success_num}')
        return success_num
    else:
        print(f'{manga_dir}必须为存在的文件夹')


def get_id(file_path):  # 使用sha-1计算文件id
    if os.path.isfile(file_path):
        sha1_hash = hashlib.sha1()
        with open(file_path, 'rb') as file:
            sha1_hash.update(file.read(512000))  # 取文件的前512KB作为id
        return sha1_hash.hexdigest()


def create_hard_link(file_path, root_path, *sub_path, auto_create_dir=False):
    """
    为文件创建硬链接，注意文件和目标路径必须在同一分区
    :param file_path:  文件的路径
    :param root_path: 要链接到的文件(夹)，输入文件或文件夹取决于是否使用sub_path
    :param sub_path: 基于root_path创建子文件夹(及文件)，比如链接到/home/sub/test.txt时，root_path='/home',sub_path='/sub/test.txt',子路径可拆分，按顺序即可
    :param auto_create_dir: 如果文件夹不存在，是否自动创建
    :return: 如果成功创建，返回硬链接的路径，如果已存在文件，返回-1，其它情况返回none
    """
    if not os.path.isfile(file_path):
        print('只能为文件创建硬链接，文件不存在或不为文件')
        return
    # 判断file_path和root_path是否在同一分区，不同分区无法创建硬链接
    drive1, _temp = os.path.splitdrive(os.path.abspath(file_path))
    drive2, _temp = os.path.splitdrive(os.path.abspath(root_path))
    if drive1 != drive2:
        print(f'分区不同不能创建硬链接：{drive1},{drive2}')
        return 0
    final_path = os.path.join(root_path)
    if sub_path:
        for p in sub_path:
            final_path = os.path.join(final_path, p)
    dir_name = os.path.dirname(final_path)
    if not os.path.exists(dir_name):
        if auto_create_dir:
            os.makedirs(dir_name)
        else:
            print('没有对应的目录，需要先手动创建目录')
            return
    if os.path.exists(final_path):
        print('文件已存在，跳过')
        return -1
    os.link(file_path, final_path)
    return final_path


def write_to_file(text_to_write, file_path, cover=False):
    try:
        if cover:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_to_write)
        else:
            with open(file_path, 'x', encoding='utf-8') as f:
                f.write(text_to_write)
        return file_path
    except FileExistsError:
        print(f'文件{file_path}已存在')
    except io.UnsupportedOperation and TypeError:
        os.remove(file_path)