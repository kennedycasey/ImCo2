import tkinter as Tk
from tkinter import simpledialog
from tkinter import Toplevel
import tkinter.messagebox as tkmb
import tkinter.filedialog
import tkinter.font
import atexit
import os
import sys
import re
import glob
import datetime
import shutil
from PIL import ImageTk, Image

from imco.version import VERSION
from imco.session import ImcoSession, ImcoImage
import imco

INFO_FRAME_WIDTH = 400
DEFAULT_CANVAS_SIZE = 700

DEFAULT_BG = '#f6f6f6'
SECTION_FG = '#424242'
CANVAS_BG  = '#0d0d12'

class ImcoTkApp(object):

    def __init__(self, app_state):
        self.root = Tk.Tk()
        self._handled_delete_window = False
        self.app_state = app_state
        self.session = None
        # A list of CodeLabel instances.
        self.code_labels = []
        # The PhotoImage instance for the currently-displayed image.
        self.photo_img = None
        self.selected_image = None
        self.prev_selected_image = None
        self.prev_viewed_img_index = None
        self.build_menu()
        self.build_main_window()
        self.install_bindings()
        self.install_protocols()
        last_workdir = app_state.get('workdir')
        if last_workdir is not None:
            self.open_workdir(last_workdir)
        self.root.mainloop()

    def build_menu(self):
        #Constructs dropdown menu for actions for files/directories, images, and text entries
        self.root.option_add('*tearOff', False)
        self.menubar = Tk.Menu(self.root)
        self.appmenu = Tk.Menu(self.menubar, name = 'apple')
        self.filemenu = Tk.Menu(self.root)
        #Menu for navigating directory and saving coding progress
        self.menubar.add_cascade(label = 'File', menu = self.filemenu)
        self.filemenu.add_command(
                label = 'Open workdir',
                command = self.handle_open,
                accelerator = meta_accelerator('O'))
        self.filemenu.add_command(
                label = 'Open specific image',
                command = self.handle_open_image,
                accelerator = meta_accelerator('I'),
                state = Tk.DISABLED)
        self.filemenu.add_command(
                label = 'View context',
                command = self.handle_open_context,
                accelerator = meta_accelerator('V'),
                state = Tk.DISABLED)
        self.filemenu.add_command(
                label = 'Save',
                command = self.handle_save,
                accelerator = meta_accelerator('S'),
                state = Tk.DISABLED)
        self.filemenu.add_command(
                label = 'Export codes to CSV',
                command = self.handle_export,
                accelerator = meta_accelerator('E'),
                state = Tk.DISABLED)
        self.filemenu.add_command(
                label = 'Check progress',
                command = self.handle_check_progress,
                state=Tk.DISABLED)
        self.imagemenu = Tk.Menu(self.root)
        #Menu for coding images in specific orders 
        self.menubar.add_cascade(
            label = 'Image', 
            menu = self.imagemenu)
        self.imagemenu.add_command(
                label = 'Previous',
                command = self.handle_prev_image,
                accelerator = 'Left',
                state = Tk.DISABLED)
        self.imagemenu.add_command(
                label = 'Next',
                command = self.handle_next_image,
                accelerator = 'Right',
                state = Tk.DISABLED)
        self.imagemenu.add_command(
                label = 'Same as previous image',
                command = self.handle_repeated,
                accelerator = meta_accelerator('.'),
                state = Tk.DISABLED)
        self.imagemenu.add_command(
            label = 'Clear codes',
            command = self.handle_clear_codes,
            accelerator = meta_accelerator('x'),
            state = Tk.DISABLED)
        self.imagemenu.add_command(
                label = 'Multiple objects',
                command = self.handle_multiple_objects,
                accelerator = meta_accelerator('='), 
                state = Tk.DISABLED)
        self.imagemenu.add_command(
                label = 'Beginning',
                command = self.handle_first,
                accelerator = meta_accelerator('Left'),
                state = Tk.DISABLED)
        self.imagemenu.add_command(
                label = 'End',
                command = self.handle_frontier,
                accelerator = meta_accelerator('Right'),
                state = Tk.DISABLED)
        self.imagemenu.add_command(
            label = 'Next Skipped',
            command = self.handle_next_skipped,
            state = Tk.DISABLED)
        self.imagemenu.add_command(
            label = 'Previous Skipped',
            command = self.handle_prev_skipped,
            state = Tk.DISABLED)
        self.entrymenu = Tk.Menu(self.root)
        #Menu for adding and editing comments and object labels to images
        self.menubar.add_cascade(
            label = 'Text Entry', 
            menu = self.entrymenu)
        self.entrymenu.add_command(
            label = 'Add object name',
            command = self.handle_object_entry,
            accelerator = meta_accelerator('L'),
            state = Tk.DISABLED)
        self.entrymenu.add_command(
            label = 'Add comment',
            command = self.handle_comment_entry,
            accelerator = meta_accelerator('U'),
            state = Tk.DISABLED)
        self.entrymenu.add_command(
            label = 'Find and replace object',
            command = self.handle_find_replace,
            accelerator = meta_accelerator('R'),
            state = Tk.DISABLED)
        self.root.config(menu = self.menubar)

    def handle_object_entry(self, event = None):
        #Makes command to enter an object name, adds input to image object object_name
        #attribute, and adds undo object button
        self.imagemenu.entryconfig('Next', state = Tk.DISABLED)
        self.imagemenu.entryconfig('Previous', state = Tk.DISABLED)
        if self.session.img.object_name != '':
            self.handle_remove_object_entry()
        self.object_entry = simpledialog.askstring(
                title = "ADD OBJECT NAME",
                prompt = "",
                parent = self.root)
        if self.object_entry is not None:
            self.object_name = Tk.Label(
                self.info_frame,
                text = "Your object name(s): " + self.object_entry,
                fg = '#05976c',
                bg = '#f6f6f6',
                wraplength = 375)
            self.object_name.pack(fill = Tk.X)
            self.object_undo_button.pack()
            self.session.set_image_object_name(self.object_entry)
        self.imagemenu.entryconfig('Next', state = Tk.NORMAL)
        self.imagemenu.entryconfig('Previous', state = Tk.NORMAL)

    def handle_remove_object_entry(self):
        #Tkinter button to remove displayed object label and clear attribute
        self.object_undo_button.pack_forget()
        self.object_name.destroy()
        self.session.set_image_object_name('')

    def handle_remove_comment_entry(self):
        #Tkinter button to remove displayed comments and clear attribute
        self.comment_undo_button.pack_forget()
        self.comments.destroy()
        self.session.set_image_comments('')

    def handle_comment_entry(self, event=None):
        #Makes command to enter a comment, adds input to image object comment 
        #attribute, and adds undo comment button
        self.imagemenu.entryconfig('Next', state=Tk.DISABLED)
        self.imagemenu.entryconfig('Previous', state=Tk.DISABLED)
        if self.session.img.comments != '':
            self.handle_remove_comment_entry()
        self.comment_entry = simpledialog.askstring(
                title="ADD COMMENTS",
                prompt="",
                parent=self.root)
        if self.comment_entry is not None:
            self.comments = Tk.Label(
                self.info_frame,
                text = "Your comments: " + self.comment_entry,
                fg = '#05976c',
                bg = '#f6f6f6',
                wraplength=375)
            self.comments.pack(fill=Tk.X)
            self.comment_undo_button.pack()
            self.session.set_image_comments(self.comment_entry)
        self.imagemenu.entryconfig('Next', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Previous', state=Tk.NORMAL)

    def handle_check_progress(self, event = None):
        #Checks and displays the number of uncoded images in the directory
        count = 0
        for dir in self.session.dirs:
            img_lst = self.session.load_images(dir)
            for img in img_lst:
                if not img.is_coded(self.session.config.codes) or img.codes['Skipped'] is not None:
                    count+=1
        self.info("Nice work! You have " + str(count) + " images left to code in this directory.")

    def build_main_window(self):
        #Constructs window displaying code labels, path, object count, and undo buttons if needed
        self.root.title("IMCO  v{}".format(VERSION))
        self.root.config(bg = DEFAULT_BG)
        self.build_fonts()
        self.info_frame = Tk.Frame(self.root, bg = DEFAULT_BG)
        self.info_frame.grid(column = 0, row = 0, sticky = Tk.N + Tk.W, padx = 10)
        self.path_section_label = Tk.Label(
                self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                font = self.section_font,
                fg = SECTION_FG,
                bg = DEFAULT_BG,
                text = 'PATH')
        self.path_section_label.pack(fill = Tk.X, pady = (10, 0))
        self.path_label = Tk.Label(
                self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                bg = DEFAULT_BG)
        self.path_label.pack(fill = Tk.X)
        self.order_section_label = Tk.Label(
                self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                font = self.section_font,
                fg = SECTION_FG,
                bg = DEFAULT_BG,
                text = 'IMAGE NUMBER')
        self.order_section_label.pack(fill = Tk.X, pady = (10, 0))
        self.order_label = Tk.Label(
            self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                bg = DEFAULT_BG)
        self.order_label.pack(fill = Tk.X)
        self.object_count_section_label = Tk.Label(
                self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                font = self.section_font,
                fg = SECTION_FG,
                bg = DEFAULT_BG,
                text = 'OBJECT COUNT')
        self.object_count_section_label.pack(fill = Tk.X, pady = (10, 0))
        self.object_count_label = Tk.Label(
            self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                bg = DEFAULT_BG)
        self.object_count_label.pack(fill = Tk.X)
        self.codes_section_label = Tk.Label(
                self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                font = self.section_font,
                fg = SECTION_FG,
                bg = DEFAULT_BG,
                text = 'CODES')
        self.codes_section_label.pack(fill = Tk.X, pady = (10, 0))
        self.code_frame = Tk.Frame(self.info_frame, bg = DEFAULT_BG)
        self.code_frame.pack(fill = Tk.X)
        self.entries_section_label = Tk.Label(
                self.info_frame,
                anchor = Tk.W,
                justify = Tk.LEFT,
                font = self.section_font,
                fg = SECTION_FG,
                bg = DEFAULT_BG,
                text = 'TEXT ENTRIES')
        self.entries_section_label.pack(fill = Tk.X, pady = (10, 0))
        self.object_undo_button = Tk.Button(
            self.info_frame,
            text = 'Undo object entry',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.handle_remove_object_entry
        )
        self.comment_undo_button = Tk.Button(
            self.info_frame,
            text = 'Undo comment entry',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.handle_remove_comment_entry
        )
        self.multiple_undo_button = Tk.Button(
            self.info_frame,
            text = 'Undo multiple objects',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.handle_undo_multiple
        )
        self.img_canvas = Tk.Canvas(
                self.root,
                bg = CANVAS_BG,
                highlightthickness = 0)
        self.resize_canvas(DEFAULT_CANVAS_SIZE, DEFAULT_CANVAS_SIZE)
        self.img_canvas.grid(column = 1, row = 0)
        self.root.grid_columnconfigure(0, minsize = INFO_FRAME_WIDTH)
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def build_fonts(self):
        label = Tk.Label(self.root, text = 'sample')
        self.section_font = tkinter.font.Font(font = label['font'])
        size = self.section_font['size']
        self.section_font.config(size = size - 2)

    def resize_canvas(self, x, y):
        self.img_canvas.config(width = x, height = y)

    def build_code_labels(self, codes):
        for code in codes:
            self.define_code_label(code)

    def define_code_label(self, code):
        cl = CodeLabel(code, root = self.code_frame, row = len(self.code_labels),
                listen = self.root, handler = self.handle_code)
        self.code_labels.append(cl)

    def install_protocols(self):
        self.root.protocol('WM_DELETE_WINDOW', self.handle_delete_window)
        # On OS X (at least), quitting via Cmd+Q doesn't trigger
        # WM_DELETE_WINDOW, so we need to do it ourselves.
        atexit.register(self.handle_delete_window)

    def install_bindings(self):
        #Sets the key commands for different drop down options
        if sys.platform != 'darwin':
            # On macOS, the accelerators defined in the menu setup appear to
            # automatically add bindings when no meta key is defined, which
            # results in double events if we also add these bindings.
            self.root.bind('<Left>', self.handle_prev_image)
            self.root.bind('<Right>', self.handle_next_image)
        self.root.bind(meta_binding('s'), self.handle_save)
        self.root.bind(meta_binding('e'), self.handle_export)
        self.root.bind(meta_binding('o'), self.handle_open)
        self.root.bind(meta_binding('i'), self.handle_open_image)
        self.root.bind(meta_binding('v'), self.handle_open_context)
        self.root.bind(meta_binding('l'), self.handle_object_entry)
        self.root.bind(meta_binding('u'), self.handle_comment_entry)
        self.root.bind(meta_binding('r'), self.handle_find_replace)
        self.root.bind(meta_binding('Right'), self.handle_frontier)
        self.root.bind(meta_binding('Left'), self.handle_first)
        self.root.bind(meta_binding('.'), self.handle_repeated)
        self.root.bind(meta_binding('='), self.handle_multiple_objects)
        self.root.bind(meta_binding('x'), self.handle_clear_codes)

    def handle_multiple_objects(self, event = None):
        #If there are multiple objects in an image, the user indicates how
        #many objects are in the image and then the image is duplicated that number minus
        #one times so that each object can be coded one at a time. Both the ImcoImage object is 
        #duplicated and duplicates of the image itself are made and put into the directory folder
        try:
            self.handle_undo_multiple()
        except AttributeError:
            pass
        self.number_objects = simpledialog.askstring(
                title = "MULTIPLE OBJECTS",
                prompt = "How many objects are in the image?",
                parent = self.root)

        if (self.number_objects is None or len(self.number_objects) == 0):
            pass

        elif (self.number_objects == "1"):
            self.info("Whoops! You indicated that there is only one object in this image. If multiple objects are present, re-enter the correct number.")
    
        else:
            try:
                n = int(self.number_objects)
            except ValueError:
                self.info("Please enter a number greater than 1 to code multiple objects")
                return
            if n <= 1:
                self.info("Please enter a number greater than 1 to code multiple objects")
                return
            self.session.set_image_object_count(n)
            self.session.modified_images[self.session.img.path] = [self.session.img]
            # when there is more than one object in the image (as identified by the user), 
            # duplicate the target image so that individual objects can be coded on separate screens
            for i in range(n - 1):
                orig = self.session.img.path
                target = self.session.img.path[:-4] + '_DUPLICATE' + str(i + 1) + '.gif'
                path = shutil.copy(orig, target)
                img = ImcoImage(self.session.img.path, self.session.config.codes)
                img.object_count = n
                img.name = self.session.img.name[:-4] + '_DUPLICATE' + str(i + 1) + '.gif'
                self.session.dir.images.insert(self.session.img_index + 1, img)
                self.session.modified_images[self.session.img.path].append(img)
            self.info("You indicated that there are " + str(n) + " objects in this image. Code them one at a time.")
            self.multiple_undo_button.pack()
            self.object_count_label.config(text = str(self.session.img.object_count))
            self.order_label.config(text = str(self.session.img_index + 1) + ' of ' + str(len(self.session.load_images(self.session.dir))))

    def handle_undo_multiple(self, event = None):
        #Deletes all image duplicates in image list and directory folder and returns user to original image
        if 'DUPLICATE' in self.session.img.name:
            change = self.session.img.object_count-int(self.session.img.name[-5])
            self.session.img_index -= (change+1)
            self.handle_next_image_conditional() 
        if self.session.img.object_count==0:
            count = self.session.dir.images[self.session.img_index+1].object_count 
        else:
            count = self.session.img.object_count
        for i in reversed(range(count - 1)):
            name = self.session.dir.images[self.session.img_index + i + 1].name
            if self.session.dir.images[self.session.img_index + i + 1].is_coded(self.session.config.codes):
                self.session.db.delete_duplicate(name)
            del self.session.dir.images[self.session.img_index + i + 1]
            img = self.session.img.path[:-4] + '_DUPLICATE' + str(i + 1) + '.gif'
            os.remove(img)
        if self.session.img.object_count != 0:
            self.session.img.object_count = 1
        if self.session.img.is_coded(self.session.config.codes):
            self.session.modified_images[self.session.img.path] = self.session.img
            self.session.save()
        self.multiple_undo_button.pack_forget()
        self.object_count_label.config(text = str(self.session.img.object_count))
        self.order_label.config(text = str(self.session.img_index + 1) + ' of ' + str(len(self.session.load_images(self.session.dir))))

    def handle_clear_codes(self, event=None):
        #Clears ImcoImage codes dictionary and object and comment attributes
        self.session.img.codes = dict((c.code, None) for c in self.session.config.codes)
        for code_label in self.code_labels:
                code_label.set_from_image(self.session.img)
        self.session.img.object_name = ''
        self.session.img.comments = ''
        try:
            self.handle_remove_object_entry()
        except AttributeError:
            pass
        try:
            self.handle_remove_comment_entry()
        except AttributeError:
            pass
    
    def handle_open(self, event=None):
        #Opens set of images if they are contained in one directory
        path = tkinter.filedialog.askdirectory(
            initialdir = os.getcwd(),
            parent=self.root)
        if os.path.exists(path + '/state.db'):
            self.info("Wait a second! A state.db file already exists in your workdir. Make sure to close the program and delete this file if it's from an old image directory.")
        # TODO: Handle empty path, missing files, etc.
        try:
            self.open_workdir(path)
            if len(self.session.dirs) > 1:
                self.info("FYI: There are " + str(len(self.session.dirs)) + " image directories in your workdir. Close the program and remove any directories if needed.")
        except AttributeError:
            return

    def handle_open_image(self, event=None):
        #Allows user to access directory of images and navigate to a specific image
        self.set_prev_viewed_image()
        try:
            self.selected_image.destroy()
        except AttributeError:
            pass
        current_image_path = self.session.img.path
        self.current_dir_path = re.sub('([^\/]+$)', '', current_image_path)
        self.selected_image = tkinter.filedialog.askopenfilename(
                    initialdir = self.current_dir_path,
                    filetypes = [("image", "*.gif")],
                    parent = self.root)
        self.session.save()
        img_lst = self.session.load_images(self.session.dir)
        for index in range(len(img_lst)):
            if img_lst[index].path==self.selected_image:
                self.session.img_index = index-1
                self.handle_next_image_conditional()
                break
        self.prev_viewed_img_index -= 1

    # Makes list of image paths within 20 of the selected image and adds them to
    # ContextApp for creation of context images interface.
    def handle_open_context(self, event=None):
        #If there is a set of context images, the function starts a new limited imco session containing 
        #the 20 images before and after the current image for the user to view
        current_image_path = self.session.img.path
        self.current_dir_path = re.sub('([^\/]+$)', '', current_image_path)
        context_path = re.sub('images', 'context', self.current_dir_path)
        context_image_path = context_path + re.sub('.*/', '', current_image_path)
        paths = sorted(glob.glob(os.path.join(context_path, self.session.config.image_glob)))
        img_lst = []
        for index, path in enumerate(paths):
            current_index = paths.index(context_image_path)
            if index <= current_index + 20 and index >= current_index - 20:
                img_lst.append(path)
        max_x = self.session.config.image_max_x
        max_y = self.session.config.image_max_y
        if not os.path.isdir(context_path):
            self.info("Context not found! Make sure the 'images' and 'context' folders contain directories with matching names.")
        else:
            self.imagemenu.entryconfig('Next', state=Tk.DISABLED)
            self.imagemenu.entryconfig('Previous', state=Tk.DISABLED)
            context = ContextApp(img_lst, context_path, context_image_path, max_x, max_y)
            self.root.wait_window(context.root)
            self.imagemenu.entryconfig('Next', state=Tk.NORMAL)
            self.imagemenu.entryconfig('Previous', state=Tk.NORMAL)

    def handle_save(self, event=None):
        #Saves coded image objects to state.db file
        if self.session is not None:
            self.session.save()

    def handle_delete_window(self):
        #Closes session and saves progress on coded images
        if self._handled_delete_window:
            return
        if self.session is not None:
            self.session.save()
        self.app_state.save()
        self.root.destroy()
        self._handled_delete_window = True

    def handle_export(self, event=None):
        #Exports csv containing filled in codes, objects, comments, timestamps, and number of objects
        #for all fully coded images
        if  self.session is None:
            return
        self.initials = simpledialog.askstring(
            title = 'Enter your initials',
            prompt = '',
            parent = self.root)
        time = datetime.datetime.now()
        time_rep = str(time.year) + str(time.month).zfill(2) + str(time.day).zfill(2) + '_' + str(time.hour).zfill(2) + str(time.minute).zfill(2)
        if len(self.session.dirs)>1:
            path = 'multiple-dirs'
        else:
            path = re.sub('/', '', re.sub('([^\/]+$)', '', self.session.img_path))
        try:
            name = path + '_' + self.initials + '_' + time_rep
            fh = tkinter.filedialog.asksaveasfile(
                    mode='w',
                    defaultextension='.csv',
                    initialfile = name,
                    filetypes=[('CSV', '*.csv')],
                    parent=self.root)
            if fh:
                self.session.export_to_csv(fh)
                fh.close()
        except TypeError:
            pass

    def handle_code(self, code, value):
        #Fills in image object codes dictionary with values for each code
        if self.session:
            self.session.code_image(code, value)

    def handle_repeated(self, event=None):
        #Fills ImcoImage object with the same codes, object labels, and comments of sequentially
        #previous image, including duplicates if the previous image had multiple objects in the
        #image. Warns and stops the user if images are not being coded in sequential order. 
        if self.session.img.object_count > 1 and 'DUPLICATE' in self.session.img.name:
            self.info("Hold up! This is image is the same as the last one. You should be coding a different object.")
        elif self.session.dir.images[self.session.img_index-1].object_count > 1:
            if self.session.img.object_count > 1:
                self.handle_undo_multiple()
                try:
                    self.handle_remove_object_entry()
                except AttributeError:
                    pass
                try:
                    self.handle_remove_comment_entry()
                except AttributeError:
                    pass
            self.handle_clear_codes()
            self.session.save()
            n = self.session.dir.images[self.session.img_index-1].object_count
            self.session.set_image_object_count(n)
            self.session.set_image_repeated(self.session.dir._images[self.session.img_index-n].codes.copy())
            self.session.img.codes = self.session.img.repeated
            self.session.set_image_comments(self.session.dir._images[self.session.img_index-n].comments)
            self.session.set_image_object_name(self.session.dir._images[self.session.img_index-n].object_name)
            self.session.modified_images[self.session.img.path] = [self.session.img]
            for i in range(n - 1):
                orig = self.session.img.path
                target = self.session.img.path[:-4] + '_DUPLICATE' + str(i + 1) + '.gif'
                path = shutil.copy(orig, target)
                img = ImcoImage(self.session.img.path, self.session.config.codes)
                img.object_count = n
                img.name = self.session.img.name[:-4] + '_DUPLICATE' + str(i + 1) + '.gif'
                img.repeated = self.session.dir.images[self.session.img_index - n + i + 1].codes.copy()
                img.codes = img.repeated
                img.comments = self.session.dir.images[self.session.img_index - n + i + 1].comments
                img.object_name = self.session.dir.images[self.session.img_index - n + i + 1].object_name
                self.session.dir.images.insert(self.session.img_index + 1, img)
                self.session.modified_images[self.session.img.path].append(img)
            self.multiple_undo_button.pack()
            self.object_count_label.config(text = str(self.session.img.object_count))
            self.order_label.config(text = str(self.session.img_index + 1) + ' of ' + str(len(self.session.load_images(self.session.dir))))
            for code_label in self.code_labels:
                code_label.set_from_image(self.session.img)
            self.prev_text()
            self.session.save()
        elif self.session.img_index == 0:
            self.info("Whoops! This is the very first image, so it can't be coded as same as previous image.")
        elif self.session.img_index != self.prev_viewed_img_index + 1:
            self.info("Hold up! You're viewing images out of order. Double check that this image matches the preceding image in time.")
        else:
            self.session.set_image_repeated(self.session.dir._images[self.session.img_index-1].codes.copy())
            self.session.img.codes = self.session.img.repeated
            for code_label in self.code_labels:
                code_label.set_from_image(self.session.img)
            try:
                self.handle_remove_object_entry()
            except AttributeError:
                pass
            try:
                self.handle_remove_comment_entry()
            except AttributeError:
                pass
            self.session.set_image_comments(self.session.dir._images[self.session.img_index-1].comments)
            self.session.set_image_object_name(self.session.dir._images[self.session.img_index-1].object_name)
            self.prev_text()

    def handle_find_replace(self, event=None):
        #Prompts user to fill in an object name to replace, and a new object name to replace
        #it with, and replaces it for all ImcoImages with that object name
        self.find = simpledialog.askstring(
                title="FIND",
                prompt="Enter the object name you want to find",
                parent=self.root)
        try:
            self.replace = simpledialog.askstring(
                    title="REPLACE",
                    prompt="Enter the object name to replace: " + self.find.upper(),
                    parent=self.root)
        except AttributeError:
            return
        old_name = self.find
        if self.replace==None:
            return
        new_name = self.replace
        for img in self.session.dir.images:
            if img.object_name.find(old_name) != -1:
                img.object_name = img.object_name.replace(old_name, new_name)
                self.session.modified_images[img.path] = img
                self.session.save()  
        if self.session.img.object_name.find(new_name) != -1:
            self.object_name.pack_forget()
            self.object_undo_button.pack_forget()
            self.object_name = Tk.Label(
                self.info_frame,
                text = "Your object name(s): " + self.session.img.object_name,
                fg = '#05976c',
                bg = '#f6f6f6',
                wraplength=375)
            self.object_name.pack(fill=Tk.X)
            self.object_undo_button.pack()
        
    def handle_prev_image(self, event=None):
        #Loads sequentially previous image, including any previously coded attributes
        if self.session.img.is_coded(self.session.config.codes):
            if self.session.img.codes['None'] is not None:
                self.session.set_image_object_count(0)
            elif self.session.img.codes['None'] is None and self.session.img.object_count <=1:
                self.session.set_image_object_count(1)
        if self.session is None:
            return
        if self.session.prev_image():
            if self.prev_selected_image != None:
                if self.prev_selected_image == self.selected_image:
                    self.selected_image = None
            self.set_prev_viewed_image()
            self.draw_image()
            self.formatting()
        elif self.session.prev_dir():
            self.info('Going back to previous directory.')
            if self.prev_selected_image != None:
                if self.prev_selected_image == self.selected_image:
                    self.selected_image = None
            self.draw_image()
            self.formatting()
        else:
            self.info('This is the very first image.')

    def prev_text(self):
        #Loads previously filled in comments or object name text for an image
        if self.session.img.object_name != '':
            self.object_name = Tk.Label(
                self.info_frame,
                text = "Your object name(s): " + self.session.img.object_name,
                fg = '#05976c',
                bg = '#f6f6f6',
                wraplength=375)
            self.object_name.pack(fill=Tk.X)
            self.object_undo_button.pack()

        if self.session.img.comments != '':
            self.comments = Tk.Label(
                self.info_frame,
                text = "Your comments: " + self.session.img.comments,
                fg = '#05976c',
                bg = '#f6f6f6',
                wraplength=375)
            self.comments.pack(fill=Tk.X)
            self.comment_undo_button.pack()

    def formatting(self):
        #Clears remove object, comment and/or undo multiple buttons when moving 
        #to the next image 
        if not self.session.img_coded():
            self.session.update_frontier()
        self.object_undo_button.pack_forget()
        self.comment_undo_button.pack_forget()
        if self.session.img.object_count > 1:
            self.multiple_undo_button.pack()
        else:
            self.multiple_undo_button.pack_forget()
        try:
            self.object_name.pack_forget()
        except AttributeError:
            pass
        try:
            self.comments.pack_forget()
        except AttributeError:
            pass
        self.prev_text()

    def handle_next_image(self, event=None):
        #Loads next image in image list, but only if the image is fully coded
        if self.session.img.codes['None'] is not None:
            self.session.set_image_object_count(0)
        elif self.session.img.codes['None'] is None and self.session.img.object_count <=1:
            self.session.set_image_object_count(1)
        if self.session is None:
            return
        if not self.session.img_coded():
            self.info("This image isn't fully coded yet.")
            return
        update_image = False
        self.set_prev_viewed_image()
        if self.session.next_image():
            update_image = True
        elif self.session.next_dir():
            self.info("Hooray! It's a brand new directory.")
            update_image = True
        else:
            finished = True
            self.session.save()
            for dir in self.session.dirs:
                img_lst = self.session.load_images(dir)
                for img in img_lst:
                    if img.codes['Skipped'] is not None or not img.is_coded(self.session.config.codes):
                        finished = False
                        self.info("Remember to code skipped images.", title="Almost done!")
                        self.session.set_dir(self.session.dirs.index(dir))
                        self.session.img_index = img_lst.index(img) - 1
                        self.handle_next_image()
                        break
                break
            if finished:
                self.info("You reached the end! You're a coding god!", title="R U SRS???")
        if update_image:
            if self.prev_selected_image != None:
                if self.prev_selected_image == self.selected_image:
                    self.selected_image = None
            self.draw_image()
            self.formatting()

    def handle_next_image_conditional(self, event=None):
        #Loads next image in the image list even if it is not fully coded. Used for functions that 
        #Load images out of order 
        if self.session.img.is_coded(self.session.config.codes):
            if self.session.img.codes['None'] is not None:
                self.session.set_image_object_count(0)
            elif self.session.img.codes['None'] is None and self.session.img.object_count <=1:
                self.session.set_image_object_count(1)
        if self.session is None:
            return
        update_image = False
        if self.session.next_image():
            update_image = True
        elif self.session.next_dir():
            self.info("Hooray! It's a brand new directory.")
            update_image = True
        else:
            finished = True
            for dir in self.session.dirs:
                img_lst = self.session.load_images(dir)
                for img in img_lst:
                    if img.codes['Skipped'] is not None or not img.is_coded(self.session.config.codes):
                        finished = False
                        self.info("Remember to code skipped images.", title="Almost done!")
                        self.session.set_dir(self.session.dirs.index(dir))
                        self.session.img_index = img_lst.index(img) - 1
                        self.handle_next_image()
                        break
                break
            if finished:
                self.info("You reached the end! You're a coding god!", title="R U SRS???")
        if update_image:
            if self.prev_selected_image != None:
                if self.prev_selected_image == self.selected_image:
                    self.selected_image = None
            self.draw_image()
            self.formatting()

    def handle_frontier(self, event=None):
        #Loads next image that is not fully coded 
        if self.session is None:
            return
        self.session.jump_to_frontier_image()
        self.draw_image()

    def handle_first(self, event=None):
        #Loads image at the very beginning of the image list
        if self.session is None:
            return
        self.session.img_index = 1
        self.handle_prev_image()

    def handle_prev_skipped(self, event=None):
        #Loads first image appearing before the current one that was marked as skipped
        img_lst = self.session.load_images(self.session.dir)
        skipped = False
        for index in reversed(range(self.session.img_index)):
            if img_lst[index].codes['Skipped'] != None:
                self.prev_index = self.session.img_index
                self.session.img_index = index-1
                skipped = True
                self.handle_next_image_conditional()
                self.prev_viewed_img_index = self.prev_index
                break
        if not skipped:
            self.info("There are no skipped images in this direction.")

    def handle_next_skipped(self, event=None):
        #Loads first image appearing after the current one that was marked as skipped
        img_lst = self.session.load_images(self.session.dir)
        skipped = False
        for index in range(self.session.img_index+1, len(img_lst)):
            if img_lst[index].codes['Skipped'] != None:
                self.prev_index = self.session.img_index
                self.session.img_index = index-1
                skipped = True
                self.handle_next_image_conditional()
                self.prev_img_index = self.prev_index
                break
        if not skipped:
            self.info("There are no skipped images in this direction.")

    def open_workdir(self, path):
        #Opens directory of images, if it contains a config.json file
        #Activates file menu and image menu commands
        try:
            self.session = ImcoSession(path)
        except imco.config.InvalidConfig:
            try:
                if self.session.workdir is not None:
                    return
            except AttributeError:
                self.info("Invalid working directory: missing config.json")
                return
        self.app_state.set('workdir', path)
        self.build_code_labels(self.session.config.codes)
        self.resize_canvas(
                self.session.config.image_max_x,
                self.session.config.image_max_y)
        self.draw_image()
        self.prev_text()
        self.filemenu.entryconfig('Save', state=Tk.NORMAL)
        self.filemenu.entryconfig('Export codes to CSV', state=Tk.NORMAL)
        self.filemenu.entryconfig('Open specific image', state=Tk.NORMAL)
        self.filemenu.entryconfig('View context', state=Tk.NORMAL)
        self.filemenu.entryconfig('Check progress', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Previous', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Next', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Same as previous image', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Multiple objects', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Beginning', state=Tk.NORMAL)
        self.imagemenu.entryconfig('End', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Next Skipped', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Previous Skipped', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Clear codes', state = Tk.NORMAL)
        self.entrymenu.entryconfig('Add object name', state=Tk.NORMAL)
        self.entrymenu.entryconfig('Add comment', state=Tk.NORMAL)
        self.entrymenu.entryconfig('Find and replace object', state=Tk.NORMAL)


    def set_prev_viewed_image(self):
        self.prev_viewed_img_index = self.session.img_index

    def draw_image(self):
        #Resizes and draws image depending if an image was selected out of order or not
        if self.selected_image is not None and len(self.selected_image)>0:
            image = Image.open(self.session.img.path)
            image=image.resize((975, 750), Image.ANTIALIAS)
            self.photo_img = ImageTk.PhotoImage(image)
            self.img_canvas.create_image(510, 412, image=self.photo_img)
            self.path_label.config(text=re.sub('^(.*images/)|_DUPLICATE[0-9]', '', self.selected_image))
            self.order_label.config(text = str(self.session.img_index+1) + ' of ' + str(len(self.session.load_images(self.session.dir))))
            self.object_count_label.config(text = str(self.session.img.object_count))
            for code_label in self.code_labels:
                code_label.set_from_image(self.session.img)
            self.prev_selected_image = self.selected_image
        else:
            if self.photo_img is not None:
                self.img_canvas.delete(self.photo_img)
            image = Image.open(self.session.img.path)
            image=image.resize((975, 750), Image.ANTIALIAS)
            self.photo_img = ImageTk.PhotoImage(image)
            self.img_canvas.create_image(510, 412, image=self.photo_img)
            self.path_label.config(text=re.sub('_DUPLICATE[0-9]', '', self.session.img_path))
            self.order_label.config(text = str(self.session.img_index+1) + ' of ' + str(len(self.session.load_images(self.session.dir))))
            self.object_count_label.config(text = str(self.session.img.object_count))
            for code_label in self.code_labels:
                code_label.set_from_image(self.session.img)

    def info(self, msg, title=''):
        tkmb.showinfo(title, msg, parent=self.root)

class CodeLabel(object):
    UNSET_COLOR = '#8a8a8a'   # grey
    SET_COLOR = '#05976c'     # green
    EDITING_COLOR = '#304dc2' # blue
    PROMPT_TIMEOUT_MS = 60 * 1000 # 60s

    class UnchangedType:
        # Used as a sentinal to represent that the user wishes to leave a code
        # unchanged.
        pass

    Unchanged = UnchangedType()

    def __init__(self, code, root, row, listen, handler):
        self.root = root
        self.code = code
        self.value = None
        self.handler = handler
        self.prompt_cancel_id = None
        # UI elements
        self.key_label = Tk.Label(
                self.root,
                text=code.key,
                bg=DEFAULT_BG)
        self.key_label.grid(column=0, row=row)
        self.label = Tk.Label(
                self.root,
                anchor=Tk.W,
                justify=Tk.LEFT,
                bg=DEFAULT_BG)
        self.label.grid(column=1, row=row, sticky=Tk.W)
        listen.bind(self.code.key.lower(), self.handle_key)
        self.draw_label()

    def set_value(self, value):
        #Assigns value to a given code for display
        if value == self.value:
            return
        self.value = value
        self.draw_label()
        self.handler(self.code, value)

    def set_from_image(self, image):
        #Loads from existing image object codes dictionary to display
        value = image.codes.get(self.code.code, None)
        self.value = value
        self.draw_label()

    def draw_label(self):
        #Highlights codes that are selected for the image
        if self.value is None:
            text = self.code.label
            self.label.config(text=text, fg=self.UNSET_COLOR)
        else:
            text = "{}: {}".format(self.code.label, self.value)
            self.label.config(text=text, fg=self.SET_COLOR)

    def handle_key(self, event):
        if self.code.values is None:
            if self.value == '1':
                self.set_value(None)
            else:
                self.set_value('1')
        else:
            self.setup_prompt()

    def setup_prompt(self):
        if self.code.prompt is not None:
            values_text = self.code.prompt
        else:
            values = [v.upper() for v in self.code.values]
            values_text = "/".join(values)
        prompt = "{} [{}]".format(self.code.label, values_text)
        self.label.config(text=prompt, fg=self.EDITING_COLOR)
        self.label.bind('<Key>', self.handle_prompt)
        self.label.bind('<BackSpace>', self.revert_to_default)
        self.label.focus_set()
        self.prompt_cancel_id = self.label.after(
                self.PROMPT_TIMEOUT_MS, self.cancel_prompt)

    def handle_prompt(self, event):
        new_value = self.Unchanged
        if event.char.lower() in self.code.values:
            code = event.char.upper()
            if code != self.value:
                new_value = code
        self.cancel_prompt(new_value)
        return "break"

    def revert_to_default(self, event):
        self.cancel_prompt(new_value=None)
        return "break"

    def cancel_prompt(self, new_value=Unchanged):
        if self.prompt_cancel_id is not None:
            self.label.after_cancel(self.prompt_cancel_id)
        self.label.unbind('<Key>')
        self.label.unbind('<BackSpace>')
        if new_value is not self.Unchanged and new_value != self.value:
            self.set_value(new_value)
        else:
            self.draw_label()

class ContextApp(object):

    def __init__(self, img_lst, context_path, context_image_path, max_x, max_y):
        #Creates module on top of ImcoSession to scroll through nearby images
        self.root = Tk.Toplevel()
        self.context_path = context_path
        self.img_path = context_image_path
        self.img = None
        self.img_lst = img_lst
        self.current_index = self.img_lst.index(self.img_path)
        self.img_index = self.current_index
        self.target_index = self.current_index
        self.max_x = max_x / 2.05
        self.max_y = max_y / 2.5
        self.build_popup_window()
        self.open_image()

    def build_popup_window(self):
        #Window to display information about context images
        self.root.title("Context Images")
        self.root.config(bg=DEFAULT_BG)
        self.build_fonts()
        self.info_frame = Tk.Frame(self.root, bg=DEFAULT_BG)
        self.info_frame.grid(column=0, row=0, sticky=Tk.N+Tk.W, padx=10)
        self.path_section_label = Tk.Label(
                self.info_frame,
                anchor=Tk.W,
                justify=Tk.LEFT,
                font=self.section_font,
                fg=SECTION_FG,
                bg=DEFAULT_BG,
                text='PATH')
        self.path_section_label.pack(fill=Tk.X, pady=(10, 0))
        self.context_path_label = Tk.Label(
            self.info_frame,
            anchor=Tk.W,
            justify=Tk.LEFT,
            text = self.img_path,
            bg=DEFAULT_BG)
        self.context_path_label.pack(fill=Tk.X)
        self.next_button = Tk.Button(
            self.info_frame,
            text = 'Next image',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.next_context_image)
        self.next_button.pack()
        self.prev_button = Tk.Button(
            self.info_frame,
            text = 'Previous image',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.prev_context_image)
        self.prev_button.pack()
        self.target_button = Tk.Button(
            self.info_frame,
            text = 'Return to target image',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.open_image)
        self.target_image = Tk.Label(
            self.info_frame,
            anchor=Tk.W,
            justify=Tk.LEFT,
            text = 'You are currently viewing the target image.',
            fg = '#05976c',
            bg = DEFAULT_BG)
        self.target_button = Tk.Button(
            self.info_frame,
            text = 'Return to target image',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.open_image)
        self.context_img_canvas = Tk.Canvas(self.root,
            bg=CANVAS_BG,
            highlightthickness=0)
        self.context_img_canvas.grid(column=1, row=0)
        self.context_img_canvas.config(width=DEFAULT_CANVAS_SIZE + 300, height=DEFAULT_CANVAS_SIZE + 200)
        self.root.grid_columnconfigure(0, minsize=INFO_FRAME_WIDTH)
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def open_image(self):
        #First image opened is the one selected in the session and is the target image
        self.img_index = self.target_index
        self.img = Tk.PhotoImage(file=self.img_path)
        self.context_img_canvas.img = self.img
        self.create = self.context_img_canvas.create_image(self.max_x, self.max_y, image=self.context_img_canvas.img)
        self.context_path_label.config(text=re.sub('^(.*context/)', '', self.img_lst[self.img_index]))
        self.target_image.pack()
        self.target_button.pack_forget()

    def next_context_image(self):
        #Loads next sequential image in context set and draws it
        if self.img_index < len(self.img_lst) - 1 and self.img_index != self.target_index - 1:
            self.img_index += 1
            self.img = Tk.PhotoImage(file=self.img_lst[self.img_index])
            self.context_img_canvas.img = self.img
            self.new = self.context_img_canvas.create_image(self.max_x, self.max_y, image=self.context_img_canvas.img)
            self.context_img_canvas.itemconfig(self.new, image=self.context_img_canvas.img)
            self.context_path_label.config(text=re.sub('^(.*context/)', '', self.img_lst[self.img_index]))
            self.target_button.pack()
            self.target_image.pack_forget()
            self.target_button.pack()
        elif self.img_index == self.target_index - 1:
            self.open_image()
        else:
            self.info("No more context images in this direction!\n\nReturning to the target image.")
            self.open_image()

    def prev_context_image(self):
        #Loads previous sequential image in context set and draws it
        if self.img_index > 0 and self.img_index != self.target_index + 1:
            self.img_index -= 1
            self.img = Tk.PhotoImage(file=self.img_lst[self.img_index])
            self.context_img_canvas.img = self.img
            self.new = self.context_img_canvas.create_image(self.max_x, self.max_y, image=self.context_img_canvas.img)
            self.context_img_canvas.itemconfig(self.new, image=self.context_img_canvas.img)
            self.context_path_label.config(text=re.sub('^(.*context/)', '', self.img_lst[self.img_index]))
            self.target_button.pack()
            self.target_image.pack_forget()
            self.target_button.pack()
        elif self.img_index == self.target_index + 1:
            self.open_image()
        else:
            self.info("No more context images in this direction!\n\nReturning to the target image.")
            self.open_image()

    def build_fonts(self):
        label = Tk.Label(self.root, text='sample')
        self.section_font = tkinter.font.Font(font = label['font'])
        size = self.section_font['size']
        self.section_font.config(size = size-2)

    def delete_window(self):
        self.root.destroy()

    def info(self, msg, title=''):
        tkmb.showinfo(title, msg, parent=self.root)

if sys.platform == 'darwin':
    META_BINDING = 'Command'
    META_ACCELERATOR = 'Command'
else:
    META_BINDING = 'Control'
    META_ACCELERATOR = 'Ctrl'


def meta_accelerator(binding):
    return "{}+{}".format(META_ACCELERATOR, binding)


def meta_binding(binding):
    return "<{}-{}>".format(META_BINDING, binding)
