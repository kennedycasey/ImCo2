# ImCo is IMage COder

A Python Tkinter application for coding _lots_ of images.

ImCo ("IMage COder") is a Python-based application for efficiently annotating image directories with pre-defined, categorical values. The app as provided is set up for annotating child-centric daylong image streams but the input values can of course be edited to your custom needs.

## Setup

Launch the application by running `app.py` in the `imco` directory (make sure the file is executable with [Python 3](https://www.python.org/downloads/) on your machine, e.g., `chmod +x app.py` for OSX with Python 3 installed).

When ImCo first runs, you'll need to open a your working directory (File > Open or cmd + o). This directory should contain a configuration .json file and a subdirectory called "images" that itself contains directories of images to code. The ImCo app will save your annotation data in a file called `state.db` that it creates in your working directory.

The structure of the working directory is as follows:

- `config.json` (sets a number of options for how to code the images)
- `images/` (a directory of directories, each one containing images to code)
  - `P1-39moM/` (a directory of images for one participant)
      - `image001.gif` (a .gif to annotate)
      - `image002.gif` (another .gif)
      - ...
  - `P1-7moF/` (another participant)
  - ...
- `state.db` (auto-generated database containing application state; **only present after you have opened a working directory**)

### Adding your images

This repository contains an example working directory `workdir` that is already set up with the files you need to initiate a new round of annotation, plus some example image subdirectories, `P1-39moM/` and `P1-7moF/`. By default ImCo expects gifs (for our project we use [ImageMagick](https://imagemagick.org/index.php) to batch convert directories with `gm mogrify -monitor -resize 1000x1000 -format gif recording_session/*.jpg`).

To begin annotating your own images, first ensure that your images are .gifs (see `config.json` to change) that are divided into labeled subdirectories as needed for your project (we use one directory per recording session for each child). Copy those subdirectories into the `images` directory provided here. If there is a `state.db` file and you have not yet begun annotating, delete it.

Now launch the application, select the provided `workdir` working directory, which now contains your images, and start annotating (see below). When you do, it will create a new `state.db` file that stores your annotations and your current progress in the working directory.

If you make a mistake selecting images or you want to start from a clean slate for some other reason, delete `state.db`. However, keep in mind that this action will cause you to lose any coding work you've already done that may be stored in `state.db`.

Please note that the application will save automatically as you annotate images, but we recommend that you periodically export your working database file to a csv file, just in case something goes wrong (see below).

### Saving and exporting annotations

When you are done annotating the files in your working directory, store your completed .db file in a safe place of your choosing and/or convert it to a .csv file for further analysis. You can of course also do so as a form of backup before you have completed your work in that directory.

### Moving between working directories

If, at this point, you would like to re-use the same working directory with new files, you can save your completed .db file elsewhere, then delete `state.db` and the old images from the `workdir` folder, adding in your new images. Once you launch the app again and select the working directory, a fresh `state.db` file will appear to store your new annotations. Note that you can also create any number of new working directories, so long as each contains the config file and a subdirectory `images/` that contains the directories of images you want to annotate.

### Converting .db files to .csv

In your terminal, call `db2csv.py` to convert a .db file to a .csv. This script expects up to three arguments:

* the path to the working directory where your `state.db` file is stored (required)
* the name of the annotator associated with this file
* a flag `-o` followed by a name for your output file (optional)

For example, if you only use the example directory we have set up, you might call `./db2csv.py workdir/state.db Annotator` to create a file called `state.csv` in the top-level ImCo directory. Alternatively you might call `./db2csv.py workdir/state.db Annotator -o workdir/annotator1-20210817.csv` to create a file called `annotator1-20210817.csv` in the `workdir/` directory. How you name and place your files is up to you, just be careful not to overwrite your annotations!

An example of csv output is given in the file `example-output.csv`.

## Annotating in ImCo

ImCo is set up for quick annotation and navigation via hotkeys—single keystrokes that enable the annotator to enter data and move between images. The image name and path is shown in the upper left hand corner, together with the current annotation values for that image, with the image shown on the right hand side.

![](example-imco-frame.png)

### Primary annotation

For each annotation category, there should be a unique initial keystroke value (e.g., "A" to enter the number of visible adults) which can then optionally lead to a more refined annotation value (e.g., the numbers 0-9; see below for examples via the default annotation types).

### Navigation

To navigate through the images use the following keystrokes:

* Previous image: left arrow
* Next image: right arrow OR enter
* Last coded image: cmd + right arrow

### In-app messages

It's easy to lose track of one's place while navigating large image collections, so ImCo provides a number of short messages to alert the annotator to issues that may be helpful along the way.

If you haven't completed all the required annotation types for an image the app will show a pop up message that says "This image isn't fully coded yet.".

If your `workdir/images` directory contains several subdirectories (e.g., multiple image stream recording sessions) then the app will show a pop up meessage to alert you when you're moving between directories with "Hooray! It's a brand new directory.".  If you navigate back from one directory to a previous one it will let you know with "Going back to previous directory.".

If you navigate back to the first image in the directory, the app will let you know with "This is the very first image". Similarly, if you reach the last images, the app will say "You reached the end! You're a coding god!".

### Customizing annotation types

You may customize the annotation types accepted by ImCo by editing the `config.json` file. Note that your initial keystroke values must be unique across your annotation categories (e.g., we can't use 'c' for both 'Kids/Children' and 'Crying' in the example below). Within annotation categories, the value keystroke options must also be unique (e.g., we can't use 'o' for both 'Dark/Obscured' and 'Other' in the Unusable annotation category).

### Default annotation types

The default annotation categories are set to be used as follows:

| Annotation category | Initial keystroke | Value keystroke options | Value meaning |
|---|---|---|---|
| Adults | a | 0–9 | The number of people who look to be of child-bearing age or older in the image, not including the person wearing the camera. More than 9 can be marked with “9”. | 
| Kids | k | 0–9 | The number of people who look to be below child-bearing age in the image, not including the person wearing the camera. More than 9 can be marked with “9”. |
| Hands | h | C, I, B, N | **C = the target child** is holding/handling something or appears to be mid-activity with a held object/person. **I = one or more of the child’s interactants** is holding/handling something in a way immediately relevant to the target child (e.g., handing them something, cleaning their face). **B = both the target child and one or more of their interactants** are holding/handling something, as defined above. **N = there is no holding/handling behavior.** |
| Crying | c | N/A | Set to no by default. Use of this flag by the annotator indicates that any child in the image is crying. |
| Breastfeeding | b | N/A | Set to no by default. Use of this flag by the annotator indicates that any child in the image is being breastfed. |
| Flagged | f | N/A | Set to no by default. Use of this flag by the annotator indicates that the image is interesting for some reason and we should come back to it later; please make a separate note with the participant and image number for images with specific comments. | 
| Unusable | u | D, C, O |  Set to no by default. Otherwise: D = the image is too dark or too light to see anything. C = the camera cover is on. O = other cases, including the images at the beginning and the end when the researchers are still present. **NOTE: If you mark a image as unusable, you do not have to fill in any of the other codes.** |
| Skipped | s | N/A | Set to no by default. Use if you would like to skip this image, leaving all the other code fields blank. |

These default annotation types were designed for a specific project and thus may not be suitable for your goals. The repository for that project, including original instructions is available here [repository: ADD-LINK; original [annotation table](https://docs.google.com/document/d/1aQlpB9N8LVAfzuac_XqZzhWiKQ6AptsDzHxLDKrJAOA/edit?usp=sharing) and [training tips](https://docs.google.com/document/d/1pbTZkqBBTE_aFawVr5daiIKrKVc1kdvi8lX65cwpn3A/edit?usp=sharing)]. We encourage you to adapt these annotations as needed for your project, though we note that re-use of categories where relevant increases comparability across studies.

## Attribution

If you use ImCo, please cite one of the following:

Casillas, M. & Tice, Shawn C. (2021). ImCo: A Python Tkinter application for coding _lots_ of images [Computer software]. Retrieved from [https://github.com/marisacasillas/ImCo.]()
