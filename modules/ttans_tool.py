import time

from easygoogletranslate import EasyGoogleTranslate


supported_languages = [
    'af', 'sq', 'am', 'ar', 'hy', 'as', 'ay', 'az', 'bm', 'eu', 'be', 'bn', 'bho', 'bs', 'bg', 'ca', 'ceb',
    'zh-TW', 'co', 'hr', 'cs', 'da', 'dv', 'doi', 'nl', 'eo', 'et', 'ee', 'fil', 'fi', 'fr', 'fy',
    'gl', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha', 'haw', 'he', 'hi', 'hmn', 'hu', 'is', 'ig', 'ilo',
    'ga', 'it', 'ja', 'jv', 'kn', 'kk', 'km', 'rw', 'gom', 'ko', 'kri', 'ku', 'ckb', 'ky', 'lo', 'la', 'lv',
    'ln', 'lt', 'lg', 'lb', 'mk', 'mai', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mni-Mtei', 'lus', 'mn', 'my',
    'ne', 'no', 'ny', 'or', 'om', 'ps', 'fa', 'pl', 'pa', 'qu', 'ro', 'ru', 'sm', 'sa', 'gd', 'nso',
    'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tl', 'tg', 'ta', 'tt', 'te',
    'th', 'ti', 'ts', 'tr', 'tk', 'ak', 'uk', 'ur', 'ug', 'uz', 'cy', 'xh', 'yi', 'yo', 'zu', 'zh-CN', 'en', 'vi', 'pt', 'id'
]

def translate_text_func(text, source_language='zh-CN', target_language='en'):
    # 初始化翻译器
    if source_language not in supported_languages or target_language not in supported_languages:
        return
    translator = EasyGoogleTranslate(source_language=source_language, target_language=target_language)
    msgtext = translator.translate(text)
    return msgtext


class LANGUAGE:
    zh_CN = 'zh_CN' # 中文
    en_US = 'en_US' # 英文
    vi_VN = 'vi_VN' # 越南
    ba_IDN = 'ba_IDN' # 印尼
    bx_Pr = 'bx_Pr' # 巴西-葡萄牙语
    ja = 'ja' # 日语
    ko = 'ko' # 韩语

    name_arr = (zh_CN, en_US, vi_VN, ba_IDN, bx_Pr, ja, ko)

    name_dict = {
        zh_CN: '中文简体',
        en_US: 'English',
        vi_VN: 'Tiếng Việt',
        ba_IDN: 'bahasa Indonesia',
        bx_Pr: 'Brasil-Português',
        ja: '日本語',
        ko: '한국인',
    }
    lang_code = {
        zh_CN: "zh-CN",
        vi_VN: "vi",
        bx_Pr: "pt",
        ba_IDN: "id",
        en_US: "en",
        ja: "ja",
        ko: "ko",
    }


def funcc1():
    texts = ['总会话数', '有效会话数', '总消息数', '起始日期', '代理商']
    for text in texts:
        result = {}
        for k,v in LANGUAGE.lang_code.items():
            res = translate_text_func(text, target_language=v)
            result[v] = res

        fff = f'''
        "zh": "{text}",
        "en": "{result.get('en') or ''}",
        "vi": "{result.get('vi') or ''}",
        "idn": "{result.get('id') or ''}",
        "Br": "",
        "Pt": "{result.get('pt') or ''}",
        "ja": "{result.get('ja') or ''}",
        "ko": "{result.get('ko') or ''}",
        '''
        print(fff)
        print('*'*30)
        time.sleep(1)



def fff2():
    ddd = [
        {
            "zh": "今日访问量",
            "en": "Visits today",
            "vi": "Ghé thăm hôm nay",
            "idn": "komentar bawaan",
            "Br": "",
            "Pt": "",
            "th": "",
            "ja": "今日訪問してください",
            "ko": "오늘 방문"
        }
    ]
    for dds in ddd:
        text = dds.get('zh')
        res = translate_text_func(text, target_language='ms')
        dds['ms'] = res
        print(dds)
        time.sleep(0.5)

# funcc1()
