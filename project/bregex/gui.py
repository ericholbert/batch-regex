from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import re
import platform
import sys
import regex


root = Tk()

ignore_case_chb_var = BooleanVar()
multiline_chb_var = BooleanVar()
dot_all_chb_var = BooleanVar()

find_in_rbs_var = IntVar(value=regex.FILECONTENT)
booleans_rbs_var = IntVar(value=regex.IF)

find_e_var = StringVar()
replace_e_var = StringVar()

finder_out_widgets = []
replacer_out_widgets = []

files_g = None
finder_g = None
prev_finder_g = None
replacer_g = None

unselected_files = []

file_count = IntVar()

chb_img_yes = PhotoImage(file="res/chb_yes.png")
chb_img_no = PhotoImage(file="res/chb_no.png")

if platform.system() == "Darwin":
    ctrl_key = "Command"
    ctrl_key_l = "Command"
else:
    ctrl_key = "Ctrl"
    ctrl_key_l = "Control"


# TODO: allow to update paths after applying the form
def open_file():
    def add():
        t.insert("", END, values=(ev.get(), ev2.get(), chbv.get()))
    
    def remove():
        selected_items = t.selection()
        for selected_item in selected_items:
            t.delete(selected_item)
    
    def apply():
        global files_g
        files_g = regex.Files()
        for x in t.get_children():
            vals = t.item(x)["values"]
            if vals[2] == "True":
                vals[2] = True
            else:
                vals[2] = False
            res = files_g.set(vals[0], vals[2])
            if vals[1]:
                options = regex.Options(regex.FILEPATH)
                finder = regex.Finder(files_g, options)
                finder.find(regex.IFNOT, vals[1])
                files_g.remove(finder._data_i)
            if not res[0]:
                messagebox.showerror(title="Error", message=f"Path '{vals[0]}' could not be found!")
            # TODO: log file paths somewhere
            if res[1]:
                messagebox.showerror(title="Error", message=f"Some files ({len(res[1])}) in path '{vals[0]}' could not be read!")
        file_count.set(len(files_g.paths))
        reset()
        dialog.destroy()
    
    ev = StringVar()
    ev2 = StringVar()
    chbv = BooleanVar()
    
    dialog = Toplevel(root)
    f = ttk.Frame(dialog, padding=(8, 4, 8, 4))
    f2 = ttk.Frame(dialog)
    l = ttk.Label(f, text="Path:")
    e = ttk.Entry(f, textvariable=ev)
    b = ttk.Button(f, text="Add", command=lambda: add())
    l2 = ttk.Label(f, text="Include:")
    e2 = ttk.Entry(f, textvariable=ev2)
    chb = ttk.Checkbutton(f, text="Recursively", variable=chbv, onvalue=True, offvalue=False)
    b2 = ttk.Button(f, text="Remove", command=lambda: remove())
    t = ttk.Treeview(f2)
    b3 = ttk.Button(f2, text="Apply", command=lambda: apply())
    
    dialog.title("Open")
    
    dialog.bind(f"<Return>", lambda x: apply())
    dialog.bind(f"<Escape>", lambda x: dialog.destroy())
    
    columns = ["path", "include", "recursively"]
    t["columns"] = columns
    t["show"] = "headings"
    t.heading("path", text="Path")
    t.column("path", width=200)
    t.heading("include", text="Include")
    t.column("include", width=200)
    t.heading("recursively", text="Recursively")
    t.column("recursively", width=100)
    
    f.grid(column=0, row=0, sticky="we")
    f2.grid(column=0, row=1, sticky="nswe")
    l.grid(column=0, row=0, sticky="e", padx=(0, 4), pady=(0, 4))
    e.grid(column=1, row=0, columnspan=2, sticky="we", padx=(0, 4), pady=(0, 4))
    b.grid(column=3, row=0, sticky="w", pady=(0, 4))
    l2.grid(column=0, row=1, sticky="e", padx=(0, 4))
    e2.grid(column=1, row=1, sticky="we", padx=(0, 4))
    chb.grid(column=2, row=1, padx=(0, 4))
    b2.grid(column=3, row=1, sticky="w")
    t.grid(column=0, row=0, sticky="nswe", pady=(0, 4))
    b3.grid(column=0, row=1, padx=8, pady=(0, 4))
    
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(1, weight=1)
    f.columnconfigure(1, weight=1)
    f.rowconfigure(0, weight=1)
    f2.columnconfigure(0, weight=1)
    f2.rowconfigure(0, weight=1)

