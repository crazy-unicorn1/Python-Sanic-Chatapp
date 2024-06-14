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


# 读取 language.json 文件
# data="Xin chào"
# print(translate_text(data, source_language='vi', target_language='en'))
'''
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
'''
