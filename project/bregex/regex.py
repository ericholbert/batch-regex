"""
This module defines a library for broader regex processing using the Python re
module (see the GitHub project page for details). It consists of four public
classes for instantiating Files, Options, Finder and Replacer objects. These
are mutually related, so a Files and an Options object are passed to a Finder
object, which in turn is passed to a Replacer object. Such a structure means
that after passing an instantiated object, its state shouldn’t be manipulated
anymore to prevent undesirable results.
"""

import os
import re


FILEPATH = 0
FILECONTENT = 1
IF = 2
IFNOT = 3
NULL = 4
BINARY = 5


class Options():
    """
    A simple class for storing settings related to data search and
    manipulation.
    """

    def __init__(self,
                 data_type=FILECONTENT,
                 ignore_case=False,
                 multiline=False,
                 dot_all=False,
                 ignore_diacritics=False):
        self.data_type = data_type
        self.ignore_case = ignore_case
        self.multiline = multiline
        self.dot_all = dot_all
        # TODO
        self.ignore_diacritics = ignore_diacritics

    def get_flags(self):
        """
        Flags are combined using the bitwise or operator and ready to be
        passed to a re module function.
        """
        flags = 0
        if self.ignore_case:
            flags |= re.IGNORECASE
        if self.multiline:
            flags |= re.MULTILINE
        if self.dot_all:
            flags |= re.DOTALL
        return flags


class Files:
    """
    A class for open, store and write operations on files. It is not
    responsible for any changes made to data.
    Current state of the object is accessible via public attributes self.paths
    and self.contents.
    """

    def __init__(self):
        self.paths = []
        self.contents = []
        
        self._path_changes_i = []
        self._content_changes_i = []

    def set(self, path, recursively):
        """
        Open “path” that can lead to either a file or a directory. If the path
        is a directory, a recursive search can be applied using the
        “recursively” argument. After getting all the paths and saving them to
        self.paths, the contents of the read files are saved to self.contents.
        Files should be text based, otherwise the BINARY constant is appended
        to self.contents.
        The method returns a tuple with a boolean informing about the validity
        of the passed path and a list of files that couldn’t be read due to an
        OSError.
        """
        res = [True, []]
        # Needed for the os.path module to not confuse a file with a trailing
        # slash with a dir
        path = re.sub(os.sep + "+$", "", path)
        if not os.path.isfile(path) and not os.path.isdir(path):
            res[0] = False
            return res
        paths_prev_len = len(self.paths)
        self._append_path(path, recursively)
        self.paths.sort()
        failed_files = self._append_content(paths_prev_len)
        if failed_files:
            failed_paths = []
            for failed_file in reversed(failed_files):
                self.paths.pop(failed_file[0])
                failed_paths.append(failed_file[1])
            res[1] = failed_paths
        return res

    def remove(self, idxs):
        """
        Remove file paths and file contents using indices in “idxs”. Every
        index removes elements both from self.paths and self.contents.
        If the state of the object have already been modified, any attempt to
        remove a file throws a RuntimeError.
        """
        if self._path_changes_i or self._content_changes_i:
            raise RuntimeError("Not permitted when some files have already "
                               "been indexed.")
        for idx in reversed(sorted(idxs)):
            self.paths.pop(idx)
            self.contents.pop(idx)

    # TODO: allow to rename files
    def save(self):
        """
        Save changes made to self.contents. Only affected files will be
        overwritten.
        The method returns a list of files that couldn’t be overwritten due to
        an OSError.
        """
        failed_files = []
        for idx in self._content_changes_i:
            if not os.path.isfile(self.paths[idx]):
                failed_files.append(self.paths[idx])
                continue
            with open(self.paths[idx], "w") as f:
                try:
                    f.write(self.contents[idx])
                except OSError:
                    failed_files.append(self.paths[idx])
        return failed_files

    def _append_path(self, path, recursively):
        def append_if_possible(path):
            if path not in self.paths:
                self.paths.append(path)
        
        if not os.path.isdir(path):
            append_if_possible(path)
            return
        
        dirs = [path]
        while dirs:
            dir_paths = os.listdir(dirs[0])
            for dir_path in dir_paths:
                ext_path = os.path.join(dirs[0], dir_path)
                if not os.path.isdir(ext_path):
                    append_if_possible(ext_path)
                else:
                    dirs.append(ext_path)
            if not recursively:
                return
            dirs.pop(0)

    def _append_content(self, start_idx):
        failed_files = []
        for i, path in enumerate(self.paths[start_idx:]):
            with open(path, "r") as f:
                try:
                    self.contents.append(f.read())
                except OSError:
                    failed_files.append((i, path))
                except UnicodeDecodeError:
                    self.contents.append(BINARY)
        return failed_files

    def _get_data(self, data_type):
        """
        A method called from outside the class to get a reference to
        self.paths or self.contents based on the “data_type” constant (either
        FILEPATH or FILECONTENT).
        """
        if data_type == FILEPATH:
            return self.paths
        if data_type == FILECONTENT:
            return self.contents

    def _log_change(self, data_type, idx):
        """
        A method called from outside the class to store “idx“ of modified data
        element and assign it to an internal variable based on the “data_type”
        constant (either FILEPATH or FILECONTENT). The result is needed for
        the save() method.
        """
        if data_type == FILEPATH and idx not in self._path_changes_i:
            self._path_changes_i.append(idx)
        elif data_type == FILECONTENT and idx not in self._content_changes_i:
            self._content_changes_i.append(idx)


