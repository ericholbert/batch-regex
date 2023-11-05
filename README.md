# Batch RegEx
A GUI multi-file regex tool using the Python regex engine for search and replace operations. A basic use case is the following: the program first chains files that match given patterns, then displays all changes to data based on the replacement string. Changes aren’t applied until the user saves them.
![example](/../main/assets/example.png)

# Requirements
* Python 3

# Getting started
1. `cd` into `project/bregex`
2. Run `python3 ./gui.py`

# Features
## Load files
* Work with multiple files
* Add multiple file/dir paths as the input source
* Search through directories recursively and filter files using a matching pattern

## Find and replace
* Find and replace using the Python re module with support for re.IGNORECASE, re.DOTALL and re.MULTILINE flags (if needed, it should be easy to add another one inside the "regex.py" script)
* On top of the basic search, you can search a path string or find files that doesn’t match a pattern
* Chain files that match specified patterns
* Apply only selected replacements, even in one file
* Keep chaining files even after typing an invalid pattern or try different replacements as long as you don’t save changes to disk
* Save changes to disk (**DISCLAIMER!** Keep copies of input files for when the program may behave unpredictably due to its current state of development)

## Others
* A GUI to help you keep track of data manipulation
* Basic key bindings
