import json
import os


class ImcoConfig(object):

    def __init__(self, config_path):
        self.config_path = config_path
        try:
            with open(config_path) as fh:
                self.config = json.load(fh)
        except IOError:
            raise InvalidConfig
        except ValueError:
            self.config = {}
        self.image_max_x = int(self.get('images.max_x', 700))
        self.image_max_y = int(self.get('images.max_y', 700))
        self.dir_glob = str(self.get('images.dir_glob', '*'))
        self.image_glob = str(self.get('images.image_glob', '*.gif'))
        self.autosave_threshold = int(self.get('csv.autosave_threshold', 1))
        self.coder = str(self.get('csv.coder', 'Lucky R.A.'))
        self.codes = [ImcoCode(**c) for c in self.get('codes', [])]

    def get(self, path, default=None):
        v = self.config
        try:
            for k in path.split('.'):
                v = v[k]
            return v
        except KeyError:
            return default


class ImcoCode(object):

    def __init__(self, code, key, label=None, required=False, exception=False,
            prompt=None, values=None):
        self.code = code
        self.label = label if label is not None else code
        self.key = key
        self.required = required
        self.exception = exception
        self.prompt = prompt
        self.values = values
        if self.values is not None:
            self.values = set(v.lower() for v in self.values)

    def to_db(self, value):
        if self.values is None:
            return '0' if value is None else '1'
        else:
            return 'NA' if value is None else value

    def from_db(self, value):
        if self.values is None:
            return '1' if value == '1' else None
        else:
            return value if value != 'NA' else None


class InvalidConfig(Exception):
    pass
