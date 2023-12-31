import sys
from my_package.my_db_class import *
from my_package.get_config import *


def init():
    global hentag_db, input_args
    if os.path.exists('config.ini'):
        config_replace_globals('config.ini', globals())
    hentag_db = MyHentagDB(db_path, table_name)
    input_args = sys.argv[1:]


def check_manga_root_path():
    if not os.path.isdir(library_root_path):
        print(RED, '警告，漫画库所在文件夹不存在，请退出后在config.ini设置library_root_path选项', CEND)
    else:
        print(f'漫画压缩包（漫画库）所在文件夹为{library_root_path}')
    if not os.path.isdir(sort_root_path):
        print(RED, '警告，漫画整理后存放文件夹不存在，请退出后在config.ini设置sort_root_path选项', CEND)
    else:
        print(f'漫画整理后存放文件夹为{sort_root_path}')


def main_processing(input_args):
    print(f'''============================进入主处理方法============================
当前脚本执行路径为{os.getcwd()}

{GREEN}如果传入参数运行脚本，执行压缩漫画文件夹操作，格式如下：

    python3 script.py 参数1 [参数2]
   
    参数1：下载下来的未打包漫画文件所在文件夹，会遍历子文件夹
    参数2：要存放到的文件夹，可选，默认为config.ini中设置的漫画库文件夹{CEND}
''')
    if input_args:
        if len(input_args) >= 2:
            compress_manga_dir_to(input_args[0], input_args[1])
            return
        elif len(input_args) == 1:
            compress_manga_dir_to(input_args[0], library_root_path)
            return

    check_manga_root_path()
    while not input_args:
        try:
            print(f'''--------------------------------------------------------------------
{GREEN}请输入数字来选择要执行的操作，ctrl+c可以强制退出：

   00.尝试清理数据库，如果数据库大小一直增大，需要尝试执行该操作
   01.修改ehviewer下载的漫画文件所在文件夹，不会更改config中的设置，本次会保存，下次打开不会保存设置，下同
   02.修改漫画库所在文件夹
   03.修改漫画分类后存放文件夹
   
    1.将漫画压缩后放到漫画库文件夹
    2.将漫画库中的文件信息导入数据库
   31.向hentag搜索漫画库中的漫画信息，最后重试出错的项
   32.向hentag搜索漫画库中的漫画信息，每项出错立刻重试，直到成功或超过最大次数
    4.分类整理漫画，根据作者名或团队名创建子文件夹为漫画分类，作者名优先
    5.输出需要手动输入数据的漫画信息到.csv文件
   61.将手动设置的作者名和团队名导入数据库
   62.将手动设置的搜索名导入数据库，并重置搜索错误标记列
    7.根据hentag_id下载网站上的元数据，存到数据库
    8.将数据库中的hentag元数据输出为info.json文件
    
等待输入,按字母q退出：{CEND}''')
            user_input = input('')
            if user_input.upper() == 'Q':
                print(f'检测到输入{user_input}，退出脚本')
                break
            elif user_input == '01':
                print(f'输入01，临时设置ehviewer下载文件所在文件夹，当前已设置的路径为：{ehviewer_dir_path}')
                temp_ehviewer_dir_path = input('输入路径，不更改请按/d：')
                while not os.path.isdir(temp_ehviewer_dir_path):
                    if temp_ehviewer_dir_path == "/d":
                        print('>>>ehviewer下载文件所在文件夹未更改')
                        break
                    temp_ehviewer_dir_path = input('路径不存在，请重新输入，不更改请按/d：')
                globals()['ehviewer_dir_path'] = temp_ehviewer_dir_path
                print(f'>>>ehviewer下载文件存放目录已修改为：{ehviewer_dir_path}')
            elif user_input == '02':
                print(f'输入02，临时设置漫画库所在文件夹，当前已设置的路径为：{library_root_path}')
                temp_library_root_path = input('输入路径，不更改请按/d：')
                while not os.path.isdir(temp_library_root_path):
                    if temp_library_root_path == "/d":
                        print('>>>漫画库所在文件夹未更改')
                        break
                    temp_library_root_path = input('路径不存在，请重新输入，不更改请按/d：')
                globals()['library_root_path'] = temp_library_root_path
                print(f'>>>漫画库所在文件夹已修改为：{library_root_path}')
            elif user_input == '03':
                print(f'输入03，临时设置漫画分类后存放文件夹，当前已设置的路径为：{sort_root_path}')
                temp_sort_root_path = input('输入路径，不更改请按/d：')
                while not os.path.isdir(temp_sort_root_path):
                    if temp_sort_root_path == "/d":
                        print('>>>漫画分类后存放文件夹未更改')
                        break
                    temp_sort_root_path = input('路径不存在，请重新输入，不更改请按/d：')
                globals()['sort_root_path'] = temp_sort_root_path
                print(f'>>>漫画分类后存放文件夹已修改为：{sort_root_path}')
            elif user_input == '1':
                print('输入1，将漫画打包后放入漫画库，检查设置的路径>>>')
                while not os.path.isdir(library_root_path):
                    globals()['library_root_path'] = input('>>>漫画库所在文件夹不存在，请临时输入漫画库所在文件夹:')
                while not os.path.isdir(ehviewer_dir_path):
                    globals()['ehviewer_dir_path'] = input('>>>ehviewer下载的漫画所在文件夹不存在，请临时输入文件夹:')
                print(f'>>>源路径是{ehviewer_dir_path}\n>>>漫画库路径是{library_root_path}\n>>>开始处理')
                compress_manga_dir_to(ehviewer_dir_path, library_root_path)
                print('>>>将漫画存入漫画库，完毕')
            elif user_input == '2':
                print('输入2，将漫画信息放入数据库，检查设置的路径>>>')
                while not os.path.isdir(library_root_path):
                    globals()['library_root_path'] = input('>>>漫画库所在文件夹不存在，请临时输入漫画库所在文件夹:')
                print(f'>>>漫画库路径是{library_root_path}\n>>>开始处理')
                hentag_db.store_files_into_db(library_root_path)
                print('>>>将漫画信息导入数据库，完毕')
            elif user_input == '31':
                print('输入31，向hentag搜索漫画信息>>>')
                hentag_db.search_hentag_info_all(timeout1, timeout2, timeout3, wait_time, headers=headers)
                print('>>>搜索完毕，如果仍有请求失败的，请再次执行该操作')
            elif user_input == '32':
                print('输入32，向hentag搜索漫画信息>>>')
                hentag_db.search_hentag_info_all_each(max_retry_count, timeout_rule, wait_time, headers=headers)
                print('>>>搜索完毕，如果仍有请求失败的，请再次执行该操作')
            elif user_input == '4':
                while not os.path.isdir(sort_root_path):
                    globals()['sort_root_path'] = input('>>>漫画分类的目标文件夹不存在，请临时输入文件夹:')
                print(f'>>>漫画分类文件夹是{sort_root_path}>>>开始处理')
                hentag_db.arrange_files_in_db(sort_root_path, sub_path_root, sub_path_artist, sub_path_group,
                                              sub_path_unsorted)
                print('>>>将漫画分类整理，完毕')
            elif user_input == '5':
                print(f'输入5，导出需要手动设置的漫画信息>>>')
                hentag_db.output_data()
                print('>>>导出完毕，在两个文件中分别手动设置作者/团队名，搜索名')
            elif user_input == '61':
                print(f'输入61，将手动设置的作者名和团队名导入数据库>>>')
                hentag_db.import_change_data(manga_unsort_csv_parh)
                print('>>>导入完毕，信息被强制更新为csv文件中的数据')
            elif user_input == '62':
                print(f'输入62，将手动设置的搜索名导入数据库，并重置搜索错误标记列>>>')
                hentag_db.import_change_data(search_no_result_csv_path, reset_flag=True)
                print('>>>导入完毕，信息被强制更新为csv文件中的数据')
            elif user_input == '00':
                print(f'输入00，尝试清理数据库>>>')
                hentag_db.try_clear_up_db()
                print('>>>执行清理命令完毕')
            elif user_input == '7':
                print('输入7，下载hentag元数据>>>')
                hentag_db.request_hentag_metadata_all_each(max_retry_count, timeout_rule, wait_time,headers)
                print('>>>下载并导入完毕，如果仍有请求失败的，请再次执行该操作')
            elif user_input == '8':
                print('输入8，将数据库中的hentag元数据输出为info.json文件>>>')
                while not os.path.isdir(sort_root_path):
                    globals()['sort_root_path'] = input('>>>漫画分类的目标文件夹不存在，请临时输入文件夹:')
                hentag_db.save_hentag_metadata_to_json_file(sort_root_path)
                print(f'>>>元数据已输出到{sort_root_path}的hentag_metadata文件夹')
            else:
                print(f'{RED}输入>{user_input}<，没有对应操作，请重新输入{CEND}')
        except KeyboardInterrupt:
            print(f'{RED}>>>检测到强制退出指令，退出当前操作{CEND}')
            continue
    print('============================退出主处理方法============================')
    hentag_db.close_db()


db_path = 'file_list.db'
if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 设置脚本的执行路径为当前脚本所在文件夹，防止使用相对路径出问题
    os.chdir(script_dir)
    try:
        init()
        main_processing(input_args)
    except KeyboardInterrupt:
        print('强制退出脚本')
        hentag_db.close_db()