def save():
    if not replacer_g or not files_g:
        return
    replacer_g.apply_sub([x[1] for x in unselected_files if not x[0].get()])
    reset()
    res = files_g.save()
    # TODO: log file paths somewhere
    if res:
        messagebox.showerror(title="Error", message=f"Some files ({len(res)}) could not be saved!")

def find(create=True):
    if not files_g:
        return
    global finder_g
    global prev_finder_g
    if create:
        options = regex.Options(find_in_rbs_var.get(), ignore_case_chb_var.get(), multiline_chb_var.get(), dot_all_chb_var.get())
        finder_g = regex.Finder(files_g, options, prev_finder_g)
        finder_g.find(booleans_rbs_var.get(), find_e_var.get())
        if finder_g.match_info:
            prev_finder_g = finder_g
    replacer_out_t.configure(state=NORMAL)
    replacer_out_t.delete("1.0", END)
    replacer_out_t.configure(state=DISABLED)
    _print_info(finder_g.match_info, finder_out_t, "yellow", "black")

def replace(create=True):
    if not finder_g:
        return
    global replacer_g
    if create:
        replacer_g = regex.Replacer(finder_g)
        replacer_g.replace(replace_e_var.get())
    global unselected_files
    unselected_files = []
    _print_info(replacer_g.match_info, replacer_out_t, "red", "white", True)

def reset():
    global finder_g
    global prev_finder_g
    global replacer_g
    finder_g = None
    prev_finder_g = None
    finder_out_t.configure(state=NORMAL)
    finder_out_t.delete("1.0", END)
    finder_out_t.configure(state=DISABLED)
    find_e.delete(0, END)
    replacer_g = None
    replacer_out_t.configure(state=NORMAL)
    replacer_out_t.delete("1.0", END)
    replacer_out_t.configure(state=DISABLED)
    replace_e.delete(0, END)

def _print_info(info, text_w, bg_color, fg_color, add_chbs=False):
    text_w.configure(state=NORMAL)
    text_w.delete("1.0", END)
    text_w.tag_config("match", background=bg_color, foreground=fg_color)
    
    file_counter = 1
    prev_idx = -1
    prev_line_num = None
    for i, x in enumerate(info):
        # file counter + file path
        if x["idx"] != prev_idx:
            if i != 0:
                text_w.insert(END, "\n\n")
            text_w.insert(END, "#")
            text_w.insert(END, f"{file_counter}: ")
            text_w.insert(END, x["path"])
            text_w.insert(END, "\n")
        else:
            if i != 0:
                text_w.insert(END, "\n")
        
        # line num
        if x["line_span"][1] - x["line_span"][0] == 1:
            line_num = f"{x['line_span'][0]}"
        elif x["line_span"][0] > 0 and x["line_span"][1] > 0:
            line_num = f"{x['line_span'][0]}–{x['line_span'][1] - 1}"
        else:
            line_num = str(0)
        if line_num != prev_line_num or x["idx"] != prev_idx:
            line_num_txt = f" #{line_num}: "
        else:
            line_num_txt = f"   " + " " * len(line_num) + " "
        text_w.insert(END, line_num_txt)
        
        # checkbuttons
        if add_chbs:
            chbv = BooleanVar()
            chb = Checkbutton(text_w, variable=chbv, onvalue=True, offvalue=False, borderwidth=0, indicatoron=False, image=chb_img_no, selectimage=chb_img_yes, cursor="arrow", takefocus=0)
            chb.select()
            text_w.window_create(END, window=chb)
            text_w.insert(END, " ")
            unselected_files.append((chbv, i))
        
        # line
        if x["line"] == regex.NULL:
            text_w.insert(END, "{No match}")
        else:
            prematch = x["line"][:x["match_span_l"][0]]
            match = x["line"][x["match_span_l"][0]:x["match_span_l"][1]]
            postmatch = x["line"][x["match_span_l"][1]:]
            match = re.sub("\r\n|\n|\r", "{EOL}", match)
            text_w.insert(END, prematch)
            text_w.insert(END, match, "match")
            text_w.insert(END, postmatch)
        
        if x["idx"] != prev_idx:
            file_counter += 1
        prev_idx = x["idx"]
        prev_line_num = line_num
    
    text_w.configure(state=DISABLED)


