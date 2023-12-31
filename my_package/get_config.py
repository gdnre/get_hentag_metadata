import configparser
import json

RED = '\x1B[31m'
GREEN = '\x1B[32m'
CEND = '\x1B[0m'


def get_config(config_path):
    config_dict = {}
    my_config = configparser.ConfigParser()
    my_config.read(config_path, encoding="utf-8")
    for section in my_config.sections():
        if section == 'headers':
            config_dict[section] = {}
            for key in my_config[section]:
                config_dict[section][key] = my_config[section][key]
        elif section == 'str':
            for key in my_config[section]:
                config_dict[key] = my_config[section][key]
        elif section == 'json':
            for key in my_config[section]:
                try:
                    config_dict[key] = json.loads(my_config[section][key])
                except json.decoder.JSONDecodeError as e:
                    print(
                        f'无法转换为{GREEN}{section}{CEND}类型，>{GREEN}{key}={my_config[section][key]}{CEND}<,未导入此选项,错误信息:',
                        e)
                    continue
        else:
            for key in my_config[section]:
                try:
                    config_dict[key] = eval(f"{section}('{my_config[section][key]}')")
                except SyntaxError as e:
                    print(
                        f'无法转换为{GREEN}{section}{CEND}类型，>{GREEN}{key}={my_config[section][key]}{CEND}<，未导入此选项,错误信息:',
                        e)
                    continue
    return config_dict


def config_replace_globals(config_path, _globals):
    config_dict = get_config(config_path)
    for key in config_dict:
        if key in _globals:
            if config_dict[key]:
                if _globals[key] != config_dict[key]:
                    _globals[key] = config_dict[key]
                    pv = str(_globals[key])
                    if len(pv)>=50:
                        pv = f'{pv:.<53.50}'
                    print(f'成功导入配置：{key}={pv}')
    return _globals
