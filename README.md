# IMCO is an IMage COder

A Python Tkinter application for coding _lots_ of images.

IMCO ("IMage COder") is a Python-based application for efficiently annotating image directories with pre-defined, categorical values. Version 1 is available [here](https://github.com/marisacasillas/ImCo). The app as provided is set up for annotating child-centric daylong image streams, but the input values can be edited to fit your custom needs. The current version (version 2) introduces a few new features -- most notably, an option for including text entries in addition to pre-defined categories and an option to view context images.

## Running IMCO
Launch the application by running `app.py` in the imco directory (make sure the file is executable with Python 3 on your machine, e.g., `chmod +x app.py` for OSX with Python 3 installed).

When ImCo first runs, you'll need to open a your working directory (File > Open or cmd + o). This directory should contain a configuration .json file and a subdirectory called "images" that itself contains directories of images to code. The ImCo app will save your annotation data in a file called state.db that it creates in your working directory.

The structure of the working directory is as follows:

* `config.json` (sets a number of options for how to code the images)
* `images/` (a directory of directories, each one containing images to code)
  * `P1-39moM/` (a directory of images to code for one participant)
    *  `image001.gif` (a .gif to annotate)
    *  `image002.gif` (another .gif to annotate)
    *  ...
* `context/` (a directory of directories, matching the participants in the `images/` directory)
  * `P1-39moM/` (a directory of images including and surrounding the images to code for reference)
    *  `context-image001.gif` (a .gif to serve as a reference while annotating)
    *  `context-image002.gif` (another .gif)
    *  ...
* `state.db` (auto-generated database containing application state; **only present after you have opened a working directory**)


## Default functions
See below for a table of app functions. Most have associated key commands, and can also be executed by clicking the file menu options.

| File menu option | Key command | Function |
| --- | --- | --- |
| File > Open specific image | ⌘ + I | Open any particular image in the current working directory |
| File > View context | ⌘ + V | Automatically pull up 20 images preceding and 20 images following the current target image for context |
| File > Save | ⌘ + S | Save progress |
| File > Export codes to CSV | ⌘ + E | Export your current state to a csv file |
| File > Check progress | n/a | Get the number of remaining images to be coded in the current directory |
| Image > Beginning | ⌘ + &#8592; | Return to the first image in the current directory | 
| Image > End | ⌘ + &#8594; | Jump to the next image to be coded | 
| Image > Next Skipped | n/a | Jump to the next skipped image | 
| Image > Previous Skipped | n/a | Jump to the previous skipped image |
| Image > Same as previous image | ⌘ + . | Code current image the same as the previous image |
| Image > Multiple objects | ⌘ + = | Duplicate images to code multiple objects separately | 
| Text entry > Add object name | ⌘ + L | Pull up text entry box to add object name(s) | 
| Text entry > Add comment | ⌘ + U | Pull up text entry box to add comment(s) |

## Attribution
If you use IMCO (version 2), please cite one of the following:

Casillas, M., Casey, K., Fisher, W., & Tice, S. C. (2021). ImCo: A Python Tkinter application for coding _lots_ of images, version 2 [Computer software]. Retrieved from https://github.com/kennedycasey/ImCo2.
