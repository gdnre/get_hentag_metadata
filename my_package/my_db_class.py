import sqlite3
import time
from csv import writer, reader
from my_package.hentag_text_processing import *
from my_package.request_from_hentag_website import *
from my_package.manga_file_processing import *

table_name = 'file_list'
ehviewer_dir_path = ''
library_root_path = ''
sort_root_path = ''
sub_path_root = 'hentag'
sub_path_artist = 'artist'
sub_path_group = 'group'
sub_path_unsorted = 'unsorted'
manga_unsort_csv_parh = 'manga_unsort.csv'
search_no_result_csv_path = 'manga_search_no_result.csv'

wait_time = 2
timeout1 = 5
timeout2 = 10
timeout3 = 15
max_retry_count = 5
timeout_rule = [[1, 10], [2, 5]]


class MyDB:
    def __init__(self, db_path):
        """
        :param db_path: 带后缀的数据库名/路径，不存在将自动创建；默认在脚本当前目录下，否则目录必须已存在。
        """
        root_path = os.path.dirname(os.path.abspath(db_path))
        if os.path.exists(root_path):
            self.db_path = db_path
            self.conn = sqlite3.connect(self.db_path, isolation_level=None)
            self.cursor = self.conn.cursor()
            print(f'已连接到数据库{db_path}')
        else:
            raise ValueError('指定的数据库目录不存在，无法自动新建数据库文件')

    def connect_db(self):
        self.conn = sqlite3.connect(self.db_path, isolation_level=None)
        self.cursor = self.conn.cursor()
        return self.conn

    def close_db(self):
        self.conn.close()
        print('已关闭数据库连接')

    def del_table(self, table_name):
        """
        删除数据表
        :param table_name: 要删除的表名
        :return: 成功删除的数据表名，不存在则打印错误信息，返回none
        """
        try:
            self.cursor.execute(f'DROP TABLE {table_name};')
            return table_name
        except sqlite3.OperationalError as e:
            print(e)
            return

    def is_col_exists(self, table_name, column_name):
        """
        检查数据库中列是否存在,返回bool
        """
        self.cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [info[1] for info in self.cursor.fetchall()]
        return column_name in columns

    def get_tables(self):
        self.cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = [column[0] for column in self.cursor.fetchall()]
        i = 0
        return tables

    def get_columns(self, table_name: str = None):
        """
        获取数据表中的列名
        :param table_name: 要查找的数据表名，不输入则返回所有数据表中的列
        :return: 如果输入了数据表名，返回其中列的列表，没有数据表则为空列表；如果没输入，则返回key为数据表名、value为列的列表的字典，没有数据表则返回空字典
        """
        if table_name:
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [info[1] for info in self.cursor.fetchall()]
            if columns:
                return columns
            else:
                return []
        else:
            tables = self.get_tables()
            if tables:
                dict_columns = {}
                for table in tables:
                    table_name = table
                    self.cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = [info[1] for info in self.cursor.fetchall()]
                    dict_columns[table_name] = columns
                return dict_columns
            else:
                return {}

    def add_col_to_db(self, table_name, column_name, datatype='TEXT', default=None):
        """
        向表中添加行,返回添加的行名
        :param table_name:要操作的表名
        :param column_name:要添加的列名
        :param datatype:列的默认数据类型
        :param default:列的默认值
        :return:列名
        """
        if default is not None:
            default_execute = f' DEFAULT {default}'
        else:
            default_execute = ''
        if not self.is_col_exists(table_name, column_name):
            self.cursor.execute(f'''
        ALTER TABLE {table_name} ADD {column_name} {datatype}{default_execute};
        ''')
            return column_name

    def del_col_in_db(self, table_name, column_name):
        """
        在表中删除列
        :param table_name: 要操作的表名
        :param column_name: 要删除的列名
        :return:
        """
        if self.is_col_exists(table_name, column_name):
            self.cursor.execute(f'''
        ALTER TABLE {table_name} DROP COLUMN {column_name};
        ''')
            return column_name

    def get_data_from(self, table_name, *column_names, search_operate: str = "AND", wildcard: bool = False,
                      fetch: str = "all", limit: int = -1, offset: int = 0, search_conditions_execute: str = None,
                      **search_conditions):  # 获取table_name数据表的column_names列的数据,可使用筛选
        """
        返回数据表指定列的数据，或根据条件筛选符合条件的列返回
        :param table_name: 要在哪个表内查找
        :param column_names: 要返回的列
        :param search_operate: 查询条件，AND或OR，默认为AND,
        :param wildcard: 是否使用通配符，默认为false
        :param fetch: all或one，返回全部结果还是一条结果，默认返回全部结果
        :param limit: 返回几条数据，只在fetch为all时有用，默认返回全部
        :param offset: 返回数据的偏移量，即从第几条数据开始返回，默认为0
        :param search_conditions_execute: 查找条件的sql语句，放在WHERE之后LIMIT之前，search_conditions无法满足需求时使用
        :param search_conditions: 查找的条件，参数格式为：列名=条件
        :return: 返回查询到的数据，注意fetch为all和one时返回结果的数据类型不同，没有结果时返回[]
        """
        try:
            table_name = str(table_name)
            columns = ','.join(map(str, column_names))
            if search_conditions_execute:
                get_execute = f'SELECT {columns} FROM {table_name} WHERE {search_conditions_execute} LIMIT {limit} OFFSET {offset}'
                self.cursor.execute(get_execute)
            elif search_conditions:
                keywords = [f'{key}=?' for key in search_conditions]
                if wildcard:
                    keywords = [f'{key} LIKE ?' for key in search_conditions]
                arg = [search_conditions[key] for key in search_conditions]
                keywords = f' {search_operate} '.join(keywords)
                get_execute = f'SELECT {columns} FROM {table_name} WHERE {keywords} LIMIT {limit} OFFSET {offset}'
                self.cursor.execute(get_execute, arg)
            else:
                get_execute = f'SELECT {columns} FROM {table_name} LIMIT {limit} OFFSET {offset}'
                self.cursor.execute(get_execute)
            if fetch == "one":
                return self.cursor.fetchone()
            return self.cursor.fetchall()
        except sqlite3.OperationalError as e:
            print("获取数据库数据出错", e)
            return []

    def update_data_from(self, table_name: str, search_param: dict, search_operate: str = "AND", force_update=False,
                         wildcard=False,
                         **change_data_param):
        """
        替换数据库中的对应数据
        :param table_name:
        :param search_param: 查询关键字，字典格式，格式为 列名:对应的数据
        :param search_operate: 查询条件，AND或OR，默认为AND,
        :param force_update: 如果列中已有数据，是否强制更新
        :param wildcard: 未使用，是否使用通配符
        :param change_data_param: 要替换的列的数据，格式为：列名=数据
        :return: 成功返回1
        """
        try:
            current_data = self.get_data_from(table_name, *change_data_param, search_operate=search_operate,
                                              wildcard=wildcard, **search_param)
            if not current_data:  # 如果没有对应列，返回
                return

            change_cols = [f'{change_col}=?' for change_col in change_data_param]
            change_cols_execute = ','.join(change_cols)
            if wildcard:
                search_cols = [f'{search_col} LIKE ?' for search_col in search_param]
            else:
                search_cols = [f'{search_col}=?' for search_col in search_param]
            search_cols_execute = f' {search_operate} '.join(search_cols)

            change_args = [change_data for change_data in change_data_param.values()]
            search_args = [search_keyword for search_keyword in search_param.values()]
            execute_args = change_args + search_args

            update_execute = f'UPDATE {table_name} SET {change_cols_execute} WHERE {search_cols_execute};'

            if not force_update:  # 如果选择不强制更新，判断所选任意列是否有数据
                for row in current_data:
                    for d in row:
                        if d:
                            p_cols = ','.join([key for key in change_data_param])
                            print(f'列[{p_cols}]中符合条件的行有数据，跳过')
                            return
            self.cursor.execute(update_execute, execute_args)
            return 1  # 数据库中没有对应的行也会成功执行
        except sqlite3.OperationalError as e:
            print("更新数据库数据出错", e)
            return

    def add_row_into(self, table_name, **cols_and_data):
        """
        向表中添加行
        :param table_name: 表名
        :param cols_and_data: 要往哪列添加什么数据
        :return: 无返回值，添加失败会报错
        """
        add_cols = [col for col in cols_and_data.keys()]
        add_args = [add_data for add_data in cols_and_data.values()]
        _arg = ['?' for arg in add_args]

        cols_execute = ', '.join(add_cols)
        arg_execute = ', '.join(_arg)

        final_execute = f'INSERT INTO {table_name} ({cols_execute}) VALUES ({arg_execute});'
        self.cursor.execute(final_execute, add_args)

    def try_clear_up_db(self):
        self.cursor.execute('VACUUM;')


