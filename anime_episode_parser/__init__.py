import re
import logging
from typing import List, Union

logger = logging.getLogger("anime-episode-parser")

_CN_NUM = {
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "零": 0,
    "壹": 1,
    "贰": 2,
    "叁": 3,
    "肆": 4,
    "伍": 5,
    "陆": 6,
    "柒": 7,
    "捌": 8,
    "玖": 9,
    "貮": 2,
    "两": 2,
}

_CN_UNIT = {
    "十": 10,
    "拾": 10,
    "百": 100,
    "佰": 100,
    "千": 1000,
    "仟": 1000,
    "万": 10000,
    "萬": 10000,
}


def chinese_to_arabic(cn: str) -> int:
    """
    https://blog.csdn.net/hexrain/article/details/52790126
    :type cn: str
    :rtype: int
    """

    unit = 0  # current
    l_dig = []  # digest
    for cn_dig in reversed(cn):
        if cn_dig in _CN_UNIT:
            unit = _CN_UNIT[cn_dig]
            if unit == 10000 or unit == 100000000:
                l_dig.append(unit)
                unit = 1
        else:
            dig = _CN_NUM[cn_dig]
            if unit:
                dig *= unit
                unit = 0
            l_dig.append(dig)
    if unit == 10:
        l_dig.append(10)
    val, tmp = 0, 0
    for x in reversed(l_dig):
        if x == 10000 or x == 100000000:
            val += tmp * x
            tmp = 0
        else:
            tmp += x
    val += tmp
    return val


FETCH_EPISODE_WITH_BRACKETS = re.compile(r"[【\[]E?(\d+)\s?(?:END)?[】\]]")

FETCH_EPISODE_ZH = re.compile(r"第?\s?(\d{1,3})\s?[話话集]")
FETCH_EPISODE_ALL_ZH = re.compile(r"第([^第]*?)[話话集]")
FETCH_EPISODE_ONLY_NUM = re.compile(r"^([\d]{2,})$")

FETCH_EPISODE_RANGE = re.compile(r"[^sS][\d]{2,}\s?-\s?([\d]{2,})")
FETCH_EPISODE_RANGE_ZH = re.compile(r"[第][\d]{2,}\s?-\s?([\d]{2,})\s?[話话集]")
FETCH_EPISODE_RANGE_ALL_ZH_1 = re.compile(r"[全]([\d-]*?)[話话集]")
FETCH_EPISODE_RANGE_ALL_ZH_2 = re.compile(r"第?(\d-\d)[話话集]")

FETCH_EPISODE_OVA_OAD = re.compile(r"([\d]{2,})\s?\((?:OVA|OAD)\)]")
FETCH_EPISODE_WITH_VERSION = re.compile(r"[【\[](\d+)\s? *v\d(?:END)?[】\]]")

FETCH_EPISODE = (
    FETCH_EPISODE_ZH,
    FETCH_EPISODE_ALL_ZH,
    FETCH_EPISODE_WITH_BRACKETS,
    FETCH_EPISODE_ONLY_NUM,
    FETCH_EPISODE_RANGE,
    FETCH_EPISODE_RANGE_ALL_ZH_1,
    FETCH_EPISODE_RANGE_ALL_ZH_2,
    FETCH_EPISODE_OVA_OAD,
    FETCH_EPISODE_WITH_VERSION,
)


def parse_episode(episode_title: str) -> Union[int, None]:
    """
    parse episode from title
    :param episode_title: episode title
    :type episode_title: str
    :return: episode of this title
    :rtype: int
    """
    spare = None

    def get_real_episode(episode_list: Union[List[str], List[int]]) -> int:
        return min(int(x) for x in episode_list)

    for pattern in (FETCH_EPISODE_RANGE_ALL_ZH_1, FETCH_EPISODE_RANGE_ALL_ZH_2):
        _ = pattern.findall(episode_title)
        if _ and _[0]:
            logger.debug("return episode range all zh '%s'", pattern.pattern)
            return None

    _ = FETCH_EPISODE_RANGE.findall(episode_title)
    if _ and _[0]:
        logger.debug("return episode range")
        return None

    _ = FETCH_EPISODE_RANGE_ZH.findall(episode_title)
    if _ and _[0]:
        logger.debug("return episode range zh")
        return None

    _ = FETCH_EPISODE_ZH.findall(episode_title)
    if _ and _[0].isdigit():
        logger.debug("return episode zh")
        return int(_[0])

    _ = FETCH_EPISODE_ALL_ZH.findall(episode_title)
    if _ and _[0]:
        try:
            logger.debug("try return episode all zh %s", _)
            e = chinese_to_arabic(_[0])
            logger.debug("return episode all zh")
            return e
        except Exception:
            logger.debug("can't convert %s to int", _[0])

    _ = FETCH_EPISODE_WITH_VERSION.findall(episode_title)
    if _ and _[0].isdigit():
        logger.debug("return episode range with version")
        return int(_[0])

    _ = FETCH_EPISODE_WITH_BRACKETS.findall(episode_title)
    if _:
        logger.debug("return episode with brackets")
        return get_real_episode(_)

    logger.debug("don't match any regex, try match after split")
    rest: List[int] = []
    for i in episode_title.replace("[", " ").replace("【", ",").split(" "):
        for regexp in FETCH_EPISODE:
            match = regexp.findall(i)
            if match and match[0].isdigit():
                m = int(match[0])
                if m > 1000:
                    spare = m
                else:
                    logger.debug(f"match {i} '{regexp.pattern}' {m}")
                    rest.append(m)

    if rest:
        return get_real_episode(rest)

    if spare:
        return spare

    return None