root.title("Batch RegEx")
root.option_add("*tearOff", FALSE)

root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

root.bind(f"<{ctrl_key_l}-n>", lambda x: reset())
root.bind(f"<{ctrl_key_l}-o>", lambda x: open_file())
root.bind(f"<{ctrl_key_l}-s>", lambda x: save())
root.bind(f"<{ctrl_key_l}-f>", lambda x: find_e.focus())
root.bind(f"<{ctrl_key_l}-r>", lambda x: replace_e.focus())


# MENUBAR
menubar = Menu(root)
file_m = Menu(menubar)
edit_m = Menu(menubar)
options_m = Menu(menubar)

menubar.add_cascade(menu=file_m, label="File")
file_m.add_command(label="New finder", command=lambda: reset())
file_m.add_separator()
file_m.add_command(label="Open...", command=lambda: open_file())
file_m.add_command(label="Save", command=lambda: save())

menubar.add_cascade(menu=edit_m, label="Edit")
edit_m.add_command(label="Find", command=lambda: find())
edit_m.add_command(label="Replace", command=lambda: replace())

menubar.add_cascade(menu=options_m, label="Options")
options_m.add_checkbutton(label="Ignore case", variable=ignore_case_chb_var, onvalue=True, offvalue=False)
options_m.add_checkbutton(label="Multiline", variable=multiline_chb_var, onvalue=True, offvalue=False)
options_m.add_checkbutton(label="Dot all", variable=dot_all_chb_var, onvalue=True, offvalue=False)
options_m.add_separator()
options_m.add_radiobutton(label="Find in file content", variable=find_in_rbs_var, value=regex.FILECONTENT)
options_m.add_radiobutton(label="Find in file path", variable=find_in_rbs_var, value=regex.FILEPATH)
options_m.add_separator()
options_m.add_radiobutton(label="Find if matches", variable=booleans_rbs_var, value=regex.IF)
options_m.add_radiobutton(label="Find if not matches", variable=booleans_rbs_var, value=regex.IFNOT)

file_m.entryconfigure("New finder", accelerator=f"{ctrl_key}+N")
file_m.entryconfigure("Open...", accelerator=f"{ctrl_key}+O")
file_m.entryconfigure("Save", accelerator=f"{ctrl_key}+S")
edit_m.entryconfigure("Find", accelerator=f"{ctrl_key}+F")
edit_m.entryconfigure("Replace", accelerator=f"{ctrl_key}+R")

root["menu"] = menubar


# FINDER FRAME
finder_f = ttk.Frame(root, padding=(8, 8, 8, 4))
finder_out_t = Text(finder_f, width=40, highlightthickness=0, wrap=NONE, state=DISABLED)
finder_scr_h = ttk.Scrollbar(finder_f, orient=HORIZONTAL, command=finder_out_t.xview)
finder_scr_v = ttk.Scrollbar(finder_f, orient=VERTICAL, command=finder_out_t.yview)
find_e = ttk.Entry(finder_f, textvariable=find_e_var)
find_b = ttk.Button(finder_f, text="Find", command=lambda: find())

finder_out_t["xscrollcommand"] = finder_scr_h.set
finder_out_t["yscrollcommand"] = finder_scr_v.set

finder_f.grid(column=0, row=0, sticky="nswe")
finder_out_t.grid(column=0, row=0, columnspan=2, sticky="nswe")
finder_scr_h.grid(column=0, row=1, columnspan=2, sticky="we")
find_e.grid(column=0, row=2, sticky="we", pady=(4, 0))
find_b.grid(column=1, row=2, sticky="w", padx=(4, 0), pady=(4, 0))
finder_scr_v.grid(column=2, row=0, rowspan=2, sticky="ns")

