#!/usr/bin/env python3

import os

import imco


if __name__ == '__main__':
    app_root = os.path.dirname(os.path.realpath(__file__))
    app_state_path = os.path.join(app_root, 'state.json')
    app_state = imco.appstate.load_file(app_state_path)
    app = imco.gui.ImcoTkApp(app_state)
