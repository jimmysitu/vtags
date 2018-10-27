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
import OfflineLib.OfflineBaseLib as OfflineBaseLib

# set_vtags_db_path( vtags_db_path )
# this function used to set the vtags.db you want to access
# exp: set_vtags_db_path('~/my_design/rtl/vtags.db')
set_vtags_db_path          =  GLB.set_vtags_db_path


# module_inf = get_full_module_inf(module_name)
# this function used to get the module_inf:
# module_inf = {
#    'module_name'           # module name
#   ,'file_path'             # module file path
#   ,'module_line_range'     # module line range in file
#   ,'module_name_match_pos' # module define position
#   ,'subcall_instance_list' # a list of subcall_inf }
# subcall_inf = {
#    'submodule_name'           # instance module name
#   ,'instance_name'            # instance name
#   ,'subcall_line_range'       # instance code range in module file
#   ,'submodule_name_match_pos' # instance call position }   
get_full_module_inf        =  OfflineBaseLib.get_full_module_inf

# open_module_file( module_name )
# this function used to open module file with vim and jump to module define position
# exp: open_module_file( 'my_module' )
open_module_file           =  OfflineBaseLib.open_module_file

# father_module_set = get_father_module_set( module_name )
# this function used to get the futher modules of current module                   
get_father_module_set      =  OfflineBaseLib.get_father_module_set

# module_trace_list = get_module_instance_trace(module_name)
# this module used th get the module instance trace in vtags database
get_module_instance_trace  =  OfflineBaseLib.get_module_instance_trace

# file_path_of_module_list = get_module_filelist( module_name )
# this function used to get current module and all subcall module file path list
get_module_filelist        =  OfflineBaseLib.get_module_filelist

# io_inf_list = get_module_io_inf( module_name )
# this function get the current module io inf list
# io_inf = {
#   "name"        : io name
#   "io_type"     : io type(input, output, ioput)
#   "left"        : left_index
#   "right"       : right_index
#   "size"        : size
#   'line_num'    : line_num in file
#   'name_pos'    : io name position in file
#   'code_line'   : io code line
#   'signal_type' : signal type(wire, reg ...)  }            
get_module_io_inf          =  OfflineBaseLib.get_module_io_inf     

            