finder_f.columnconfigure(0, weight=2)
finder_f.rowconfigure(0, weight=1)

find_e.bind("<Return>", lambda x: find())


# REPLACER FRAME
replacer_f = ttk.Frame(root, padding=(0, 8, 8, 4))
replacer_out_t = Text(replacer_f, width=40, highlightthickness=0, wrap=NONE, state=DISABLED)
replacer_scr_h = ttk.Scrollbar(replacer_f, orient=HORIZONTAL, command=replacer_out_t.xview)
replacer_scr_v = ttk.Scrollbar(replacer_f, orient=VERTICAL, command=replacer_out_t.yview)
replace_e = ttk.Entry(replacer_f, textvariable=replace_e_var)
replace_b = ttk.Button(replacer_f, text="Replace", command=lambda: replace())

replacer_out_t["xscrollcommand"] = replacer_scr_h.set
replacer_out_t["yscrollcommand"] = replacer_scr_v.set

replacer_f.grid(column=1, row=0, sticky="nswe")
replacer_out_t.grid(column=0, row=0, columnspan=2, sticky="nswe")
replacer_scr_h.grid(column=0, row=1, columnspan=2, sticky="we")
replace_e.grid(column=0, row=2, sticky="we", pady=(4, 0))
replace_b.grid(column=1, row=2, sticky="w", padx=(4, 0), pady=(4, 0))
replacer_scr_v.grid(column=2, row=0, rowspan=2, sticky="ns")

replacer_f.columnconfigure(0, weight=2)
replacer_f.rowconfigure(0, weight=1)

replace_e.bind("<Return>", lambda x: replace())


# OPTIONS FRAME
options_f = ttk.Frame(root, padding=(8, 4, 8, 4))
ignore_case_chb = ttk.Checkbutton(options_f, text="Ignore case", variable=ignore_case_chb_var, onvalue=True, offvalue=False)
multiline_chb = ttk.Checkbutton(options_f, text="Multiline", variable=multiline_chb_var, onvalue=True, offvalue=False)
dot_all_chb = ttk.Checkbutton(options_f, text="Dot all", variable=dot_all_chb_var, onvalue=True, offvalue=False)
find_in_s = ttk.Separator(options_f, orient=VERTICAL)
file_rb = ttk.Radiobutton(options_f, text="File", variable=find_in_rbs_var, value=regex.FILECONTENT)
path_rb = ttk.Radiobutton(options_f, text="Path", variable=find_in_rbs_var, value=regex.FILEPATH)
booleans_s = ttk.Separator(options_f, orient=VERTICAL)
if_rb = ttk.Radiobutton(options_f, text="If", variable=booleans_rbs_var, value=regex.IF)
if_not_rb = ttk.Radiobutton(options_f, text="If not", variable=booleans_rbs_var, value=regex.IFNOT)
info_s = ttk.Separator(options_f, orient=VERTICAL)
info_l_str = ttk.Label(options_f, text="Open files:")
info_l_num = ttk.Label(options_f, textvariable=file_count)

options_f.grid(column=0, row=1, columnspan=2, sticky="we")
ignore_case_chb.grid(column=0, row=0, padx=(0, 4))
multiline_chb.grid(column=1, row=0, padx=(0, 4))
dot_all_chb.grid(column=2, row=0, padx=(0, 8))
find_in_s.grid(column=3, row=0, sticky="ns", padx=(0, 8))
file_rb.grid(column=4, row=0, padx=(0, 4))
path_rb.grid(column=5, row=0, padx=(0, 8))
booleans_s.grid(column=6, row=0, sticky="ns", padx=(0, 8))
if_rb.grid(column=7, row=0, padx=(0, 4))
if_not_rb.grid(column=8, row=0, padx=(0, 8))
info_s.grid(column=9, row=0, sticky="ns", padx=(0, 8))
info_l_str.grid(column=10, row=0, sticky="e")
info_l_num.grid(column=11, row=0, sticky="e")

options_f.columnconfigure(10, weight=1)


root.mainloop()