class _MatchInfo:
    """
    An internal class that stores search or replacement results in
    self.match_info. It also contains several methods that partially
    constitute the result.
    """

    def __init__(self):
        self.match_info = []
        self._data_i = []
        self._match_span_l = (-1, -1)

    # TODO: limit chars
    def _get_line(self, span, match, string):
        """
        Extract a line from “string” where the span indices “span” are located
        and insert “match” instead of the substring defined by the span. The
        “match” argument is necessary to get the correct replacement result,
        because in these cases the match string differs from the substring
        defined by the span. The returned line will not contain any EOL chars
        except those found in the match.
        As a side product, the span of the match inside the returned line is
        set as an internal class property to be used later.
        """
        def is_new_line(char):
            if (char == "\n" or
                char == "\r" or
                char == "\r\n"):
                return True
            return False
        
        prefix = ""
        postfix = ""
        x_minus = span[0] - 1
        x_plus = span[1]
        
        if x_plus > 0 and is_new_line(string[x_plus - 1]):
            x_plus -= 1
        while x_minus >= 0:
            if is_new_line(string[x_minus]):
                break
            prefix = string[x_minus] + prefix
            x_minus -= 1
        while x_plus < len(string):
            if is_new_line(string[x_plus]):
                break
            postfix += string[x_plus]
            x_plus += 1
        
        if x_minus == -1:
            a = 0 + span[0]
            b = span[1]
        else:
            a = span[0] - x_minus - 1
            b = span[1] - x_minus - 1
        self._match_span_l = (a, b)
        
        return str(prefix + match + postfix)

    def _get_line_span(self, start_idx, match, string):
        """
        Get a number of the line inside “string” where the char index
        “start_idx” is located. “match” is used to count the line span in case
        it contains an EOL char. The returned line span is a tuple with the
        starting line included and the ending line excluded.
        """
        lines = string.splitlines(True)
        counter = 0
        line_counter = 0
        for i, line in enumerate(lines):
            counter += 1
            line_counter += len(line)
            if line_counter > start_idx:
                break
        match_lines = match.splitlines(True)
        match_counter = 0
        for match_line in match_lines:
            match_counter += 1
        if match_counter > 1:
            end_idx = counter + match_counter
            return (counter, end_idx)
        else:
            return (counter, counter + 1)

    def _log_match(self, idx, info):
        if not info:
            return
        # Prevents multiple logging of a single result
        for x in self.match_info:
            if idx == x["idx"] and info[2] == x["match_span"]:
                return
        self.match_info.append({"idx": idx,
                                "path": self.files.paths[idx],
                                "line": info[0],
                                "line_span": info[1],
                                "match_span": info[2],
                                "match_span_l": info[3]})
        self._data_i.append(idx)


