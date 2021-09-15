import json


def load_file(state_path):
    try:
        with open(state_path) as fh:
            state = json.load(fh)
        if type(state) is not dict:
            state = {}
    except IOError:
        # Invalid file
        state = {}
        state_path = None
    except ValueError:
        # Invalid JSON
        state = {}
    return AppState(state, state_path)


class AppState(object):

    def __init__(self, state, state_path = None):
        self.state = state
        self.state_path = state_path

    def get(self, key, default=None):
        return self.state.get(key, default)

    def set(self, key, value):
        self.state[key] = value

    def save(self):
        if self.state_path is None:
            return
        with open(self.state_path, 'w') as fh:
            json.dump(self.state, fh, indent=3)
