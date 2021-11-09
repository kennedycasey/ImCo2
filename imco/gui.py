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

from imco.version import VERSION
from imco.session import ImcoSession
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
        self.root.option_add('*tearOff', False)
        self.menubar = Tk.Menu(self.root)
        self.appmenu = Tk.Menu(self.menubar, name='apple')
        self.filemenu = Tk.Menu(self.root)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.filemenu.add_command(
                label='Open workdir',
                command=self.handle_open,
                accelerator=meta_accelerator('O'))
        self.filemenu.add_command(
                label='Open specific image',
                command=self.handle_open_image,
                accelerator=meta_accelerator('I'),
                state=Tk.DISABLED)
        self.filemenu.add_command(
                label='View context',
                command=self.handle_open_context,
                accelerator=meta_accelerator('V'),
                state=Tk.DISABLED)
        self.filemenu.add_command(
                label='Save',
                command=self.handle_save,
                accelerator=meta_accelerator('S'),
                state=Tk.DISABLED)
        self.filemenu.add_command(
                label='Export codes to CSV...',
                command=self.handle_export,
                accelerator=meta_accelerator('E'),
                state=Tk.DISABLED)
        self.filemenu.add_command(
                label='Check progress',
                command=self.handle_check_progress,
                accelerator=meta_accelerator('P'),
                state=Tk.DISABLED)
        self.imagemenu = Tk.Menu(self.root)
        self.menubar.add_cascade(label='Image', menu=self.imagemenu)
        self.imagemenu.add_command(
                label='Previous',
                command=self.handle_prev_image,
                accelerator='Left',
                state=Tk.DISABLED)
        self.imagemenu.add_command(
                label='Next',
                command=self.handle_next_image,
                accelerator='Right',
                state=Tk.DISABLED)
        self.imagemenu.add_command(
                label='End',
                command=self.handle_frontier,
                accelerator=meta_accelerator('Right'),
                state=Tk.DISABLED)
        self.imagemenu.add_command(
            label='Next Skipped',
            command=self.handle_next_skipped,
            accelerator=meta_accelerator('Shift-Right'),
            state=Tk.DISABLED)
        self.imagemenu.add_command(
            label='Previous Skipped',
            command=self.handle_prev_skipped,
            accelerator=meta_accelerator('Shift-Left'),
            state=Tk.DISABLED)
        self.imagemenu.add_command(
            label='Same as previous image',
            command=self.handle_repeated,
            accelerator=meta_accelerator('.'))
        self.entrymenu = Tk.Menu(self.root)
        self.menubar.add_cascade(label='Text Entry', menu=self.entrymenu)
        self.entrymenu.add_command(
            label='Add object name',
            command=self.handle_object_entry,
            accelerator=meta_accelerator('L'),
            state=Tk.DISABLED)
        self.entrymenu.add_command(
            label='Add comment',
            command=self.handle_comment_entry,
            accelerator=meta_accelerator('U'),
            state=Tk.DISABLED)
        self.root.config(menu=self.menubar)

    def handle_object_entry(self, event=None):
        if self.session.img.object_name != '':
            self.handle_remove_object_entry()
        self.object_entry = simpledialog.askstring(
                title="Add object name(s)",
                prompt="Reminder: Make sure to add commas between names if there are 2+ objects",
                parent=self.root)
        if self.object_entry is not None:
            self.object_name = Tk.Label(
                self.info_frame,
                text = "Your object name(s): " + self.object_entry,
                fg = '#05976c',
                bg = '#f6f6f6')
            self.object_name.pack(fill=Tk.X)
            self.object_undo_button.pack()
            self.session.set_image_object_name(self.object_entry)

    def handle_remove_object_entry(self):
        self.object_undo_button.pack_forget()
        self.object_name.destroy()
        self.session.set_image_object_name('')

    def handle_remove_comment_entry(self):
        self.comment_undo_button.pack_forget()
        self.comments.destroy()
        self.session.set_image_comments('')

    def handle_comment_entry(self, event=None):
        if self.session.img.comments != '':
            self.handle_remove_comment_entry()
        self.comment_entry = simpledialog.askstring(
                title="Add comments",
                prompt="",
                parent=self.root)
        if self.comment_entry is not None:
            self.comments = Tk.Label(
                self.info_frame,
                text = "Your comments: " + self.comment_entry,
                fg = '#05976c',
                bg = '#f6f6f6')
            self.comments.pack(fill=Tk.X)
            self.comment_undo_button.pack()
            self.session.set_image_comments(self.comment_entry)

    def handle_check_progress(self, event=None):
        count = 0
        for dir in self.session.dirs:
            img_lst = self.session.load_images(dir)
            for img in img_lst:
                if not img.is_coded(self.session.config.codes) or img.codes['Skipped'] is not None:
                    count+=1
        self.info("Nice work! You have " + str(count) + " images left to code in this directory.")

    def build_main_window(self):
        self.root.title("IMCO  v{}".format(VERSION))
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
        self.path_label = Tk.Label(
                self.info_frame,
                anchor=Tk.W,
                justify=Tk.LEFT,
                bg=DEFAULT_BG)
        self.path_label.pack(fill=Tk.X)
        self.order_section_label = Tk.Label(
                self.info_frame,
                anchor=Tk.W,
                justify=Tk.LEFT,
                font=self.section_font,
                fg=SECTION_FG,
                bg=DEFAULT_BG,
                text='IMAGE NUMBER')
        self.order_section_label.pack(fill=Tk.X, pady=(10, 0))
        self.order_label = Tk.Label(
            self.info_frame,
                anchor=Tk.W,
                justify=Tk.LEFT,
                bg=DEFAULT_BG)
        self.order_label.pack(fill=Tk.X)
        self.codes_section_label = Tk.Label(
                self.info_frame,
                anchor=Tk.W,
                justify=Tk.LEFT,
                font=self.section_font,
                fg=SECTION_FG,
                bg=DEFAULT_BG,
                text='CODES')
        self.codes_section_label.pack(fill=Tk.X, pady=(10, 0))
        self.code_frame = Tk.Frame(self.info_frame, bg=DEFAULT_BG)
        self.code_frame.pack(fill=Tk.X)
        self.entries_section_label = Tk.Label(
                self.info_frame,
                anchor=Tk.W,
                justify=Tk.LEFT,
                font=self.section_font,
                fg=SECTION_FG,
                bg=DEFAULT_BG,
                text='TEXT ENTRIES')
        self.entries_section_label.pack(fill=Tk.X, pady=(10, 0))
        self.comment_exists=False
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
        self.img_canvas = Tk.Canvas(
                self.root,
                bg=CANVAS_BG,
                highlightthickness=0)
        self.resize_canvas(DEFAULT_CANVAS_SIZE, DEFAULT_CANVAS_SIZE)
        self.img_canvas.grid(column=1, row=0)
        self.root.grid_columnconfigure(0, minsize=INFO_FRAME_WIDTH)
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def build_fonts(self):
        label = Tk.Label(self.root, text='sample')
        self.section_font = tkinter.font.Font(font=label['font'])
        size = self.section_font['size']
        self.section_font.config(size=size-2)

    def resize_canvas(self, x, y):
        self.img_canvas.config(width=x, height=y)

    def build_code_labels(self, codes):
        for code in codes:
            self.define_code_label(code)

    def define_code_label(self, code):
        cl = CodeLabel(code, root=self.code_frame, row=len(self.code_labels),
                listen=self.root, handler=self.handle_code)
        self.code_labels.append(cl)

    def install_protocols(self):
        self.root.protocol('WM_DELETE_WINDOW', self.handle_delete_window)
        # On OS X (at least), quitting via Cmd+Q doesn't trigger
        # WM_DELETE_WINDOW, so we need to do it ourselves.
        atexit.register(self.handle_delete_window)

    def install_bindings(self):
        if sys.platform != 'darwin':
            # On macOS, the accelerators defined in the menu setup appear to
            # automatically add bindings when no meta key is defined, which
            # results in double events if we also add these bindings.
            self.root.bind('<Left>', self.handle_prev_image)
            self.root.bind('<Right>', self.handle_next_image)
        self.root.bind(meta_binding('Shift-Left'), self.handle_prev_skipped)
        self.root.bind(meta_binding('Shift-Right'), self.handle_next_skipped)
        self.root.bind(meta_binding('s'), self.handle_save)
        self.root.bind(meta_binding('e'), self.handle_export)
        self.root.bind(meta_binding('o'), self.handle_open)
        self.root.bind(meta_binding('i'), self.handle_open_image)
        self.root.bind(meta_binding('v'), self.handle_open_context)
        self.root.bind(meta_binding('p'), self.handle_check_progress)
        self.root.bind(meta_binding('l'), self.handle_object_entry)
        self.root.bind(meta_binding('u'), self.handle_comment_entry)
        self.root.bind(meta_binding('Right'), self.handle_frontier)
        self.root.bind(meta_binding('.'), self.handle_repeated)

    def handle_open(self, event=None):
        path = tkinter.filedialog.askdirectory(
            initialdir = os.getcwd(),
            parent=self.root)
        # TODO: Handle empty path, missing files, etc.
        self.open_workdir(path)

    def handle_open_image(self, event=None):
        self.set_prev_viewed_image()
        try:
            self.selected_image.destroy()
        except AttributeError:
            pass
        self.selected_image=tkinter.filedialog.askopenfilename(
                    initialdir = os.getcwd(),
                    filetypes=[("image", "*.gif")],
                    parent=self.root)
        self.session.save()
        img_lst = self.session.load_images(self.session.dir)
        for index in range(len(img_lst)):
            if img_lst[index].path==self.selected_image:
                self.session.img_index = index-1
                self.check_prev = True
                self.handle_next_image_conditional()
                break


    # Makes list of image paths within 20 of the selected image and adds them to
    # ContextApp for creation of context images interface.
    def handle_open_context(self, event=None):
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
        ContextApp(img_lst, context_path, context_image_path, max_x, max_y)

    def handle_save(self, event=None):
        if self.session is not None:
            self.session.save()

    def handle_delete_window(self):
        if self._handled_delete_window:
            return
        if self.session is not None:
            self.session.save()
        self.app_state.save()
        self.root.destroy()
        self._handled_delete_window = True

    def handle_export(self, event=None):
        if  self.session is None:
            return
        fh = tkinter.filedialog.asksaveasfile(
                mode='w',
                defaultextension='.csv',
                filetypes=[('CSV', '*.csv')],
                parent=self.root)
        if fh:
            self.session.export_to_csv(fh)
            fh.close()

    def handle_code(self, code, value):
        if self.session:
            self.session.code_image(code, value)

    def handle_repeated(self, event=None):
        if self.session.img_index == 0:
            self.info("Whoops! This is the very first image, so it can't be coded as same as previous image.")
        elif self.session.img_index != self.prev_viewed_img_index + 1:
            self.info("Hold up! You're viewing images out of order. Double check that this image matches the preceding image in time.")
        else:
            self.session.img.codes = self.session.dir._images[self.session.img_index-1].codes
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

    def handle_prev_image(self, event=None):
        if self.session is None:
            return
        self.set_prev_viewed_image()
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
            self.set_prev_viewed_image()
            self.draw_image()
            self.formatting()
        else:
            self.info('This is the very first image.')

    def prev_text(self):
        if self.session.img.object_name != '':
            self.object_name = Tk.Label(
                self.info_frame,
                text = "Your object name(s): " + self.session.img.object_name,
                fg = '#05976c',
                bg = '#f6f6f6')
            self.object_name.pack(fill=Tk.X)
            self.object_undo_button.pack()

        if self.session.img.comments != '':
            self.comments = Tk.Label(
                self.info_frame,
                text = "Your comments: " + self.session.img.comments,
                fg = '#05976c',
                bg = '#f6f6f6')
            self.comments.pack(fill=Tk.X)
            self.comment_undo_button.pack()

    def formatting(self):
        if not self.session.img_coded():
            self.session.update_frontier()
        self.object_undo_button.pack_forget()
        self.comment_undo_button.pack_forget()
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
        if self.session is None:
            return
        self.session.jump_to_frontier_image()
        self.draw_image()

    def handle_prev_skipped(self, event=None):
        self.set_prev_viewed_image()
        img_lst = self.session.load_images(self.session.dir)
        for index in reversed(range(self.session.img_index)):
            if img_lst[index].codes['Skipped'] != None:
                self.session.img_index = index-1
                self.check_prev = True
                self.handle_next_image_conditional()
                break

    def handle_next_skipped(self, event=None):
        self.set_prev_viewed_image()
        img_lst = self.session.load_images(self.session.dir)
        for index in range(self.session.img_index+1, len(img_lst)):
            if img_lst[index].codes['Skipped'] != None:
                self.session.img_index = index-1
                self.check_prev = True
                self.handle_next_image_conditional()
                break

    def open_workdir(self, path):
        try:
            self.session = ImcoSession(path)
        except imco.config.InvalidConfig:
            self.session = None
            self.info("Invalid working directory: missing config.json")
        if self.session is None:
            return
        self.app_state.set('workdir', path)
        self.build_code_labels(self.session.config.codes)
        self.resize_canvas(
                self.session.config.image_max_x,
                self.session.config.image_max_y)
        self.draw_image()
        self.prev_text()
        self.filemenu.entryconfig('Save', state=Tk.NORMAL)
        self.filemenu.entryconfig('Export codes to CSV...', state=Tk.NORMAL)
        self.filemenu.entryconfig('Open specific image', state=Tk.NORMAL)
        self.filemenu.entryconfig('View context', state=Tk.NORMAL)
        self.filemenu.entryconfig('Check progress', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Previous', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Next', state=Tk.NORMAL)
        self.imagemenu.entryconfig('End', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Next Skipped', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Previous Skipped', state=Tk.NORMAL)
        self.entrymenu.entryconfig('Add object name', state=Tk.NORMAL)
        self.entrymenu.entryconfig('Add comment', state=Tk.NORMAL)

    def set_prev_viewed_image(self):
        self.prev_viewed_img_index = self.session.img_index

    def draw_image(self):
        if self.selected_image is not None:
            self.photo_img = Tk.PhotoImage(file=self.selected_image)
            x = self.session.config.image_max_x / 2 - 1
            y = self.session.config.image_max_y / 2.42 - 1
            self.img_canvas.create_image(x, y, image=self.photo_img)
            self.path_label.config(text=re.sub('^(.*images/)', '', self.selected_image))
            self.order_label.config(text = str(self.session.img_index+1) + ' of ' + str(len(self.session.load_images(self.session.dir))))
            for code_label in self.code_labels:
                code_label.set_from_image(self.session.img)
            self.prev_selected_image = self.selected_image
        else:
            if self.photo_img is not None:
                self.img_canvas.delete(self.photo_img)
            self.photo_img = Tk.PhotoImage(file=self.session.img.path)
            x = self.session.config.image_max_x / 2 - 1
            y = self.session.config.image_max_y / 2.42 - 1
            self.img_canvas.create_image(x, y, image=self.photo_img)
            self.path_label.config(text=self.session.img_path)
            self.order_label.config(text = str(self.session.img_index+1) + ' of ' + str(len(self.session.load_images(self.session.dir))))
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
        if value == self.value:
            return
        self.value = value
        self.draw_label()
        self.handler(self.code, value)

    def set_from_image(self, image):
        value = image.codes.get(self.code.code, None)
        self.value = value
        self.draw_label()

    def draw_label(self):
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
        self.root = Tk.Toplevel()
        self.context_path = context_path
        self.img_path = context_image_path
        self.img = None
        self.img_lst = img_lst
        self.current_index = self.img_lst.index(self.img_path)
        self.img_index = self.current_index
        self.target_index = self.current_index
        self.max_x = max_x / 2-1
        self.max_y = max_y / 2.42-1
        self.build_popup_window()
        self.open_image()

    def build_popup_window(self):
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
            text = 'Go to target image',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = self.go_to_target)
        self.context_img_canvas = Tk.Canvas(self.root,
            bg=CANVAS_BG,
            highlightthickness=0)
        self.context_img_canvas.grid(column=1, row=0)
        self.context_img_canvas.config(width=DEFAULT_CANVAS_SIZE + 200, height=DEFAULT_CANVAS_SIZE)
        self.root.grid_columnconfigure(0, minsize=INFO_FRAME_WIDTH)
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def open_image(self):
        self.img_index = self.target_index
        self.img = Tk.PhotoImage(file=self.img_path)
        self.context_img_canvas.img = self.img
        self.create = self.context_img_canvas.create_image(self.max_x, self.max_y, image=self.context_img_canvas.img)
        self.context_path_label.config(text=re.sub('^(.*context/)', '', self.img_lst[self.img_index]))
        self.target_image.pack()
        self.target_button.pack_forget()

    def next_context_image(self):
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

    def go_to_target(self):
        if self.img_index != self.target_index:
            self.target_button.pack_forget()
            self.open_image()

    def build_fonts(self):
        label = Tk.Label(self.root, text='sample')
        self.section_font = tkinter.font.Font(font=label['font'])
        size = self.section_font['size']
        self.section_font.config(size=size-2)

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