class Finder(_MatchInfo):
    """
    A class responsible for finding matches. It takes a “files” object, from
    which it gets base data, and an “options” object, from which it gets the
    settings to be passed in a re function. “prev_finder” allows to stick to
    the results from the previous Finder object by doing a new searches only
    within the range of already found files. Otherwise, all files are searched
    by this method.
    The current find results are stored in self.match_info.
    """

    def __init__(self, files, options, prev_finder=None):
        super().__init__()
        self.files = files
        self.options = options
        if not prev_finder or not prev_finder._data_i:
            self._data_i = list(range(0, len(self.files.paths)))
        elif prev_finder:
            self._data_i.extend(prev_finder._data_i)
        self.logical_op = None
        self.pattern = None

    def find(self, logical_op, pattern):
        """
        If “logical_op” is the IF constant, find files that match “pattern”.
        If it is the IFNOT constant, find every file that doesn’t match the
        specified pattern. If no match was found, the method returns None. If
        the pattern is an empty string, it also returns None.
        After calling the method repeatedly, a new search operation is done in
        the subset of already found files. For entirely new search, create a
        new Finder object.
        """
        if not pattern:
            return
        self.logical_op = logical_op
        self.pattern = pattern
        _data_i = list(self._data_i)
        self.match_info = []
        self._data_i = []
        for idx in _data_i:
            data = self.files._get_data(self.options.data_type)
            self._find_by_op(logical_op, data, idx)

    def _find_by_op(self, logical_op, data, idx):
        if logical_op == IF:
            res = self._find(data[idx])
            for x in res:
                self._log_match(idx, x)
        if logical_op == IFNOT:
            res = self._find_not(data[idx])
            self._log_match(idx, res)

    def _find(self, string):
        if type(string) is not str:
            return [None]
        res = []
        match_objs = re.finditer(self.pattern,
                                 string,
                                 self.options.get_flags())
        counter = 0
        for i, match_obj in enumerate(match_objs):
            # Could be used to eliminate empty strings
            # if not match_obj.group(0):
            #    continue
            line = self._get_line(match_obj.span(),
                                  match_obj.group(0),
                                  string)
            line_span = self._get_line_span(match_obj.span()[0],
                                            match_obj.group(0),
                                            string)
            res.append((line,
                        line_span,
                        match_obj.span(),
                        self._match_span_l))
            counter += 1
        if counter > 0:
            return res
        else:
            return [None]

    def _find_not(self, string):
        """
        Return None if the result obtained by the _find() method is True,
        otherwise return specific null values as the find result.
        """
        if not self._find(string)[0]:
            return (NULL, (-1, -1), (-1, -1), (-1, -1))
        else:
            return None