class MyHentagDB(MyDB):
    def __init__(self, db_path, table_name=table_name):
        super().__init__(db_path)
        self.table_name = table_name
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id               TEXT    PRIMARY KEY,
                file_name        TEXT,
                hentag_title     TEXT,
                search_name      TEXT,
                artist           TEXT,
                _group           TEXT,
                tags             TEXT,
                file_path        TEXT,
                hentag_id        TEXT,
                hentag_text      TEXT,
                requested        INTEGER,
                search_no_result INTEGER,
                hentag_metadata  TEXT
            );
            ''')

    def get_data(self, *column_names, operate: str = "AND", wildcard: bool = False,
                 fetch: str = "all", limit: int = -1, offset: int = 0, search_conditions_execute=None,
                 **conditions):
        """
        返回self.table_name中指定列的数据，或根据条件筛选符合条件的列返回
        :param column_names: 要返回的列
        :param operate: 查询条件，AND或OR，默认为AND,
        :param wildcard: 是否使用通配符，默认为false
        :param fetch: all或one，返回全部结果还是一条结果，默认返回全部结果
        :param limit: 返回几条数据，只在fetch为all时有用，默认返回全部
        :param offset: 返回数据的偏移量，即从第几条数据开始返回，默认为0
        :param conditions: 查找的条件，参数格式为：列名=条件
        :return: 返回查询到的数据，注意fetch为all和one时返回结果的数据类型不同
        """
        result = self.get_data_from(self.table_name, *column_names, search_operate=operate, wildcard=wildcard,
                                    fetch=fetch, limit=limit, offset=offset,
                                    search_conditions_execute=search_conditions_execute, **conditions)
        return result

    def update_data(self, search_id, force_update=False,
                    **change_data_param):
        """

        :param search_id: 文件的id
        :param force_update: 如果已有数据，是否仍更新
        :param change_data_param: 要更新的列和对应数据，格式为：列名=数据
        :return: 成功返回1
        """
        result = self.update_data_from(self.table_name, {'id': search_id},
                                       force_update=force_update, wildcard=False, **change_data_param)
        return result

    def is_file_exist_in_db(self, search_keyword, return_cols='id') -> str | bool:
        """
        查找{table_name}的id/file_name列中是否存在等于{search_keyword}的数据：
        :param search_keyword: 要查找的id或者文件名
        :param return_cols: 要返回的列，默认为id，可以使用'id,file_name'的格式返回多列
        :return: 返回查找到的第一个结果
        """
        self.cursor.execute(f'SELECT {return_cols} FROM {self.table_name} WHERE id=? OR file_name=?',
                            (search_keyword, search_keyword))
        search_result = self.cursor.fetchone()
        if search_result:
            search_result, = search_result
            return search_result
        else:
            return False

    def __store_file_into_db(self, file_path):
        """
        将单个压缩文件的信息添加入数据库
        :param file_path:
        :return:
        """
        try:
            file_path = os.path.abspath(file_path)
            if is_compress_file(file_path):
                file_id = get_id(file_path)
                # 如果已经有id对应的文件
                file_path_in_db = self.is_file_exist_in_db(file_id, 'file_path')
                if file_path_in_db:
                    #print(f'[{file_id}]已存在>>>', end='')
                    if file_path_in_db != file_path:
                        #print(f'文件路径更新为[{file_path}]')
                        self.update_data(file_id, force_update=True, file_path=file_path)
                        return file_id
                    #print('文件路径不需要更新')
                    return file_id
                # 如果没有id对应的文件
                file_name = os.path.basename(file_path)
                self.cursor.execute(f'INSERT INTO {self.table_name} (id, file_name, file_path) VALUES (?, ?, ?);',
                                    (file_id, file_name, file_path))
                # print(f'文件[{file_id}]成功添加')
                return file_id
            #print(f'[{file_path}]不为压缩文件，无法添加入数据库')
        except OSError as e:
            print(e)

    def store_files_into_db(self, target_path):  # 自动将路径下压缩文件加入数据库
        """
        自动将路径下压缩文件加入数据库
        :param target_path:
        :return:
        """
        success_num = 0
        i = 0
        if os.path.exists(target_path):
            if os.path.isfile(target_path):
                file_id = self.__store_file_into_db(target_path)
                if file_id:
                    success_num += 1
                return success_num
            elif os.path.isdir(target_path):
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        i += 1
                        file_path = os.path.join(root, file)
                        print(i,f'遍历到{file_path}>>>',end=" ")
                        file_id = self.__store_file_into_db(file_path)
                        if file_id:
                            success_num += 1
                            print('处理成功>>>')
                        else:
                            print('处理失败>>>')
                print(f'成功导入或更新信息{success_num}条')
                return success_num
            else:
                print("当前路径不存在压缩文件")
        else:
            print("将压缩文件加入数据库错误：路径不存在")

    def search_hentag_info_one(self, db_id, col_to_search='file_name', ignore_requested=False, timeout=10,
                               headers=headers):
        get_cols_name = [f'{col_to_search}', 'requested']
        db_data = self.get_data(*get_cols_name, fetch='one', id=db_id)
        search_name, requested, = db_data
        if (not ignore_requested and requested) or not search_name:
            print('已经提取过数据或需要设置查找名')
            return
        if str(search_name).endswith(compress_extension):
            search_name, extension = os.path.splitext(search_name)
        print(f'开始查找{search_name}>>>', end='')
        search_return = get_hentag_search_result(search_name, timeout_seconds=timeout, request_headers=headers)
        if search_return:
            print('收到返回数据>>>', end='')
            hentag_text = get_result_by_hentag_text(search_return)
            if hentag_text:
                print(f'搜索成功，开始提取信息>>>', end='')
                hentag_id = get_hentag_id_from_result(hentag_text)
                hentag_title = get_title_from_result(hentag_text)
                artist, group = get_artist_and_group_from_result(hentag_text)
                tags = get_tags_from_result(hentag_text)
                self.update_data(db_id, force_update=False, artist=artist, _group=group)
                self.update_data(db_id, force_update=True, hentag_id=hentag_id, hentag_title=hentag_title,
                                 tags=tags, hentag_text=hentag_text, requested=1)
                print('提取信息完毕')
                return db_id
            else:
                print('返回数据中没有找到结果')
                if col_to_search == 'search_name':
                    search_no_result = 2
                else:
                    search_no_result = 1
                self.update_data(db_id, force_update=True, search_no_result=search_no_result)
        print('没有收到返回数据，请求失败')

    def search_hentag_info_all(self, timeout1=timeout1, timeout2=timeout2, timeout3=timeout3, wait_time=wait_time,
                               headers=headers):
        """
        依次查找数据库中漫画的hentag信息，出错的会跳过，下次再重试
        :param timeout1: 第一次请求的超时时间
        :param timeout2: 第二次请求的超时时间
        :param timeout3: 同上
        :param wait_time: 请求成功后的等待时间，防止请求过于频繁
        :return:
        """
        get_cols_name = ['id', 'file_name', 'search_name', 'requested', 'search_no_result']
        no_result_list = []
        request_fail_list = []
        no_result_num = 0
        skip_num = 0
        success_num = 0
        request_fail_num = 0
        print('第一遍请求：')
        i = 0
        for _id, file_name, search_name, requested, search_no_result in self.get_data(*get_cols_name):
            i += 1
            # 成功提取过信息的跳过
            if requested:
                print(i, f'{_id}已获取过数据')
                skip_num += 1
                continue
            # 有过请求但没有得到结果的跳过
            if search_no_result and not search_name:
                no_result_list.append(_id)
                print(i, f'{_id}无法根据文件名搜索出结果，请手动设置搜索名')
                no_result_num += 1
                continue
            if search_no_result == 2:
                no_result_list.append(_id)
                print(i, f'{_id}无法根据搜索名搜索出结果，请重新设置搜索名')
                no_result_num += 1
                continue

            # 如果有搜索名，优先使用搜索名，将使用搜索名也无法得到结果的错误代码设为2
            search_no_result = 1
            if search_name:
                search_keyword = search_name
                search_no_result = 2
            elif str(file_name).endswith(compress_extension):
                search_keyword, extension = os.path.splitext(file_name)
            else:
                search_keyword = file_name

            # 开始请求数据,第一遍设置超时时间为5
            print(i, f'开始搜索{search_keyword}>>>', end='')
            search_return = get_hentag_search_result(search_keyword, timeout_seconds=timeout1, request_headers=headers)
            if search_return:  # 如果收到返回数据
                print('收到返回数据>>>', end='')
                hentag_text = get_result_by_hentag_text(search_return)
                if hentag_text:  # 如果返回数据中有结果
                    print(f'搜索成功，开始提取信息>>>', end='')
                    hentag_id = get_hentag_id_from_result(hentag_text)
                    hentag_title = get_title_from_result(hentag_text)
                    artist, group = get_artist_and_group_from_result(hentag_text)
                    tags = get_tags_from_result(hentag_text)
                    self.update_data(_id, force_update=False, artist=artist, _group=group)
                    self.update_data(_id, force_update=True, hentag_id=hentag_id, hentag_title=hentag_title,
                                     tags=tags, hentag_text=hentag_text, requested=1)
                    success_num += 1
                    print(f'提取信息完毕，等待{wait_time}秒')
                    time.sleep(wait_time)
                else:  # 如果返回数据中没有结果
                    no_result_list.append(_id)
                    no_result_num += 1
                    self.update_data(_id, force_update=True, search_no_result=search_no_result)
                    print(f'返回数据中没有找到结果，等待{wait_time}秒')
                    time.sleep(wait_time)
            else:  # 如果没有返回数据，之后要重试
                request_fail_list.append((_id, search_keyword, search_no_result))
                request_fail_num += 1
                print('没有收到返回数据，请求失败')
        print(
            f'第一遍请求结束，共处理{i}条数据，跳过{skip_num}条，成功{success_num}条，需要设置搜索名{no_result_num}条，请求失败{request_fail_num}条,请求失败列表中有{len(request_fail_list)}条数据')

        print(r'第二遍请求')
        j = 0
        request_fail_list_2 = []
        for _id, search_keyword, search_no_result in request_fail_list:
            j += 1
            # 开始请求数据,第二遍设置超时时间为7
            print(j, f'开始搜索{search_keyword}>>>', end='')
            search_return = get_hentag_search_result(search_keyword, timeout_seconds=timeout2, request_headers=headers)
            if search_return:  # 如果收到返回数据
                print('收到返回数据>>>', end='')
                hentag_text = get_result_by_hentag_text(search_return)
                if hentag_text:  # 如果返回数据中有结果
                    print(f'搜索成功，开始提取信息>>>', end='')
                    hentag_id = get_hentag_id_from_result(hentag_text)
                    hentag_title = get_title_from_result(hentag_text)
                    artist, group = get_artist_and_group_from_result(hentag_text)
                    tags = get_tags_from_result(hentag_text)
                    self.update_data(_id, force_update=False, artist=artist, _group=group)
                    self.update_data(_id, force_update=True, hentag_id=hentag_id, hentag_title=hentag_title,
                                     tags=tags, hentag_text=hentag_text, requested=1)
                    success_num += 1
                    request_fail_num -= 1
                    print(f'提取信息完毕，等待{wait_time}秒')
                    time.sleep(wait_time)
                else:  # 如果返回数据中没有结果
                    no_result_list.append(_id)
                    no_result_num += 1
                    self.update_data(_id, force_update=True, search_no_result=search_no_result)
                    print(f'返回数据中没有找到结果，等待{wait_time}秒')
                    time.sleep(wait_time)
            else:  # 如果没有返回数据，之后要重试
                request_fail_list_2.append((_id, search_keyword, search_no_result))
                print('没有收到返回数据，请求失败')
        print(
            f'第二遍请求共处理{j}条数据，包括上次共成功{success_num}条，需要设置搜索名{no_result_num}条，请求失败{request_fail_num}条,请求失败列表中还有{len(request_fail_list_2)}条数据')

        print('第三遍请求')
        k = 0
        request_fail_list_3 = []
        for _id, search_keyword, search_no_result in request_fail_list_2:
            k += 1
            # 开始请求数据,第三遍设置超时时间为10
            print(k, f'开始搜索{search_keyword}>>>', end='')
            search_return = get_hentag_search_result(search_keyword, timeout_seconds=timeout3, request_headers=headers)
            if search_return:  # 如果收到返回数据
                print('收到返回数据>>>', end='')
                hentag_text = get_result_by_hentag_text(search_return)
                if hentag_text:  # 如果返回数据中有结果
                    print(f'搜索成功，开始提取信息>>>', end='')
                    hentag_id = get_hentag_id_from_result(hentag_text)
                    hentag_title = get_title_from_result(hentag_text)
                    artist, group = get_artist_and_group_from_result(hentag_text)
                    tags = get_tags_from_result(hentag_text)
                    self.update_data(_id, force_update=False, artist=artist, _group=group)
                    self.update_data(_id, force_update=True, hentag_id=hentag_id, hentag_title=hentag_title,
                                     tags=tags, hentag_text=hentag_text, requested=1)
                    success_num += 1
                    request_fail_num -= 1
                    print(f'提取信息完毕，等待{wait_time}秒')
                    time.sleep(wait_time)
                else:  # 如果返回数据中没有结果
                    no_result_list.append(_id)
                    no_result_num += 1
                    self.update_data(_id, force_update=True, search_no_result=search_no_result)
                    print(f'返回数据中没有找到结果，等待{wait_time}秒')
                    time.sleep(wait_time)
            else:  # 如果没有返回数据，之后要重试
                print('没有收到返回数据，请求失败')
                request_fail_list_3.append((_id, search_keyword, search_no_result))
        print(
            f'第三遍请求共处理{k}条数据，本次执行脚本共成功{success_num}条，需要设置搜索名{no_result_num}条，请求失败{request_fail_num}条')
        return no_result_list, request_fail_list_3

    def search_hentag_info_all_each(self, max_retry_count=max_retry_count, timeout_rule=None,
                                    wait_time=wait_time, headers=headers):
        """
        尝试获取每条漫画的元数据，直到成功或者到最大尝试次数
        :param max_retry_count: 最大尝试次数
        :param timeout_rule: 超时时间，关于(次数,增加时间)的数组，比如(1,10)就是下1次，加10s，[(1, 10), (2, 5)]就是[10,15,20]，未进行设定的默认按最后的时间
        :param wait_time: 每次请求后的等待时间
        :return:
        """
        if timeout_rule is None:
            timeout_rule = timeout_rule
        get_cols_name = ['id', 'file_name', 'search_name', 'requested', 'search_no_result']
        timeout_array, no_result_list = [], []
        timeout_second, no_result_num, skip_num, success_num, request_fail_num, i = 0, 0, 0, 0, 0, 0
        # 根据规则得到每次请求的超时时间数组
        for count, timeout_time in timeout_rule:
            while count > 0:
                timeout_second += timeout_time
                timeout_array.append(timeout_second)
                count -= 1
        n = max_retry_count - len(timeout_array)
        while n > 0:
            n -= 1
            timeout_array.append(timeout_second)

        for _id, file_name, search_name, requested, search_no_result in self.get_data(*get_cols_name):
            i += 1
            # 成功提取过信息的，有过请求但没有得到结果的跳过
            if requested:
                print(i, f'{_id}已获取过数据')
                skip_num += 1
                continue
            if search_no_result and not search_name:
                no_result_list.append(_id)
                print(i, f'{_id}无法根据文件名搜索出结果，请手动设置搜索名')
                no_result_num += 1
                continue
            if search_no_result == 2:
                no_result_list.append(_id)
                print(i, f'{_id}无法根据搜索名搜索出结果，请重新设置搜索名')
                no_result_num += 1
                continue

            # 如果有搜索名，优先使用搜索名，将使用搜索名也无法得到结果的错误代码设为2
            search_no_result = 1
            if search_name:
                search_keyword = search_name
                search_no_result = 2
            elif str(file_name).endswith(compress_extension):
                search_keyword, extension = os.path.splitext(file_name)
            else:
                search_keyword = file_name

            print(i, f'开始搜索{search_keyword}>>>')
            search_return = None
            current_retry_count = 0

            while (not search_return) and (current_retry_count < max_retry_count):
                timeout_second = timeout_array[current_retry_count]
                current_retry_count += 1
                print(f'\t第{current_retry_count}遍尝试，超时时间设置为{timeout_second}>>>', end='')
                search_return = get_hentag_search_result(search_keyword, timeout_seconds=timeout_second,
                                                         request_headers=headers)
                if search_return:  # 如果收到返回数据
                    print('收到返回数据>>>', end='')
                    hentag_text = get_result_by_hentag_text(search_return)
                    if hentag_text:  # 如果返回数据中有结果
                        print(f'搜索成功，开始提取信息>>>', end='')
                        hentag_id = get_hentag_id_from_result(hentag_text)
                        hentag_title = get_title_from_result(hentag_text)
                        artist, group = get_artist_and_group_from_result(hentag_text)
                        tags = get_tags_from_result(hentag_text)
                        self.update_data(_id, force_update=False, artist=artist, _group=group)
                        self.update_data(_id, force_update=True, hentag_id=hentag_id, hentag_title=hentag_title,
                                         tags=tags, hentag_text=hentag_text, requested=1)
                        success_num += 1
                        print(f'提取信息完毕，等待{wait_time}秒')
                        time.sleep(wait_time)
                        break
                    else:  # 如果返回数据中没有结果
                        no_result_list.append(_id)
                        no_result_num += 1
                        self.update_data(_id, force_update=True, search_no_result=search_no_result)
                        print(f'返回数据中没有找到结果，等待{wait_time}秒')
                        time.sleep(wait_time)
                        break
                else:  # 如果没有返回数据，之后要重试
                    print('没有收到返回数据，请求失败')
                    if current_retry_count >= max_retry_count:
                        request_fail_num += 1

        print(
            f'当前共处理{i}条数据，跳过{skip_num}条，成功{success_num}条，需要设置搜索名{no_result_num}条，请求失败{request_fail_num}条')

    def arrange_files_in_db(self, sort_root_path=sort_root_path, sub_path_root=sub_path_root,
                            sub_path_artist=sub_path_artist, sub_path_group=sub_path_group,
                            sub_path_unsorted=sub_path_unsorted):
        artist_path = long_path + os.path.join(sort_root_path, sub_path_root, sub_path_artist)
        group_path = long_path + os.path.join(sort_root_path, sub_path_root, sub_path_group)
        unsorted_path = long_path + os.path.join(sort_root_path, sub_path_root, sub_path_unsorted)
        cols = ['id', 'file_path', 'artist', '_group']
        i = 0
        success_num = 0
        for db_id, file_path, artist, _group in self.get_data(*cols):
            i += 1
            s_a, s_g, s_u = 0, 0, 0
            print(i, '>>>')
            file_name = os.path.basename(file_path)
            file_path = long_path + os.path.abspath(file_path)
            artist,_group = str(artist),str(_group)
            while artist.endswith(r'.'):
                artist = artist[:-1]
            while _group.endswith(r'.'):
                _group = _group[:-1]
            if artist:
                s_a = create_hard_link(file_path, artist_path, artist, file_name, auto_create_dir=True)
                if s_a and s_a != -1:
                    success_num += 1
                    print(f'分类并创建硬链接成功artist：[{artist}]')
            elif _group:
                s_g = create_hard_link(file_path, group_path, _group, file_name, auto_create_dir=True)
                if s_g and s_g != -1:
                    success_num += 1
                    print(f'分类并创建硬链接成功group：[{_group}]')
            else:
                s_u = create_hard_link(file_path, unsorted_path, file_name, auto_create_dir=True)
                if s_u and s_u != -1:
                    print(f'[{db_id}]没有无法分类，加入[{sub_path_unsorted}]')
        print('成功分类并创建硬链接', success_num)

    def output_data(self):
        """
        将需要手动修改的信息输出到csv文件中
        :return:
        """
        manga_unsort_csv_parh = 'manga_unsort.csv'
        unsort_target_cols = ('file_name', 'artist', '_group', 'id', 'search_name', 'hentag_id')
        manga_unsort_data = [unsort_target_cols] + self.get_data(*unsort_target_cols,
                                                                 search_conditions_execute=' (artist is Null and _group is Null) or (artist="" and _group="")')
        try:
            with open(manga_unsort_csv_parh, 'w', newline='', encoding='utf-8-sig') as f:
                csv_writer = writer(f)
                csv_writer.writerows(manga_unsort_data)
                print(
                    f'已将没有作者和团队名的漫画信息输出到{manga_unsort_csv_parh}中，共有{len(manga_unsort_data) - 1}条数据')
        except PermissionError:
            print(f'导出漫画信息失败，文件{manga_unsort_csv_parh}正在使用')

        search_no_result_path = 'manga_search_no_result.csv'
        no_result_target_cols = ('file_name', 'search_name', 'id')
        no_result_data = [no_result_target_cols] + self.get_data(*no_result_target_cols,
                                                                 search_conditions_execute='search_no_result=1 or search_no_result=2')
        try:
            with open(search_no_result_path, 'w', newline='', encoding='utf-8-sig') as f:
                csv_writer = writer(f)
                csv_writer.writerows(no_result_data)
                print(
                    f'已将没有搜索结果的漫画信息输出到{search_no_result_path}中，共有{len(no_result_data) - 1}条数据，请手动修改search_name列的数据')
        except PermissionError:
            print(f'导出漫画信息失败，文件{search_no_result_path}正在使用')

    def import_change_data(self, csv_path, reset_flag=False):
        """

        :param csv_path:
        :param reset_flag: 是否将search_no_result列的值设为0
        :return:
        """
        _id = 'id'
        cols_need_change = ['artist', '_group', 'search_name']
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            col_need_change_index_dict = {}
            csv_reader = reader(f)
            all_rows = []
            for row in csv_reader:
                all_rows.append(row)
            first_row = all_rows[0]

            if _id in first_row:
                id_index = first_row.index(_id)
            else:
                print(f'无法识别到{csv_path}中的id列，退出')
            for col in cols_need_change:
                if col in first_row:
                    col_need_change_index_dict[col] = first_row.index(col)
            print(f'开始修改数据，共有{len(all_rows) - 1}条数据要修改')
            for row in all_rows[1:]:
                current_change_data = {}
                for key in col_need_change_index_dict:
                    current_index = col_need_change_index_dict[key]
                    current_value = row[current_index]
                    current_change_data[key] = current_value
                if reset_flag:
                    current_change_data['search_no_result'] = 0
                print(f'正在修改{row[id_index]}的数据为{current_change_data}')
                self.update_data(row[id_index], force_update=True, **current_change_data)
            print(f'{len(all_rows) - 1}条数据修改完毕')

    def request_hentag_metadata_all_each(self, max_retry_count=max_retry_count, timeout_rule=None,
                                         wait_time=wait_time, headers=headers):
        """
        尝试获取每条漫画的hentag元数据info.json文件，直到成功或者到最大尝试次数
        :param max_retry_count: 最大尝试次数
        :param timeout_rule: 超时时间，关于(次数,增加时间)的数组，比如(1,10)就是下1次，加10s，[(1, 10), (2, 5)]就是[10,15,20]，未进行设定的默认按最后的时间
        :param wait_time: 每次请求后的等待时间
        :return:
        """
        if timeout_rule is None:
            timeout_rule = timeout_rule
        get_cols_name = ['id', 'hentag_id', 'hentag_metadata']
        timeout_array, no_result_list = [], []
        timeout_second, skip_num, success_num, request_fail_num,no_manga, i = 0, 0, 0, 0, 0,0
        # 根据规则得到每次请求的超时时间数组
        for count, timeout_time in timeout_rule:
            while count > 0:
                timeout_second += timeout_time
                timeout_array.append(timeout_second)
                count -= 1
        n = max_retry_count - len(timeout_array)
        while n > 0:
            n -= 1
            timeout_array.append(timeout_second)

        for _id, hentag_id, hentag_metadata in self.get_data(*get_cols_name):
            i += 1
            # 成功提取过信息的，没有hentag_id的跳过
            if hentag_metadata or not hentag_id:
                print(i, f'{_id}跳过')
                skip_num += 1
                continue
            print(i, f'开始获取hentag_id为{hentag_id}的元数据>>>', end='')
            search_return = None
            current_retry_count = 0
            while (not search_return) and (current_retry_count < max_retry_count):
                timeout_second = timeout_array[current_retry_count]
                current_retry_count += 1
                print(f'第{current_retry_count}遍尝试，超时时间设置为{timeout_second}>>>', end='')
                search_return = get_hentag_metadata(hentag_id, timeout=timeout_second, headers=headers)
                if search_return:  # 如果收到返回数据
                    if search_return == 404:
                        print(f'hentag_id没有对应数据，跳过请求该条数据')
                        no_manga += 1
                        break
                    hentag_metadata_text = search_return
                    print('收到返回数据，存入数据库>>>', end='')
                    self.update_data(_id, force_update=True, hentag_metadata=hentag_metadata_text)
                    success_num += 1
                    print(f'提取信息完毕，等待{wait_time}秒')
                    time.sleep(wait_time)
                    break
                else:  # 如果没有返回数据
                    print('没有收到返回数据，请求失败')
                    if current_retry_count >= max_retry_count:
                        request_fail_num += 1
        print(
            f'当前共处理{i}条数据，跳过{skip_num}条，成功{success_num}条，没有该hentag_id的{no_manga}条，请求失败{request_fail_num}条')

    def save_hentag_metadata_to_json_file(self, root_dir_path=sort_root_path):
        get_cols = ['file_name', 'hentag_metadata']
        metadata_root_path = 'hentag_metadata'
        metadata_name = 'info.json'
        i, success_num = 0, 0
        root_dir_path = long_path+os.path.abspath(root_dir_path)
        for file_name, hentag_metadata in self.get_data(*get_cols):
            i += 1
            print(i,' ',end='')
            if not hentag_metadata:
                print('文件还没有下载info.json，跳过')
                continue
            if str(file_name).endswith(compress_extension):
                file_name, extension = os.path.splitext(file_name)
            target_dir = os.path.join(root_dir_path, metadata_root_path, file_name)
            if os.path.exists(target_dir):
                if not os.path.isdir(target_dir):
                    print(f'文件夹名{target_dir}已被同名文件占用，跳过')
                    continue
            else:
                os.makedirs(target_dir,exist_ok=True)
            metadata_path = os.path.join(target_dir, metadata_name)
            if write_to_file(hentag_metadata, metadata_path):
                print(f'已写入到{metadata_path}')
                success_num += 1
        print(f'输出完毕，共处理{i}条，输出{success_num}条')
        return i
