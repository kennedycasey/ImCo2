import csv
import datetime
import glob
import os
import re
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
        #dictionary mapping modified image paths to image objects
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

    def load_images_start(self, imco_dir):
        #creates list of ImcoImage objects from directory images 
        #and removes duplicate images that have not
        #been coded yet for when a session is started
        paths = sorted(glob.glob(os.path.join(imco_dir.path, self.config.image_glob)))
        img_rows = self.db.load_image_rows(imco_dir.name)
        images = []
        for path in paths:
            img = ImcoImage(path, self.config.codes)
            row = img_rows.get(img.name)
            if row is not None:
                img.fill_from_db_row(row, self.config.codes)
                images.append(img)
            else:
                if 'DUPLICATE' in img.name:
                    if row==None:
                        os.remove(img.path)  
                    else:
                        images.append(img)
                else:
                    images.append(img)
        for index in range(len(images)):
            if images[index].object_count>1:
                if 'DUPLICATE' not in images[index].name:
                    i = index+1
                    count=1
                    while 'DUPLICATE' in images[i].name:
                        count+=1
                        i+=1
                    for j in range(count):
                        images[index+j].object_count = count
        return images

    def load_images(self, imco_dir):
        #creates list of ImcoImage objects from the current working directory
        paths = sorted(glob.glob(os.path.join(imco_dir.path, self.config.image_glob)))
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
        #sets working directory
        self.dir_index = index
        self.dir = self.dirs[self.dir_order[index]]

    def prev_dir(self):
        #moves one index back in list of directories
        if self.dir is None or self.dir_index == 0:
            return False
        self.set_dir(self.dir_index - 1)
        self.set_image(len(self.dir.images) - 1)
        return True

    def next_dir(self):
        #moves on index forward in list of directories
        if self.dir is None or self.dir_index + 1 == len(self.dir_order):
            return False
        self.set_dir(self.dir_index + 1)
        self.set_image(0)
        return True

    def set_image(self, index):
        #changes image to inputted index in list of session images
        self.img_index = index
        self.img = self.dir.images[index]

    def prev_image(self):
        #switches to previous image in the image list order
        if self.dir is None or self.img_index == 0:
            return False
        self.set_image(self.img_index - 1)
        self.check_autosave()
        return True

    def next_image(self):
        #switches to next image in the image list order
        if self.dir is None or self.img_index + 1 == len(self.dir.images):
            return False
        self.set_image(self.img_index + 1)
        self.check_autosave()
        return True

    def jump_to_frontier_image(self):
        #Goes to next uncoded image
        self.set_dir(int(self.state.get('dir_index', self.dir_index)))
        self.set_image(int(self.state.get('img_index', self.img_index)))

    def update_frontier(self):
        #Updates index for next uncoded image
        self.state['dir_index'] = self.dir_index
        self.state['img_index'] = self.img_index

    def code_image(self, code, value):
        #updates status of image code and adds it to list of modified
        #images if fully coded
        self.img.code(code, value)
        if self.img.is_coded(self.config.codes):
            self.modified_images[self.img.path] = self.img

    def set_image_object_count(self, object_count):
        #sets object_count attribute of ImcoImage object
        if self.img.codes['None'] is not None:
            self.img.object_count = 0
        else: 
            self.img.object_count = object_count
        self.modified_images[self.img.path] = self.img

    def set_image_object_name(self, object_name):
        #sets object_name attribute of ImcoImage object
        self.img.object_name = object_name
        self.modified_images[self.img.path] = self.img

    def set_image_comments(self, comments):
        #sets comments attribute of ImcoImage object
        self.img.comments = comments
        self.modified_images[self.img.path] = self.img

    def set_image_repeated(self, repeated):
        #sets codes of image to be the codes of the previous image
        self.img.repeated = repeated
        self.modified_images[self.img.path] = self.img

    def img_coded(self):
        #determines if ImcoImage object is fully coded
        return self.img is not None and self.img.is_coded(self.config.codes)

    def check_autosave(self):
        #Automatically saves if there has been a certain number of modified
        #images without a user or function saving progress
        if len(self.modified_images) == self.config.autosave_threshold:
            self.save()

    def save(self):
        #stores code values of fully coded images that have been modified since
        #the previous save statement to state.db file
        self.db.store_state(self.state)
        modified = []
        for images in self.modified_images.values():
            try: 
                if len(images) > 1:
                    for img in images:
                        if img._modified != None:
                            modified.append(img)
            except TypeError:
                modified.append(images)
        self.modified_images = {}
        self.db.store_image_rows(modified, self.config.codes)

    def export_to_csv(self, fh):
        #exports table of code values to csv format 
        writer = csv.writer(fh, lineterminator='\n')
        coder = self.config.coder
        for i, row in enumerate(self.db.iterate_image_rows()):
            if i == 0:
                writer.writerow(['Coder'] + list(row.keys()))
            row = [coder] + list(row)
            writer.writerow(row)

    def delete_duplicates(self, name):
        self.db.delete_duplicate(name)

class ImcoDir(object):

    def __init__(self, path, session):
        self.path = path
        self.session = session
        self.name = os.path.basename(path)
        self._images = None

    @property
    def images(self):
        if self._images is None:
            self._images = self.session.load_images_start(self)
        return self._images


class ImcoImage(object):
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, path, codes):
        self.path = path
        dirname, self.name = os.path.split(path)
        self.dir = os.path.basename(dirname)
        self._modified = None
        self.codes = dict((c.code, None) for c in codes)
        self._comments = ''
        self._object_name = ''
        self._repeated = {}
        #Whether or not image attributes were repeated from the previous image 
        #in the directory
        self._object_count = 1

    @property
    def timestamp(self):
        return self._modified.strftime(self.DATE_FORMAT)

    def fill_from_db_row(self, row, codes):
        #Sets image attributes if image was previously coded
        self._modified = datetime.datetime.strptime(
                row['Modified'], self.DATE_FORMAT)
        for code in codes:
            db_value = row.get(code.code)
            if db_value is not None:
                self.codes[code.code] = code.from_db(db_value)
        self._comments = row['Comments']
        self._object_name = row['Object']
        if row['ObjectCount'] is None:
            self.object_count = 0
        else:
            self.object_count = row['ObjectCount']

    def code(self, code, value):
        #updates code value and sets modification timestamp
        self.codes[code.code] = value
        self._modified = datetime.datetime.now()

    @property
    def object_name(self):
        return self._object_name

    @object_name.setter
    def object_name(self, object_name):
        self._object_name = object_name
        self._modified = datetime.datetime.now()

    @property
    def object_count(self):
        return self._object_count

    @object_count.setter
    def object_count(self, object_count):
        self._object_count = object_count

    @property
    def comments(self):
        return self._comments

    @comments.setter
    def comments(self, comments):
        self._comments = comments
        self._modified = datetime.datetime.now()

    @property
    def repeated(self):
        return self._repeated

    @repeated.setter
    def repeated(self, repeated):
        self._repeated = repeated
        self._modified = datetime.datetime.now()

    def is_coded(self, codes):
        #determines if image is fully coded based on exception and required codes
        req = len([i for i in codes if i.required])
        req_count = 0
        label = False
        for code in codes:
            value = self.codes.get(code.code)
            if code.exception and value is not None:
                return True
            elif not code.exception and not code.required and value is not None:
                label = True
            elif not code.exception and code.required and value is not None:
                req_count+=1
        if req_count == req:
            if label:
                if self._object_name != '':
                    return True
        return False
