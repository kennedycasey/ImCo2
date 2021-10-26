import tkinter as Tk
from tkinter import Toplevel
from tkinter import simpledialog
import tkinter.messagebox as tkmb
import tkinter.filedialog
import tkinter.font
import atexit
import os
import sys
import re
import webbrowser

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
        #self.top = Toplevel()
        self.app_state = app_state
        self.session = None
        # A list of CodeLabel instances.
        self.code_labels = []
        # The PhotoImage instance for the currently-displayed image.
        self.photo_img = None
        self.selected_image = None
        self.prev_selected_image = None
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
                label='Open',
                command=self.handle_open,
                accelerator=meta_accelerator('O'))
        self.filemenu.add_command(
                label='Open specific image',
                command=self.handle_open_image,
                accelerator=meta_accelerator('I'))
        self.filemenu.add_command(
                label='View context',
                command=self.handle_open_context,
                accelerator=meta_accelerator('C'))
        self.filemenu.add_command(
                label='Save',
                command=self.handle_save,
                accelerator=meta_accelerator('S'),
                state=Tk.DISABLED)
        self.filemenu.add_command(
                label='Export codes to CSV...',
                command=self.handle_export,
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
            state=Tk.DISABLED)
        self.imagemenu.add_command(
            label='Previous Skipped',
            command=self.handle_prev_skipped,
            state=Tk.DISABLED)
        self.root.config(menu=self.menubar)

    def build_object_entry(self):
        self.object_entry = simpledialog.askstring(
                title="Add object name(s)",
                prompt="Reminder: Make sure to add commas between names if there are 2+ objects")
        self.object_name = Tk.Label(
                self.info_frame,
                text = "Your object name(s): " + self.object_entry,
                fg = '#05976c',
                bg = '#f6f6f6')
        self.object_name.pack(fill=Tk.X)
        self.session.img.object_name = self.object_entry
        if self.object_entry != '':
            self.session.modified_images[self.session.img.path] = self.session.img
        self.object_entry_button.pack_forget()

    def build_comment_entry(self):
        self.comment_entry = simpledialog.askstring(
                title="Add comments",
                prompt="")
        self.comments = Tk.Label(
                self.info_frame,
                text = "Your comments: " + self.comment_entry,
                fg = '#05976c',
                bg = '#f6f6f6')
        self.comments.pack(fill=Tk.X)
        self.session.img.comments = self.comment_entry
        if self.comment_entry != '':
            self.session.modified_images[self.session.img.path] = self.session.img
        self.comment_entry_button.pack_forget()

    def build_main_window(self):
        self.root.title("IMCO  v{}".format(VERSION))
        self.root.config(bg=DEFAULT_BG)
        #self.root.tk_setPalette(background=DEFAULT_BG)
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
        #self.image_select_button = Tk.Button(
            #self.info_frame,
            #text = "Open specific image",
            #bg = DEFAULT_BG,
            #highlightbackground = DEFAULT_BG,
            #command = self.build_image_select)
        #self.image_select_button.pack()
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
        self.object_entry_button = Tk.Button(
                self.info_frame,
                text = "Add object name(s)",
                bg = DEFAULT_BG,
                highlightbackground = DEFAULT_BG,
                #command = self.build_object_entry
                command = lambda:[self.build_object_entry(),
                    self.object_undo_button.pack(),
                    self.object_entry_button.pack_forget()]
                )
        self.object_entry_button.pack()
        self.comment_entry_button = Tk.Button(
                self.info_frame,
                text = "Add comments",
                bg = DEFAULT_BG,
                highlightbackground = DEFAULT_BG,
                command = lambda:[self.build_comment_entry(),
                    self.comment_undo_button.pack(),
                    self.comment_entry_button.pack_forget()]
                )
        self.comment_entry_button.pack()
        self.comment_exists=False
        self.object_undo_button = Tk.Button(
            self.info_frame,
            text = 'Undo object entry',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = lambda:[self.object_entry_button.pack(),
                self.object_undo_button.pack_forget(),
                self.object_name.destroy()]
        )
        self.comment_undo_button = Tk.Button(
            self.info_frame,
            text = 'Undo comment entry',
            bg = DEFAULT_BG,
            highlightbackground = DEFAULT_BG,
            command = lambda:[self.comment_entry_button.pack(),
                self.comment_undo_button.pack_forget(),
                self.comments.destroy()]
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

    #def entry_label(self):
        #el = Label()

    def install_protocols(self):
        self.root.protocol('WM_DELETE_WINDOW', self.handle_delete_window)
        # On OS X (at least), quitting via Cmd+Q doesn't trigger
        # WM_DELETE_WINDOW, so we need to do it ourselves.
        atexit.register(self.handle_delete_window)

    def install_bindings(self):
        self.root.bind('<Left>', self.handle_prev_image)
        self.root.bind('<Right>', self.handle_next_image)
        self.root.bind('<Return>', self.handle_next_image)
        self.root.bind('<Shift-Left>', self.handle_prev_skipped)
        self.root.bind('<Shift-Right>', self.handle_next_skipped)
        self.root.bind(meta_binding('s'), self.handle_save)
        self.root.bind(meta_binding('o'), self.handle_open)
        self.root.bind(meta_binding('i'), self.handle_open_image)
        self.root.bind(meta_binding('c'), self.handle_open_context)
        self.root.bind(meta_binding('Right'), self.handle_frontier)

    def handle_open(self, event=None):
        path = tkinter.filedialog.askdirectory(initialdir = os.getcwd(),
            parent=self.root)
        # TODO: Handle empty path, missing files, etc.
        self.open_workdir(path)

    def handle_open_image(self, event=None):
        try:
            self.selected_image.destroy()
        except AttributeError:
            pass
        self.selected_image=tkinter.filedialog.askopenfilename(
                    initialdir = os.getcwd(),
                    filetypes=[("image", "*.gif")],
                    parent=self.root)
        self.session.save()
        #for dir in self.session.dirs:
        img_lst = self.session.load_images(self.session.dir)
        for index in range(len(img_lst)):
            if img_lst[index].path==self.selected_image:
                self.session.img_index = index-1
                self.handle_next_image()
                break
            #break
        self.draw_image()

    def handle_open_context(self, event=None):
        context_path = tkinter.filedialog.askdirectory(initialdir = os.getcwd(),
            parent=self.root)
        current_image_path = self.session.img.path
        context_image_path = context_path + '/' + re.sub('.*/', '', current_image_path)
        webbrowser.open(context_path)
        #load = Image.open(context_image_path)
        #render = Tk.PhotoImage(load)

    def handle_save(self, event=None):
        if self.session is not None:
            self.session.save()

    def handle_delete_window(self):
        if self.session is not None:
            self.session.save()
        self.app_state.save()
        self.root.destroy()

    def handle_export(self, event=None):
        if  self.session is None:
            return
        fh = tkinter.filedialog.asksaveasfile(
                mode='w',
                defaultextension='.csv',
                filetypes=[('CSV', '*.csv')])
        if fh:
            self.session.export_to_csv(fh)
            fh.close()

    def handle_code(self, code, value):
        if self.session:
            self.session.code_image(code, value)

    def handle_prev_image(self, event=None):
        if self.session is None:
            return
        if self.session.prev_image():
            self.draw_image()
        elif self.session.prev_dir():
            tkmb.showinfo('', 'Going back to previous directory.')
            self.draw_image()
        else:
            tkmb.showinfo('', 'This is the very first image.')

    def handle_next_image(self, event=None):
        if self.session is None:
            return
        if not self.session.img_coded():
            tkmb.showinfo('', "This image isn't fully coded yet.")
            return
        update_image = False
        if self.session.next_image():
            update_image = True
        elif self.session.next_dir():
            tkmb.showinfo('', "Hooray! It's a brand new directory.")
            update_image = True
        else:
            tkmb.showinfo('R U SRS???',
                    "You reached the end! You're a coding god!")
        if update_image:
            if self.prev_selected_image != None:
                if self.prev_selected_image == self.selected_image:
                    self.selected_image = None
            self.draw_image()
            if not self.session.img_coded():
                self.session.update_frontier()
            self.object_entry_button.pack()
            self.comment_entry_button.pack()
            self.object_undo_button.pack_forget()
            self.comment_undo_button.pack_forget()
            try:
                self.comments.pack_forget()
            except AttributeError:
                pass
            try:
                self.object_name.pack_forget()
            except AttributeError:
                pass

    def handle_frontier(self, event=None):
        if self.session is None:
            return
        self.session.jump_to_frontier_image()
        self.draw_image()

    def handle_prev_skipped(self, event=None):
        img_lst = self.session.load_images(self.session.dir)
        for index in range(self.session.img_index):
            if img_lst[index].codes['Skipped'] != None:
                self.session.img_index = index-1
                self.handle_next_image()
                break

    def handle_next_skipped(self, event=None):
        img_lst = self.session.load_images(self.session.dir)
        for index in range(self.session.img_index+1, len(img_lst)):
            if img_lst[index].codes['Skipped'] != None:
                self.session.img_index = index-1
                self.handle_next_image()
                break

    def open_workdir(self, path):
        try:
            self.session = ImcoSession(path)
        except imco.config.InvalidConfig:
            self.session = None
            tkmb.showinfo('', "Invalid working directory: missing config.json")
        if self.session is None:
            return
        self.app_state.set('workdir', path)
        self.build_code_labels(self.session.config.codes)
        self.resize_canvas(
                self.session.config.image_max_x,
                self.session.config.image_max_y)
        self.draw_image()
        self.filemenu.entryconfig('Save', state=Tk.NORMAL)
        self.filemenu.entryconfig('Export codes to CSV...', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Previous', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Next', state=Tk.NORMAL)
        self.imagemenu.entryconfig('End', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Next Skipped', state=Tk.NORMAL)
        self.imagemenu.entryconfig('Previous Skipped', state=Tk.NORMAL)

    def draw_image(self):
        #try:
        if self.selected_image is not None:
            self.photo_img = Tk.PhotoImage(file=self.selected_image)
            x = self.session.config.image_max_x / 2 - 1
            y = self.session.config.image_max_y / 2 - 1
            self.img_canvas.create_image(x, y, image=self.photo_img)
            self.path_label.config(text=re.sub('^(.*images/)', '', self.selected_image))
            self.prev_selected_image=self.selected_image
            # TO DO: need to recognize match between files with same path,
            # then update code values accordingly
            #for code_label in self.code_labels:
                #code_label.set_from_image(re.sub('^(.*images/)', '', self.selected_image))
        #except AttributeError:
        else:
            if self.photo_img is not None:
                self.img_canvas.delete(self.photo_img)
            self.photo_img = Tk.PhotoImage(file=self.session.img.path)
            x = self.session.config.image_max_x / 2 - 1
            y = self.session.config.image_max_y / 2 - 1
            self.img_canvas.create_image(x, y, image=self.photo_img)
            self.path_label.config(text=self.session.img_path)
            for code_label in self.code_labels:
                code_label.set_from_image(self.session.img)

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

if sys.platform == 'darwin':
    META_BINDING = 'Command'
    META_ACCELERATOR = 'Cmd'
else:
    META_BINDING = 'Control'
    META_ACCELERATOR = 'Ctrl'


def meta_accelerator(binding):
    return "{}+{}".format(META_ACCELERATOR, binding)


def meta_binding(binding):
    return "<{}-{}>".format(META_BINDING, binding)
