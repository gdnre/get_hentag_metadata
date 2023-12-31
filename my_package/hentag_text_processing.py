import json

hentag_example = {
    'parody': 'parodies',
    'group': 'circles',
    'artist': 'artists',
    'character': 'characters',
    'male': 'maleTags',
    'female': 'femaleTags',
    'other': 'otherTags',
    'locations': 'locations'
}


def get_data_from_json(text, key: int | str = 0, getting_type='value'):
    """
    从json字符串中提取数据
    :param text: json格式的字符串
    :param key: 要获取的数据的键，也可以是int格式的索引
    :param getting_type: value或item，返回单个值或键值对的元组；keys、values、items，返回所有对应数据的数组
    :return: 返回对应数据，没有则返回none
    """
    try:
        all_dicts = json.loads(text)
        if getting_type == 'value':
            if isinstance(key, int):  # 判断key是不是数字
                all_values = [value for value in all_dicts.values()]
                return all_values[key]
            else:
                return all_dicts[key]
        if getting_type == 'item':
            if isinstance(key, int):
                all_items = [item for item in all_dicts.items()]
                return all_items[key]
            else:
                return key, all_dicts[key]

        if getting_type == 'keys' or getting_type == 'key':
            return [key for key in all_dicts.keys()]
        if getting_type == 'values':
            return [value for value in all_dicts.values()]
        if getting_type == 'items':
            return [item for item in all_dicts.items()]
    except:
        return


def get_result_by_hentag_text(hentag_text, index=0):
    """
    从hentag网站返回的搜索结果中提取一条结果保存
    :param hentag_text: 返回的结果，json格式
    :param index: 要第几条数据，默认为0，搜索的第一个结果
    :return: 返回json格式的字符串
    """
    try:
        j = json.loads(hentag_text)
        result_dict = j["works"][index]
        result = json.dumps(result_dict, ensure_ascii=False)
        return result
    except:
        print("无法从中获取hentag数据")


def get_title_from_result(hentag_text_result):
    """
    从get_result_by_hentag_text处理过的数据中提取标题
    :param hentag_text_result:
    :return: 返回标题
    """
    title = get_data_from_json(hentag_text_result, 'title')
    return title


def get_hentag_id_from_result(hentag_text_result):
    """
    从get_result_by_hentag_text处理过的数据中提取hentag的id
    :param hentag_text_result:
    :return: 返回hentag id
    """
    hentag_id = get_data_from_json(hentag_text_result, 'id')
    return hentag_id


def get_artist_and_group_from_result(hentag_text_result):
    """
    从get_result_by_hentag_text处理过的数据中提取作者和团队
    :param hentag_text_result:
    :return: 返回artist,group
    """
    artist = get_data_from_json(hentag_text_result, 'artists')
    group = get_data_from_json(hentag_text_result, 'circles')
    if artist:
        artist = artist[0]['name']
    else:
        artist = ''
    if group:
        group = group[0]['name']
    else:
        group = ''
    return artist, group


def get_tags_from_result(hentag_text_result):
    """
    从get_result_by_hentag_text处理过的数据中提取tag
    :param hentag_text_result:
    :return: 返回json格式的tags
    """
    try:
        hentag_tags = hentag_example.copy()
        for key, value in hentag_tags.items():
            hentag_tags[key] = []
            tags = get_data_from_json(hentag_text_result, value)
            if key == 'locations':
                hentag_tags[key] = tags
                continue
            if tags:
                for tag in tags:
                    hentag_tags[key] += [tag['name']]
        hentag_tags_json = json.dumps(hentag_tags,ensure_ascii=False)
        return hentag_tags_json
    except Exception:
        return


