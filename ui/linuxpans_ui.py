#!/usr/bin/python3
import re
import tkinter as tk
from tkinter import ttk

import pygubu
from linuxpans_ui_template import LinuxpansAppUI
from ui.linuxpans_ui_templateui import RESOURCE_PATHS, PROJECT_UI


def run_pan(process, id_num=None, val=None):
    import subprocess
    args = ["../pan", "-P", process]
    if id_num is not None:
        args += ["-i", "%s" % id_num]
    if val is not None:
        args += ["-p", "%s" % val]
    out = subprocess.check_output(args)
    return out.decode("utf-8")

def get_processes(process):
    for entry in groupwise(run_pan(process).split("\n"), 2):
        print("entry", entry)
        num_str = entry[0].split(" ", 1)[0]
        print("num_str", repr(num_str))
        if num_str.startswith("b\""):
            num_str=num_str[2:]
        assert num_str.startswith("#")
        id_num = int(num_str[1:])
        process_name = entry[0].split(" '", 1)[1][:-1]
        yield id_num, process_name

def groupwise(lines, n):
    i = 0
    entries = []
    cur = []
    while i < len(lines):
        line = lines[i]
        cur.append(line)
        i += 1
        if i % n == 0:
            entries.append(cur)
            cur = []
    return entries

class LinuxpansAppImpl(LinuxpansAppUI):
    def __init__(self, master=None):
        super().__init__(master)
        self.entryProcess: tk.Entry = self.builder.get_object(
            "entryProcess", master)
        self.frameProcesses: ttk.Frame = self.builder.get_object(
            "frameProcesses", master)
        self.processSubForms = []
        self.processBuilders = []
        self.cur_ids = []

        self.entryProcess.focus()

    def create_process_builder(self):
        builder = pygubu.Builder()
        builder.add_resource_paths(RESOURCE_PATHS)
        builder.add_from_file(PROJECT_UI)
        builder.connect_callbacks(self)
        return builder

    def update_process(self, pattern):
        self.clear_process()
        index = 0
        for id_num, process_name in get_processes(pattern):
            self.cur_ids.append(id_num)
            builder = self.create_process_builder()
            self.processBuilders.append(builder)
            custom_id = "tkProcessSubform%s" % id_num
            print("creating " + custom_id)

            cur_subform : tk.Frame = builder.get_object("tkProcessSubform", self.frameProcesses, {"name": custom_id})
            label: tk.Label = builder.get_object("labelProcess", cur_subform)
            label.config(text="#%s: %s" % (id_num, process_name))
            label.bind("<ButtonRelease>", self.label_click_cb)
            self.processSubForms.append(cur_subform)
            scroll: ttk.Scale = builder.get_object("scalePan", cur_subform)
            scroll.bind("<ButtonRelease>", self.scalepan_change_cb)

            self.update_pan_val_label(index)
            index += 1

    def clear_process(self):
        for child in self.frameProcesses.winfo_children():
            child.destroy()
        self.processSubForms = []
        self.processBuilders = []
        self.cur_ids[:] = []

    def entry_process_cb(self, event=None):
        value = self.entryProcess.get()
        print("entry_process_cb called, got value %r" % value)
        if value != "":
            self.update_process(value)
        else:
            self.clear_process()

    def get_subform_index(self, subform_widget):
        parent_name = subform_widget.winfo_parent()
        match = re.search(r'\d+$', parent_name)
        index = int(match.group())
        return index

    def label_click_cb(self, event:tk.Event=None):
        label:tk.Label = event.widget
        index = self.get_subform_index(label)
        self.update_pan_val_label(index)
        builder = self.processBuilders[index]
        scale:ttk.Scale = builder.get_object("scalePan")
        scale.set(0)
        self.update_pan_val_label(index)
        self.update_pan_from_scale(index, scale)

    def scalepan_change_cb(self, event:tk.Event=None):
        scale:ttk.Scale = event.widget
        index = self.get_subform_index(scale)
        self.update_pan_val_label(index)
        self.update_pan_from_scale(index, scale)

    def update_pan_val_label(self, index):
        # update panval label while we're at it
        builder = self.processBuilders[index]
        scale:ttk.Scale = builder.get_object("scalePan")
        val = scale.get()
        labelPanVal: tk.Label = builder.get_object("labelPanVal")
        labelPanVal.config(text="%0.01f" % val)

    def update_pan_from_scale(self, index, scale):
        id_num = self.cur_ids[index]
        val = scale.get()
        print("pan", id_num, val)
        process = self.entryProcess.get()
        run_pan(process, id_num, val)



if __name__ == "__main__":
    app = LinuxpansAppImpl()
    app.run()
