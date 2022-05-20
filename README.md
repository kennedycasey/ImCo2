# IMCO is an IMage COder

A Python Tkinter application for coding _lots_ of images.

IMCO ("IMage COder") is a Python-based application for efficiently annotating image directories with pre-defined, categorical values. Version 1 is available [here](https://github.com/marisacasillas/ImCo). The app as provided is set up for annotating child-centric daylong image streams, but the input values can be edited to fit your custom needs. The current version (Version 2) introduces a few new features - most notably, an option for including text entries in addition to pre-defined categories and an option to view context images. This version of the application is fully functional but still in development to meet the evolving needs of an ongoing annotation project.

## Running IMCO
Launch the application by running `app.py` in the imco directory (make sure the file is executable with Python 3 on your machine, e.g., `chmod +x app.py` for OSX with Python 3 installed).

When IMCO first runs, you'll need to open a your working directory (File > Open or ⌘ + O). This directory should contain a configuration .json file and a subdirectory called "images" that itself contains directories of images to code. The IMCO app will save your annotation data in a file called state.db that it creates in your working directory.

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
See below for a table of app functions. Most have associated key commands and can also be executed by clicking the file menu options.

| File menu option | Key command | Function |
| --- | --- | --- |
| File > Open specific image | ⌘ + I | Open any particular image in the current working directory |
| File > View context | ⌘ + V | Automatically pull up 20 images preceding and 20 images following the current target image for context |
| File > Save | ⌘ + S | Save progress |
| File > Export codes to CSV | ⌘ + E | Export your current state to a csv file |
| File > Check progress | n/a | Get the number of remaining images to be coded in the current directory |
| Image > Same as previous image | ⌘ + . | Code current image the same as the previous image |
| Image > Multiple objects | ⌘ + = | Duplicate images to code multiple objects separately | 
| Image > Clear codes | ⌘ + X | Remove existing hot key codes and/or text entries to recode from scratch |
| Image > Beginning | ⌘ + &#8592; | Return to the first image in the current directory | 
| Image > End | ⌘ + &#8594; | Jump to the next image to be coded | 
| Image > Next Skipped | n/a | Jump to the next skipped image | 
| Image > Previous Skipped | n/a | Jump to the previous skipped image |
| Text entry > Add object name | ⌘ + L | Pull up text entry box to add object name(s) | 
| Text entry > Add comment | ⌘ + U | Pull up text entry box to add comment(s) |
| Text entry > Find and replace object name | ⌘ + R | Relabel objects within the current directory |

## Removing functions
In order to remove functions from the app, enter the following into the command line while in the Imco2 directory:

python3 -c"import setup; setup.function()"

Where 'function()' can be replaced by one of the following:

**no_object_count()**: Removes functions and attributes for coding multiple objects in an image one at a time and noting the number of objects in an image

**no_object_label()**: Removes functions and attributes for editing and labeling objects in an image

**no_count_and labels()**: Runs both of the above functions

**switch_extension(extension)**: Imco is by default set up for images with a .gif extension. If you have images with a different extension, you can switch by running this function, where the parameter is the extenstion you would like to switch to (ex: switch_extension('jpg')). 

When one of these functions is run, the gui.py, session.py, and db.py files are overwritten with these changes in functionality. 

## Default annotation categories
The default annotation categories are described below. The annotation scheme was developed for a project investigating children's first-person object handling experiences.
| Hot key | Category | Second keystroke options | Value meaning |
| --- | --- | --- | --- |
| **O** | **Object out of frame** | Y, N | Is the handled object visible? "Y" means you cannot see any part of the object, "N" means that you can see at least a portion of the object |
| **R** | **Reaching** | Y, N | Is the handled object being reached for? "Y" means there is reaching, "N" means that there is hand-to-object contact. |
| **X** | **Study-related object** | n/a | Includes cameras, vests, headbands/hats, instructions, etc. that are present in the environment because the study is happening |
| **F** | **Food** | n/a | Includes food, drinks, and other consumables (e.g., drugs) |
| **C** | **Clothing** | n/a | Includes non-study-related items that can be worn (e.g., shirt, pants, shoe, necklace, purse, etc.) |
| **T** | **Toy** | n/a | Includes objects that are designed solely for recreational/play purposes, regardless of their size (e.g., ball, doll, sandbox, swing, slide, etc.) | 
| **B** | **Book** | n/a | Includes all books (for kids or adults), along with notebooks and paper | 
| **E** | **Electronic** | n/a | Includes all non-study-related and non-toy electronic devices (e.g., phone, baby monitor, tablet, etc.) |
| **P** | **Plant** | n/a | Includes all plants (e.g., leaf, grass, tree, flower, etc.) | 
| **A** | **Animal** | n/a | Includes all live animals and pets (e.g., dog, cat, chicken, frog, worm, etc.) |
| **W** | **Tool (work/cleaning)** | n/a | Includes household cleaning products, personal hygiene products, and other work tools (e.g., laundry detergent, dish soap, water (in handwashing/other washing contexts), lotion, toothbrush, broom, mop, harvesting tool, shovel, etc.) |
| **M** | **Tool (mealtime)** | n/a | Includes non-toy cups, bowls, spoons, forks, etc. that are typically used in a mealtime context (even if the current activity context is not mealtime) |
| **H** | **Other large, immovable object** | n/a | Includes furniture or housing structures that do not fall into any of the above categories (e.g., chair, table, floor, door, houseframe, veranda, patio deck, etc.) |
| **S** | **Other synthetic/manmade object** | n/a | Any non-natural object that does not fit into any of the above categories (e.g., miscellaneous container lid, rope, plastic packaging, etc.) |
| **N** | **Other natural object** | n/a | Any non-synthetic object that does not fit into any of the above categories (e.g., rock, sand, etc.) |
| **0** | **There is no held object** | n/a | There is no handled object in the image |
| **-** | **Too dark/blurry/covered to judge** | n/a | The image is too dark/blurry/covered to determine if there is a handled object |
| **?** | **Unsure what the object is** | n/a | There is a handled object but it is unclear what the label should be |
| **!** | **Flagged** | n/a | Notable example that would be good for a group discussion or conference presentation |
| **/** | **Skipped** | n/a | Return to this image later |


## Attribution
If you use IMCO, please cite the following:

Casey, K., Fisher, W., Tice, S. C., & Casillas, M. (2022). ImCo: A Python Tkinter application for coding _lots_ of images, version 2.0 [Computer software]. Retrieved from https://github.com/kennedycasey/ImCo2.
