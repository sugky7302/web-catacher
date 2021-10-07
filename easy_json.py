#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    VERSION: 1.0.0
    Author: Arvin, Yang
    Release Date: 2020-05-22
    Introduction: 整合python的json函數，包裝成一個類別簡化操作。
'''

import os
import re
from collections import OrderedDict as ODict
import json


class StandardEncoder(json.JSONEncoder):
    """A JSON Encoder that puts small lists on single lines."""

    def __init__(self, *args, **kwargs):
        super(StandardEncoder, self).__init__(*args, **kwargs)
        self.indentation_level = 0

    # NOTE: json.dump會調用此函數
    def iterencode(self, o):
        return self.encode(o)

    # NOTE: json.dumps會調用此函數
    def encode(self, o):
        """Encode JSON object *o* with respect to single line lists."""

        if isinstance(o, list):
            if self._is_single_line_list(o):
                return "[{}]".format(", ".join(json.dumps(el, ensure_ascii=False) for el in o))
            else:
                self.indentation_level += 1
                output = [self.indent_str + self.encode(el) for el in o]
                self.indentation_level -= 1
                output_str = ",\n".join(output)
                return ("[\n{}\n{}]").format(output_str, self.indent_str)

        elif isinstance(o, ODict):
            if o.get("type", None):
                self.indentation_level += 1
                output = [
                    "{}{}: {}".format(self.indent_str, json.dumps(k, ensure_ascii=False),
                                      self.encode(v)) for k, v in o.items()
                ]
                self.indentation_level -= 1
                return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"
            else:
                output = [
                    "{}: {}".format(json.dumps(k, ensure_ascii=False), self.encode(v))
                    for k, v in o.items()
                ]
                return "{" + ", ".join(output) + "}"
        else:
            return json.dumps(o, ensure_ascii=False)

    # NOTE: 檢查對象的長度，判斷轉成json字串須不需要換行
    def _is_single_line_list(self, o):
        return not any(isinstance(el, (list, ODict)) for el in o)\
               and len(str(o)) - 2 <= 60

    # NOTE: 根據層數計算給json字串的對齊空格
    @property
    def indent_str(self):
        return " " * self.indentation_level * self.indent


class Json(object):
    encoder = StandardEncoder
    indent = 4

    @classmethod
    def set_encoder(cls, encoder):
        cls.encoder = encoder

    @classmethod
    def set_indent(cls, indent):
        cls.indent = indent

    def __init__(self, path):
        self.__string = ""
        self.__object = {}
        self.__name = re.search(r'[\w\s]+.json', path).group()
        self.__path = path

        # 防止找不到檔案而使open報錯
        if not os.path.isfile(path):
            return

        with open(path, 'r', encoding='utf-8') as f:
            self.__string = f.read().encode('utf-8')
            self.__string_sync_object()

    @property
    def name(self):
        return self.__name[:-5]

    @property
    def string(self):
        return self.__string

    @string.setter
    def string(self, new_string):
        self.__string = str(new_string)
        self.__string_sync_object()

    def __string_sync_object(self):
        self.__object = json.loads(self.__string, object_pairs_hook=ODict)

    @property
    def object(self):
        return self.__object

    def __getitem__(self, key):
        try:
            return self.__object[key]
        except Exception:
            return None

    def __setitem__(self, key, value):
        try:
            self.__object[key] = value
            self.__object_sync_string()
        except Exception:
            pass

    def __object_sync_string(self):
        self.__string = json.dumps(
            self.__object,
            ensure_ascii=False,
            sort_keys=False,
            indent=self.__class__.indent,
            cls=self.__class__.encoder)

    def write(self):
        with open(self.__path, 'w') as f:
            json.dump(
                self.__object,
                f,
                ensure_ascii=False,
                sort_keys=False,
                indent=self.__class__.indent,
                cls=self.__class__.encoder)
