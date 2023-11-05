import unittest
import re
import shutil
import os
import sys
sys.path.insert(0, "../")

from bregex import regex


class TestOptions(unittest.TestCase):

    def test_get_flags(self):
        options = regex.Options()
        self.assertEqual(options.get_flags(), 0)
        options.ignore_case = True
        self.assertEqual(options.get_flags(), re.IGNORECASE)
        options.multiline = True
        self.assertEqual(options.get_flags(), re.IGNORECASE|re.MULTILINE)


class TestFiles(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.read_files = {}
        shutil.copytree("./data", "./data_tmp", dirs_exist_ok=True)
        file_paths = []
        for root, dirs, files in os.walk("./data_tmp"):
            for file_ in files:
                file_path = os.path.join(root, file_)
                if not file_.startswith("."):
                    file_paths.append(file_path)
                else:
                    os.remove(file_path)
        file_paths.sort()
        for file_path in file_paths:
            with open(file_path, "r") as f:
                self.read_files[file_path] = f.read()

    def setUp(self):
        self.files = regex.Files()
        self.files._allow_relative_path = True

    def _get_content(self, path):
        res = []
        for key in self.read_files.keys():
            if key.startswith(path):
                res.append(self.read_files[key])
        return res

    def _get_paths(self, path):
        res = []
        for key in self.read_files.keys():
            if key.startswith(path):
                res.append(key)
        return res

    def test_set_file(self):
        path = "./data_tmp/prague_16th_century_drawings/savery.txt"
        self.files.set(path, False)
        self.assertEqual(self.files.paths, self._get_paths(path))
        self.assertEqual(self.files.contents, self._get_content(path))

    def test_set_file_return_value(self):
        res = self.files.set("./data_tmp/prague_16th_century_drawings/savery.txt", False)
        self.assertEqual(res, [True, []])

    def test_set_file_recursively(self):
        path = "./data_tmp/prague_16th_century_drawings/savery.txt"
        self.files.set(path, True)
        self.assertEqual(self.files.paths, self._get_paths(path))
        self.assertEqual(self.files.contents, self._get_content(path))

    def test_set_dir(self):
        path = "./data_tmp/prague_16th_century_drawings/lesser_town_square"
        self.files.set(path, False)
        self.assertEqual(self.files.paths, self._get_paths(path))
        self.assertEqual(self.files.contents, self._get_content(path))

    def test_set_dir_recursively(self):
        path = "./data_tmp/prague_16th_century_drawings"
        self.files.set(path, True)
        self.assertEqual(self.files.paths, self._get_paths(path))
        self.assertEqual(self.files.contents, self._get_content(path))

    def test_set_multiple_calls_different_files(self):
        path = "./data_tmp/prague_16th_century_drawings/lesser_town_square"
        path2 = "./data_tmp/prague_16th_century_drawings/prague_castle"
        self.files.set(path, False)
        self.files.set(path2, False)
        self.assertEqual(self.files.paths, self._get_paths(path) + self._get_paths(path2))
        self.assertEqual(self.files.contents, self._get_content(path) + self._get_content(path2))

    def test_set_multiple_calls_duplicated_file(self):
        path = "./data_tmp/prague_16th_century_drawings/lesser_town_square"
        path2 = "./data_tmp/prague_16th_century_drawings/lesser_town_square/savery.txt"
        self.files.set(path, False)
        self.files.set(path2, False)
        self.assertEqual(self.files.paths, self._get_paths(path2))
        self.assertEqual(self.files.contents, self._get_content(path2))

    def test_set_multiple_calls_duplicated_files(self):
        path = "./data_tmp/prague_16th_century_drawings"
        path2 = "./data_tmp/prague_16th_century_drawings/lesser_town_square"
        self.files.set(path, True)
        self.files.set(path2, False)
        self.assertEqual(self.files.paths, self._get_paths(path))
        self.assertEqual(self.files.contents, self._get_content(path))

    def test_set_trailing_slash(self):
        wrong_path = "./data_tmp/prague_16th_century_drawings/savery.txt/"
        path = "./data_tmp/prague_16th_century_drawings/savery.txt"
        self.files.set(wrong_path, False)
        self.assertEqual(self.files.paths, self._get_paths(path))
        self.assertEqual(self.files.contents, self._get_content(path))

    def test_set_invalid_path(self):
        self.files.set("./foo/bar", False)
        self.assertEqual(self.files.paths, [])
        self.assertEqual(self.files.contents, [])

    def test_set_invalid_path_return_value(self):
        res = self.files.set("./foo/bar", False)
        self.assertEqual(res, [False, []])

    def test_set_forbid_relative_path(self):
        self.files._allow_relative_path = False
        self.files.set("./foo/bar", False)
        self.assertEqual(self.files.paths, [])
        self.assertEqual(self.files.contents, [])

    def test_set_forbid_relative_path_return_value(self):
        self.files._allow_relative_path = False
        res = self.files.set("./foo/bar", False)
        self.assertEqual(res, [False, []])

    def test_remove_files(self):
        path = "./data_tmp/prague_16th_century_drawings/prague_castle"
        self.files.set(path, False)
        self.files.remove([0, 1])
        self.assertEqual(self.files.paths, self._get_paths(path)[2:])
        self.assertEqual(self.files.contents, self._get_content(path)[2:])

    def test_remove_files_no_order(self):
        path = "./data_tmp/prague_16th_century_drawings/prague_castle"
        self.files.set(path, False)
        self.files.remove([2, 0])
        self.assertEqual(self.files.paths, [self._get_paths(path)[1]])
        self.assertEqual(self.files.contents, [self._get_content(path)[1]])

    def test_remove_files_after_sub(self):
        self.files.set("./data_tmp/prague_16th_century_drawings/savery.txt", False)
        options = regex.Options()
        finder = regex.Finder(self.files, options)
        replacer = regex.Replacer(finder)
        finder.find(regex.IF, "Prague")
        replacer.replace("Praha")
        replacer.apply_sub()
        with self.assertRaises(RuntimeError):
            self.files.remove([0])

    def test_save(self):
        old_path = "./data_tmp/prague_16th_century_drawings/savery.txt"
        path = "./data_tmp/test_save/foo.txt"
        os.mkdir(os.path.dirname(path))
        shutil.copy(old_path, path)
        self.files.set(path, False)
        self.files.contents = ["foo bar"]
        options = regex.Options()
        finder = regex.Finder(self.files, options)
        replacer = regex.Replacer(finder)
        finder.find(regex.IF, "foo")
        replacer.replace("baz")
        replacer.apply_sub()
        self.files.save()
        with open(path, "r") as f:
            content = f.read()
        self.assertEqual(content, "baz bar")

    @classmethod
    def tearDownClass(self):
        shutil.rmtree("./data_tmp")


class TestFinder(unittest.TestCase):

    def setUp(self):
        self.options = regex.Options()
        self.files = regex.Files()

    def test_find_path(self):
        self.options.data_type = regex.FILEPATH
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "path")
        self.assertEqual([x["line"] for x in finder.match_info], ["path1", "path2", "path3"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1", "path2", "path3"])

    def test_find_file(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo", "foo bar"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1", "path3"])

    def test_find_file_if_not_operator(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IFNOT, "bar")
        self.assertEqual([x["line"] for x in finder.match_info], [regex.NULL])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1"])

    def test_find_file_one_file_multiple_results(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo bar foo"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo bar foo", "foo bar foo"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1", "path1"])

    def test_find_file_multiple_calls(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        finder.find(regex.IF, "bar")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo bar"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path3"])

    def test_find_file_multiple_calls_if_not_operator(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IFNOT, "foo")
        finder.find(regex.IFNOT, "bar")
        self.assertEqual(finder.match_info, [])

    def test_find_file_multiple_calls_if_operator_after_if_not_operator(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IFNOT, "foo")
        finder.find(regex.IF, "bar")
        self.assertEqual([x["line"] for x in finder.match_info], ["bar"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path2"])

    def test_find_file_multiple_calls_if_operator_before_if_not_operator(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        finder.find(regex.IFNOT, "bar")
        self.assertEqual([x["line"] for x in finder.match_info], [regex.NULL])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1"])

    def test_find_file_multiple_calls_one_file_multiple_results(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo bar foo"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "bar")
        finder.find(regex.IF, "foo")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo bar foo", "foo bar foo"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1", "path1"])

    def test_find_file_multiple_objects(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        finder2 = regex.Finder(self.files, self.options, finder)
        finder2.find(regex.IF, "bar")
        self.assertEqual([x["line"] for x in finder2.match_info], ["foo bar"])
        self.assertEqual([x["path"] for x in finder2.match_info], ["path3"])

    def test_find_file_multiple_objects_if_not_operator(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar baz"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IFNOT, "baz")
        finder2 = regex.Finder(self.files, self.options, finder)
        finder2.find(regex.IFNOT, "bar")
        self.assertEqual([x["line"] for x in finder2.match_info], [regex.NULL])
        self.assertEqual([x["path"] for x in finder2.match_info], ["path1"])

    def test_find_file_multiple_objects_multiple_calls(self):
        self.files.paths = ["path1", "path2", "path3", "path4"]
        self.files.contents = ["foobar", "bar", "foo bar", "foo baz"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        finder2 = regex.Finder(self.files, self.options, finder)
        finder2.find(regex.IF, "bar")
        finder2.find(regex.IF, "foobar")
        self.assertEqual([x["line"] for x in finder2.match_info], ["foobar"])
        self.assertEqual([x["path"] for x in finder2.match_info], ["path1"])

    def test_find_no_binary_file(self):
        self.files.paths = ["path1", "path2"]
        self.files.contents = [regex.BINARY, "foo"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path2"])

    def test_find_file_invalid_pattern(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "baz")
        self.assertEqual(finder.match_info, [])

    def test_find_file_invalid_pattern_after_valid_pattern(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "bar")
        finder.find(regex.IF, "baz")
        self.assertEqual(finder.match_info, [])

    def test_find_file_valid_pattern_after_invalid_pattern(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        finder.find(regex.IF, "baz")
        finder.find(regex.IF, "bar")
        self.assertEqual(finder.match_info, [])

    def test_find_file_empty_input(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "")
        self.assertEqual(finder.match_info, [])

    def test_find_file_special_chars(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo 123 bar", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "^\w+ (.*) \w+$")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo 123 bar"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1"])

    def test_find_file_string_with_EOL_char(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo\nbar", "bar\nfoo\nbar", "bar\nfoo\n"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo", "foo", "foo"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1", "path2", "path3"])

    def test_find_file_match_with_EOL_char(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo\nbar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "o\nb")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo\nbar"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1"])

    def test_find_file_match_starts_with_EOL_char(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo\nbar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "\nbar")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo\nbar"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1"])

    def test_find_file_match_with_trailing_EOL_char(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo\nbar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "\n")
        self.assertEqual([x["line"] for x in finder.match_info], ["foo\n"])
        self.assertEqual([x["path"] for x in finder.match_info], ["path1"])

    def test_find_line_span(self):
        self.files.paths = ["path1", "path2"]
        self.files.contents = ["bar", "foo\nbar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "bar")
        self.assertEqual([x["line_span"] for x in finder.match_info], [(1, 2), (2, 3)])

    def test_find_line_span_one_file_multiple_results(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo bar\nbaz\nfoo"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        self.assertEqual([x["line_span"] for x in finder.match_info], [(1, 2), (3, 4)])

    def test_find_line_span_string_with_different_EOL_chars(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo\nbar\nbaz", "foo\r\nbar\r\nbaz", "foo\rbar\r\nbaz"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "baz")
        self.assertEqual([x["line_span"] for x in finder.match_info], [(3, 4), (3, 4), (3, 4)])

    def test_find_line_span_input_with_EOL_char(self):
        self.files.paths = ["path1"]
        self.files.contents = ["f\no\no\nb\na\nrfoo"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "\nb\na\nr")
        self.assertEqual([x["line_span"] for x in finder.match_info], [(3, 7)])

    def test_find_line_span_if_not_operator(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IFNOT, "bar")
        self.assertEqual([x["line_span"] for x in finder.match_info], [(-1, -1)])

    def test_find_match_span(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar foo bar", "bar\nfoo\nbar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        self.assertEqual([x["match_span"] for x in finder.match_info], [(0, 3 ), (4, 7), (4, 7)])

    def test_find_match_span_one_file_multiple_results(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo bar foo"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IF, "foo")
        self.assertEqual([x["match_span"] for x in finder.match_info], [(0, 3 ), (8, 11)])

    def test_find_match_span_if_not_operator(self):
        self.files.paths = ["path1", "path2"]
        self.files.contents = ["foo", "bar"]
        finder = regex.Finder(self.files, self.options)
        finder.find(regex.IFNOT, "foo")
        self.assertEqual([x["match_span"] for x in finder.match_info], [(-1, -1)])


class TestReplacer(unittest.TestCase):

    def setUp(self):
        self.options = regex.Options()
        self.files = regex.Files()

    def test_replace_path(self):
        self.options.data_type = regex.FILEPATH
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar foo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "2")
        self.replacer = regex.Replacer(self.finder)
        self.replacer._allow_file_path = True
        self.replacer.replace("baz")
        self.assertEqual([x["line"] for x in self.replacer.match_info], ["pathbaz"])
        self.assertEqual([x["path"] for x in self.replacer.match_info], ["path2"])

    def test_replace_file(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar foo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.assertEqual([x["line"] for x in self.replacer.match_info], ["baz", "bar baz bar"])
        self.assertEqual([x["path"] for x in self.replacer.match_info], ["path1", "path3"])

    def test_replace_file_if_not_operator(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar foo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IFNOT, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.assertEqual(self.replacer.match_info, [])

    def test_replace_file_multiple_calls(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar foo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.replacer.replace("bar")
        self.assertEqual([x["line"] for x in self.replacer.match_info], ["bar", "bar bar bar"])

    def test_replace_line_empty_finder(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar foo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "baz")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.assertEqual(self.replacer.match_info, [])

    def test_replace_line_span(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar\nfoo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.assertEqual([x["line_span"] for x in self.replacer.match_info], [(1, 2), (2, 3)])

    def test_replace_match_span(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar foo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.assertEqual([x["match_span"] for x in self.replacer.match_info], [(0, 3), (4, 7)])

    def test_apply_sub(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "bar foo bar"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.replacer.apply_sub()
        self.assertEqual(self.files.contents, ["baz", "bar", "bar baz bar"])

    def test_apply_sub_one_file_multiple_replacements(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo bar foo"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.replacer.apply_sub()
        self.assertEqual(self.files.contents, ["baz bar baz"])

    def test_apply_sub_one_file_multiple_replacements_before_single_replacement(self):
        self.files.paths = ["path1", "path2"]
        self.files.contents = ["foo bar foo", "foo"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.replacer.apply_sub()
        self.assertEqual(self.files.contents, ["baz bar baz", "baz"])

    def test_apply_sub_one_file_multiple_replacements_after_single_replacement(self):
        self.files.paths = ["path1", "path2"]
        self.files.contents = ["foo", "foo bar foo"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.replacer.apply_sub()
        self.assertEqual(self.files.contents, ["baz", "baz bar baz"])

    def test_apply_sub_multiple_calls(self):
        self.files.paths = ["path1", "path2"]
        self.files.contents = ["foo", "foo bar foo"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("ba")
        self.replacer.apply_sub()
        with self.assertRaises(RuntimeError):
            self.replacer.replace("z")
        with self.assertRaises(RuntimeError):
            self.replacer.apply_sub()

    def test_apply_sub_using_group(self):
        self.files.paths = ["path1", "path2"]
        self.files.contents = ["foo", "foo bar foo"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "(foo)")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("x\\1x")
        self.replacer.apply_sub()
        self.assertEqual(self.files.contents, ["xfoox", "xfoox bar xfoox"])

    def test_apply_sub_using_group_different_replacements(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo bar-baz foo-bar baz"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "(\w+)-(\w+)")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("\\1 \\2")
        self.replacer.apply_sub()
        self.assertEqual(self.files.contents, ["foo bar baz foo bar baz"])

    def test_apply_sub_using_group_different_replacements_with_EOL_char(self):
        self.files.paths = ["path1"]
        self.files.contents = ["foo bar-baz \nfoo-bar baz foo-bar baz"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "(\w+)-(\w+)")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("\\1 \\2")
        self.replacer.apply_sub()
        self.assertEqual(self.files.contents, ["foo bar baz \nfoo bar baz foo bar baz"])

    def test_apply_sub_using_filter(self):
        self.files.paths = ["path1", "path2", "path3"]
        self.files.contents = ["foo", "bar", "foo bar foo"]
        self.finder = regex.Finder(self.files, self.options)
        self.finder.find(regex.IF, "foo")
        self.replacer = regex.Replacer(self.finder)
        self.replacer.replace("baz")
        self.replacer.apply_sub([0, 2])
        self.assertEqual(self.files.contents, ["foo", "bar", "baz bar foo"])


if __name__ == "__main__":
    unittest.main()
