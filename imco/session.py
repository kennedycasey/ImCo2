import csv
import datetime
import glob
import os
import random

from imco.config import ImcoConfig
from imco.db import ImcoDb


CONFIG_PATH = 'config.json'
DB_PATH = 'state.db'
IMAGES_PATH = 'images'


class ImcoSession(object):

    def __init__(self, workdir):
        self.workdir = workdir
        self.config = ImcoConfig(self.path(CONFIG_PATH))
        self.db = ImcoDb(self.path(DB_PATH), self.config.codes)
        self.state = self.db.load_state()
        self.dirs = [
                ImcoDir(d, self)
                for d in self.glob(IMAGES_PATH, self.config.dir_glob)
                if os.path.isdir(d)]
        seed = self.state.get('seed')
        if seed is not None:
            seed = int(seed)
        else:
            seed = random.randint(0, 1e6)
        self.state['seed'] = seed
        rng = random.Random(self.state['seed'])
        self.dir_order = list(range(0, len(self.dirs)))
        rng.shuffle(self.dir_order)
        self.modified_images = {}
        self.dir_index = None
        self.dir = None
        self.img_index = None
        self.img = None
        self.set_dir(int(self.state.get('dir_index', '0')))
        self.set_image(int(self.state.get('img_index', '0')))

    @property
    def img_path(self):
        return os.path.join(self.dir.name, self.img.name)

    def path(self, *components):
        return os.path.join(self.workdir, *components)

    def glob(self, *components):
        return glob.glob(self.path(*components))

    def load_images(self, imco_dir):
        paths = glob.glob(os.path.join(imco_dir.path, self.config.image_glob))
        img_rows = self.db.load_image_rows(imco_dir.name)
        images = []
        for path in paths:
            img = ImcoImage(path, self.config.codes)
            row = img_rows.get(img.name)
            if row is not None:
                img.fill_from_db_row(row, self.config.codes)
            images.append(img)
        return images

    def set_dir(self, index):
        self.dir_index = index
        self.dir = self.dirs[self.dir_order[index]]

    def prev_dir(self):
        if self.dir is None or self.dir_index == 0:
            return False
        self.set_dir(self.dir_index - 1)
        self.set_image(len(self.dir.images) - 1)
        return True

    def next_dir(self):
        if self.dir is None or self.dir_index + 1 == len(self.dir_order):
            return False
        self.set_dir(self.dir_index + 1)
        self.set_image(0)
        return True

    def set_image(self, index):
        self.img_index = index;
        self.img = self.dir.images[index]

    def prev_image(self):
        if self.dir is None or self.img_index == 0:
            return False
        self.set_image(self.img_index - 1)
        self.check_autosave()
        return True

    def next_image(self):
        if self.dir is None or self.img_index + 1 == len(self.dir.images):
            return False
        self.set_image(self.img_index + 1)
        self.check_autosave()
        return True

    def jump_to_frontier_image(self):
        self.set_dir(int(self.state.get('dir_index', self.dir_index)))
        self.set_image(int(self.state.get('img_index', self.img_index)))

    def update_frontier(self):
        self.state['dir_index'] = self.dir_index
        self.state['img_index'] = self.img_index

    def code_image(self, code, value):
        self.img.code(code, value)
        if self.img.is_coded(self.config.codes):
            # We only record codes once they're complete.
            self.modified_images[self.img.path] = self.img

    def img_coded(self):
        return self.img is not None and self.img.is_coded(self.config.codes)

    def check_autosave(self):
        if len(self.modified_images) == self.config.autosave_threshold:
            self.save()

    def save(self):
        self.db.store_state(self.state)
        modified = list(self.modified_images.values())
        self.modified_images = {}
        self.db.store_image_rows(modified, self.config.codes)

    def export_to_csv(self, fh):
        writer = csv.writer(fh, lineterminator='\n')
        coder = self.config.coder
        for i, row in enumerate(self.db.iterate_image_rows()):
            if i == 0:
                writer.writerow(['Coder'] + list(row.keys()))
            row = [coder] + list(row)
            writer.writerow(row)


class ImcoDir(object):

    def __init__(self, path, session):
        self.path = path
        self.session = session
        self.name = os.path.basename(path)
        self._images = None

    @property
    def images(self):
        if self._images is None:
            self._images = self.session.load_images(self)
        return self._images


class ImcoImage(object):
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, path, codes):
        self.path = path
        dirname, self.name = os.path.split(path)
        self.dir = os.path.basename(dirname)
        self._modified = None
        self.codes = dict((c.code, None) for c in codes)

    @property
    def timestamp(self):
        return self._modified.strftime(self.DATE_FORMAT)

    def fill_from_db_row(self, row, codes):
        self._modified = datetime.datetime.strptime(
                row['Modified'], self.DATE_FORMAT)
        for code in codes:
            db_value = row.get(code.code)
            if db_value is not None:
                self.codes[code.code] = code.from_db(db_value)

    def code(self, code, value):
        self.codes[code.code] = value
        self._modified = datetime.datetime.now()

    def is_coded(self, codes):
        missing_required = False
        for code in codes:
            value = self.codes.get(code.code)
            if code.exception and value is not None:
                return True
            elif code.required and value is None:
                missing_required = True
        return not missing_required