class Replacer(_MatchInfo):
    """
    A class responsible for making changes to matching files found by the
    “finder” object. For this reason, it also uses other objects stored in the
    Finder object.
    The current replacement results are stored in self.match_info.
    """

    def __init__(self, finder):
        super().__init__()
        self.finder = finder
        self.files = finder.files
        self.options = finder.options
        self.repl = None
        
        # For now, it should only be changed for testing purposes
        self._allow_file_path = False
        # Locking a Replacer object would not be necessary if the state of the
        # Files object was stored before calling the apply_sub() method.
        # Perhaps other changes made to this or Finder class, such as updating
        # attributes of existing objects, could work. So far, however, without
        # raising an error when calling a public method after the apply_sub()
        # method, incorrect results occur.
        self._locked = False

    def replace(self, repl):
        """
        Demonstrate possible file changes using the Finder object pattern and
        the replacement “repl”. Every new method call overwrites the current
        state of self.match_info.
        If there is no matching file in finder.match_info, the method returns
        None. If the current data type in the options object is set to the
        FILEPATH constant, the method returns None because changing a path is
        not implemented yet.
        If the data of the Files object have already been modified, a
        RuntimeError is raised.
        """
        if self._locked:
            raise RuntimeError("The Files object have already been modified. "
                               "Create a new Replacer object instead.")
        # TODO: allow to replace file paths
        if self.options.data_type == FILEPATH and not self._allow_file_path:
            return
        if not self.finder.match_info or self.finder.logical_op == IFNOT:
            return
        self.repl = repl
        self.match_info = []
        self._data_i = []
        self._replace_found_data((self.files.
                                  _get_data(
                                  self.options.
                                  data_type)))

    # The method doesn’t manipulate data using the re module, instead it uses
    # information stored in self.match_info (see the _replace_found_data()
    # comment for some context)
    def apply_sub(self, filter_list=[]):
        """
        Apply data changes suggested by the replace() method. Only data change
        suggestions not listed in “filter_list” are applied.
        If self.match_info is empty, the method returns None.
        After calling the method, the Replacer object became locked, which
        means that any new call to its public methods throws a RuntimeError.
        For new data manipulation, create a new Replacer object.
        """
        if self._locked:
            raise RuntimeError("The Files object have already been modified. "
                               "Create a new Replacer object instead.")
        if not self.match_info:
            return
        if len(self._data_i) == 1 or self._data_i[0] == self._data_i[1]:
            prev_file_idx = self._data_i[0]
        else:
            prev_file_idx = -1
        new_str = ""
        prev_start_idx = 0
        for i, idx in enumerate(self._data_i):
            content = self.files._get_data(self.options.data_type)[idx]
            finder_span = self.finder.match_info[i]["match_span"]
            prematch_line = content[prev_start_idx:finder_span[0]]
            replacer_span = self.match_info[i]["match_span_l"]
            if i in filter_list:
                match = content[finder_span[0]:finder_span[1]]
            else:
                match = (self.match_info
                         [i]
                         ["line"]
                         [replacer_span[0]:replacer_span[1]])
            prev_start_idx = finder_span[1]
            b = False
            new_str += prematch_line
            new_str += match
            if ((idx != prev_file_idx and
                i != len(self._data_i) - 1 and
                self._data_i[i] != self._data_i[i + 1]) or
                (i == len(self._data_i) - 1 or
                self._data_i[i] != self._data_i[i + 1])):
                b = True
            if b:
                new_str += content[prev_start_idx:]
                self.files._get_data(self.options.data_type)[idx] = new_str
                self.files._log_change(self.options.data_type, idx)
                new_str = ""
                prev_start_idx = 0
            prev_file_idx = idx
        self._locked = True

    # For the sake of filtering the results, multiple data change suggestions
    # from one file must be appended to self.match_info without them knowing
    # anything about each other. The method should also keep support for regex
    # back-references, where the replacement string could always be different.
    # As a consequence, things get somewhat complicated. Maybe storing more
    # data in memory would be helpful, but the module’s objective is not to
    # store any data that is not strictly necessary. For this reason, a rather
    # complex attempt using the Replacer and Finder match_info attribute was
    # finally held to accomplish the goals. Similarly, apply_sub() method is
    # also more complicated than it has to be if different objectives were
    # set.
    def _replace_found_data(self, data):
        is_group = False
        # TODO: check also Python alternative backreference notation
        if re.search("\\\\\d+", self.repl):
            is_group = True
        else:
            repl_to_pass = self._get_repl_str(self.finder.match_info
                                              [0]
                                              ["line"],
                                              self.finder.match_info
                                              [0]
                                              ["match_span_l"])
        
        for i, idx in enumerate(self.finder._data_i):
            if is_group:
                finder_span = self.finder.match_info[i]["match_span_l"]
                finder_line = self.finder.match_info[i]["line"]
                
                pf_prematch = None
                if (self.match_info and
                    (self.finder.match_info[i]["idx"] ==
                    self.finder.match_info[i - 1]["idx"]) and
                    (self.finder.match_info[i]["line_span"] == 
                    self.finder.match_info[i - 1]["line_span"])):
                    pr_span = (self.match_info
                               [len(self.match_info) - 1]
                               ["match_span_l"])
                    pf_span = self.finder.match_info[i - 1]["match_span_l"]
                    pr_line = (self.match_info
                               [len(self.match_info) - 1]
                               ["line"])
                    pf_line = self.finder.match_info[i - 1]["line"]
                    pf_prematch = pf_line[:pf_span[1]]
                    
                    finder_line = pr_line
                    finder_line = pr_line[pr_span[1]:]
                repl_line = re.sub(self.finder.pattern,
                                   self.repl,
                                   finder_line,
                                   flags=self.options.get_flags(),
                                   count=1)
                if pf_prematch:
                    repl_line = pf_prematch + repl_line
                    finder_line = pf_prematch + finder_line
                repl_to_pass = self._get_repl_str(finder_line,
                                                  finder_span,
                                                  repl_line)
            
            finder_span = self.finder.match_info[i]["match_span"]
            content = data[idx]
            prestr = content[:finder_span[0]]
            midstr = content[finder_span[0]:finder_span[1]]
            sufstr = content[finder_span[1]:]
            string = prestr + repl_to_pass + sufstr
            if string is not data[idx]:
                spans = self._get_match_spans(i, repl_to_pass)
                match_span = spans[0]
                match_span_l = spans[1]
                line = self._get_line(match_span, repl_to_pass, string)
                line_span = self._get_line_span(match_span[0],
                                                repl_to_pass,
                                                string)
                self._log_match(idx, (line,
                                      line_span,
                                      match_span,
                                      match_span_l))

    def _get_repl_str(self, match_line, match_span, repl_line=None):
        """
        Get a replacement string by applying the re module sub() method to
        “match_line” and then extracting it using “match_span”. “repl_line”
        could be passed to omit replacing inside the method.
        """
        if not repl_line:
            repl_line = re.sub(self.finder.pattern,
                               self.repl,
                               match_line,
                               flags=self.options.get_flags(),
                               count=1)
        prematch = match_line[:match_span[0]]
        postmatch = match_line[match_span[1]:]
        new_repl = repl_line.replace(prematch, "", 1)
        new_repl = new_repl[::-1].replace(postmatch[::-1], "", 1)
        return new_repl[::-1]

    def _get_match_spans(self, idx, repl):
        """
        Get both the span indices of the replacement string “repl” located
        inside the data element with the index “idx” and the span indices of
        the replacement string located inside the replaced line of the same
        data element.
        """
        span = self.finder.match_info[idx]["match_span"]
        span2 = self.finder.match_info[idx]["match_span_l"]
        return ((span[0], span[0] + len(repl)),
                (span2[0], span2[0] + len(repl)))
