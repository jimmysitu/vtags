"""
http://www.vim.org/scripts/script.php?script_id=5494
"""
#===============================================================================
# BSD 2-Clause License

# Copyright (c) 2016, CaoJun
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#===============================================================================

import os
import sys
import re
import pickle
import inspect
import copy

# when vtags.py run, this function can return the dir path vtags.py exist.
def cur_file_dir():
     path = sys.path[0]
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)

# get the vtags.py's dir path, which is the install src path.
vtags_install_path = cur_file_dir()

#-------------------------------------------------------------------------------
# import base libary
#-------------------------------------------------------------------------------
# add install dir path to python search path, to import all the needed python module
sys.path.insert(0,vtags_install_path)
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
import Lib.CodeLib as CodeLib
import Lib.FileInfLib as FileInfLib
import InlineLib.WinLib as WinLib


#-------------------------------------------------------------------------------
# function get for user
#-------------------------------------------------------------------------------

# this function used to get module_inf for custom user
def get_full_module_inf(module_name):
    # valid when has vtags.db
    if not G['OfflineActive']:
        print('Error: no vtags.db found !')
        return {}
    # get pre module inf no subcall list    
    cur_module_inf  = FileInfLib.get_module_inf(module_name)
    if not cur_module_inf:
        print('Error: module %s not found! \n'%(module_name))
        return {}
    if cur_module_inf.setdefault('subcall_instance_list',None) == None:
        assert(FileInfLib.module_inf_add_subcall_instance_list(cur_module_inf))
    # give a copy of module_inf incase someone change it
    return copy.deepcopy(cur_module_inf)

# this function used to open module and go to some lines
def open_module_file(module_name):
    cur_module_inf  = FileInfLib.get_module_inf(module_name)
    if not cur_module_inf:
        print('Error: module %s not found! \n'%(module_name))
        return False
    file_path = cur_module_inf['file_path']
    module_name_match_pos = cur_module_inf['module_name_match_pos']
    if not os.path.isfile(file_path):
        print('Error: module file %s not exist! \n'%(file_path))
        return False
    WinLib.open_file_separately(file_path, module_name_match_pos[0])

# this function used to get current module upper module
def get_father_module_set( module_name, dir_path_set = None ):
    upper_module_set= set()
    if not dir_path_set:
        dir_path_set = get_vtags_db_dir_path_set()
    for dir_path in dir_path_set:
        if not os.path.exists(dir_path):
            continue
        exclude_patten = '--exclude-dir="vtags.db"'
        include_patten = '--include ' + (' --include '.join( ['"*.%s"'%(p) for p in G['SupportVerilogPostfix'] ] ))
        match_lines = os.popen('egrep -n -r %s %s \'(^|\W)%s(\W|$)\' %s'%(exclude_patten, include_patten, module_name, dir_path)).readlines()
        for l in match_lines:
            try:
                spl = l.split(':') #not support file name has ':'
                file_path = spl[0]
                line_num  = int(spl[1]) - 1
                line_inf  = FileInfLib.get_file_line_inf(line_num, file_path)
                submodule = line_inf['subcall_inf']['submodule_name']
                upmodule  = line_inf['module_inf']['module_name']
                if submodule == module_name:
                    upper_module_set.add(upmodule) 
            except:
                continue
    return upper_module_set

def get_module_filelist(module_name):
    def rec_gen_module_filelist(module_name, trace_file):
        cur_module_inf  = get_full_module_inf(module_name)
        if not cur_module_inf:
            print('Warning: module %s not found! \n'%(module_name))
            return
        cur_module_path = cur_module_inf['file_path']
        if (module_name, cur_module_path) in trace_file:
            return
        trace_file.add( (module_name, cur_module_path) )
        subcall_instance_list = cur_module_inf['subcall_instance_list']
        if not subcall_instance_list:
            return
        for subcall_inf in subcall_instance_list:
            submodule_name =  subcall_inf['submodule_name']
            rec_gen_module_filelist(submodule_name, trace_file)
    # if no data base return []
    if not G['OfflineActive']:
        return []
    trace_file = set()
    rec_gen_module_filelist(module_name, trace_file)

    return list( set( [ name_file[1] for name_file in trace_file ] ) )


def get_module_io_inf(module_name):
    return CodeLib.get_io_inf(module_name)
            #   "name"        : name
            # , "io_type"     : io_type
            # , "left"        : left_index
            # , "right"       : right_index
            # , "size"        : size
            # , 'line_num'    : line_num
            # , 'name_pos'    : names_pos[i]
            # , 'code_line'   : code_line
            # , 'signal_type' : signal_type 



#-------------------------------------------------------------------------------
# base function
#-------------------------------------------------------------------------------
def get_vtags_db_dir_path_set():
    # get file list
    vtags_db_refresh_inf_pkl_path = G['VTagsPath']+'/pickle/vtags_db_refresh_inf.pkl'
    vtags_db_refresh_inf = pickle_reload(vtags_db_refresh_inf_pkl_path)
    file_list = vtags_db_refresh_inf['file_list']
    dir_list  = open(file_list,'r').readlines()
    dir_list  = [re.sub('//.*','',l.strip()) for l in dir_list]
    dir_list  = [l.strip() for l in dir_list if l.strip() != '' ]
    dir_path_set = set(dir_list)
    return dir_path_set






