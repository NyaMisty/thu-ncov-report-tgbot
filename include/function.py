import re
from typing import Dict, Optional
import logging

import json5
import requests
import logging
import json
from .config import *

_logger = logging.getLogger(__name__)

class UsernameNotSet(Exception):
    pass

def match_re_group1(re_str: str, text: str) -> str:
    """
    在 text 中匹配正则表达式 re_str，返回第 1 个捕获组（即首个用括号包住的捕获组）
    :param re_str: 正则表达式（字符串）
    :param text: 要被匹配的文本
    :return: 第 1 个捕获组
    """
    match = re.search(re_str, text)
    if match is None:
        raise ValueError(f'在文本中匹配 {re_str} 失败，没找到任何东西。\n请阅读脚本文档中的“使用前提”部分。')

    return match.group(1)

def extract_post_data(html: str) -> Dict[str, str]:
    """
    从上报页面的 HTML 中，提取出上报 API 所需要填写的参数。
    :return: 最终 POST 的参数（使用 dict 表示）
    """
    data = match_re_group1(r'<script type="text/tpl" id="dcstr">(.*?)</script>', html)
    if data == None:
        pass

    # 检查数据是否足够长
    if len(data) < REASONABLE_LENGTH:
        _logger.debug(f'\ndata: {data}')
        raise ValueError('获取到的数据过短。请阅读脚本文档的“使用前提”部分')

    data = json5.loads(data)

    rows = re.findall(r'<.*?databind="(.*?)".*?dojotype="(.*?)".*?presetbind="(.*?)".*?>', html)
    if not rows:
        _logger.debug(f'\nerroneous data: {data}')
        raise ValueError('无法获取表单数据。请阅读脚本文档的“使用前提”部分')

    basedata_stores = data['body']['dataStores']
    datastore_namedict = { c['rowSetName']: c for c in basedata_stores.values() if 'rowSetName' in c}
    presetsDict = {c['name']: c['value'] for c in data['body']['dataStores']['variable']['rowSet']['primary']}

    for row in rows:
        databind = row[0]
        dojotype = row[1]
        presetbind = row[2]

        databind_entity, _, databind_field = databind.partition('.')

        datastore = datastore_namedict[databind_entity]
        if not presetbind in presetsDict:
            raise ValueError('已填写信息与待填信息格式不匹配。')
        presetValue = presetsDict[presetbind]
        if datastore['recordCount'] == 0:
            datastore['recordCount'] += 1
            datastore['rowSet']['primary'].append({})

        datastore['rowSet']['primary'][0][databind_field] = presetValue
        if dojotype == 'unieap.form.ComboBox':
            datastore['rowSet']['primary'][0][databind_field + '_TEXT'] = presetValue
            if not presetValue:
                datastore['rowSet']['primary'][0][databind_field + '_TEXT'] = "请选择"

    for datastore in datastore_namedict.values():
        datastore['rowSet']['primary'][0]['_o'] = list(datastore['rowSet']['primary'][0])
        datastore['rowSet']['primary'][0]['_t'] = 3

    ret = json5.dumps(data)
    return ret
