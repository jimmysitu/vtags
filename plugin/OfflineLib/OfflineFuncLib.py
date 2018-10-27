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


# all function inf
custom_function_inf = {}

# offline_func_help
def offline_func_help(Print = False):
    help_str_list = []
    help_str_list.append('supported offline functions: ')
    help_str_list += show_func_help()
    help_str_list.append('offline call exp: ')
    help_str_list.append('    "vtags -func find topo " # used to find all function which name has string "topo" ')
    help_str_list.append('    "vtags -func \'print_module_io( my_cpu )\'" # used to print module my_cpu\'s io ! ' )
    help_str_list.append('    "vtags -func -db ~/design/vtags_db \'print_module_io( my_cpu )\'" # used specified vtags.db to get io' )
    if Print: 
        for l in help_str_list: print(l)
    return help_str_list

# used for vtags to call functions
def function_run( parm_list ):
    if parm_list == []:
        MountPrintLines(offline_func_help(), label = 'Offline Function Help', Print = True)
        return True
    if parm_list[0] == 'find':
        MountPrintLines(show_func_help( ''.join(parm_list[1:2])), label = 'Func Find Result', Print = True)
        return
    if parm_list[0] == '-db':
        db_path = ''.join(parm_list[1:2])
        if os.path.isdir(db_path):
            GLB.set_vtags_db_path(db_path)
            parm_list = parm_list[2:]
        else:
            print('Error: -db must follow a valid vtags_db dir path !')
            return False
    call_string = ' '.join(parm_list)
    function_name, parm_list = decode_call_string(call_string)
    if not function_name:
        return False
    if check_call_func_valid(function_name, parm_list):
        return real_call_custom_function(function_name, parm_list)
    return False


# used for register a function to all function
def register_function( function_class, description = '' ):
    if not (inspect.isfunction(function_class) and type(description) == str):
        print('Error: unsupport parameters for "register_function(function_class, description_string)"')
        return
    function_name = function_class.__name__
    if function_name in custom_function_inf:
        func  = custom_function_inf[func_name]
        func_define = '%s(%s) : %s'(func_name, ', '.join(inspect.getargspec(func).args), func.description)
        print('func:"%s" already registered ! %s'%(function_name, func_define))
        return
    function_class.description = description
    custom_function_inf[function_name] = function_class
    return

# used to show all support function with key in name
def show_func_help(key = '', Print = False):
    func_str_list = []
    func_name_list = list(custom_function_inf)
    if key:
        assert(type(key) == str),'only support str parms!'
        func_name_list = [ fn for fn in func_name_list if fn.find(key) != -1]
    func_name_list.sort()
    for func_name in func_name_list:
        func  = custom_function_inf[func_name]
        func_define = '    %s( %s )    # %s'%(func_name, ', '.join(inspect.getargspec(func).args), func.description)
        func_str_list.append(func_define)
    if Print:
        for l in func_str_list: print(l)
    return func_str_list

# decode the input call string to function and parms
def decode_call_string(call_string):
    match_func = re.match('(?P<name>\w+)\s*\((?P<parms>.*)\)\s*$', call_string.strip())
    if not match_func:
        print('Error: %s not a valid function call format ! valid call is like "function_name( parm0, parm1, ...)".'%(call_string))
        return None, []
    function_name  = match_func.group('name')
    parm_list      = [ p.strip() for p in (match_func.group('parms')).split(',') if p.strip() ]
    return function_name, parm_list

# check input parm is valid for some function
def check_call_func_valid(function_name, parm_list):
    if function_name not in custom_function_inf:
        print('Error: func: "%s" not exist ! '%(function_name))
        return False
    func = custom_function_inf[function_name]
    arg_num = len(inspect.getargspec(func).args)
    arg_has_default = 0
    if inspect.getargspec(func).defaults:
        arg_has_default = len(inspect.getargspec(func).defaults)
    if len(parm_list) >= (arg_num - arg_has_default) and len(parm_list) <= arg_num:
        return True
    print('Error: input parameters number not match function define! input:%d, need:[%s-%s]'%(len(parm_list), arg_num - arg_has_default, arg_num))
    return False

# real call custom function
def real_call_custom_function(function_name, parm_list):
    # the max number of custom function is 10
    if len(parm_list)   == 0:
        return custom_function_inf[function_name]()
    elif len(parm_list) == 1:
        return custom_function_inf[function_name](parm_list[0])
    elif len(parm_list) == 2:
        return custom_function_inf[function_name](parm_list[0], parm_list[1])
    elif len(parm_list) == 3:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2])
    elif len(parm_list) == 4:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2], parm_list[3])
    elif len(parm_list) == 5:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2], parm_list[3], parm_list[4])
    elif len(parm_list) == 6:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2], parm_list[3], parm_list[4], parm_list[5])
    elif len(parm_list) == 7:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2], parm_list[3], parm_list[4], parm_list[5], parm_list[6])
    elif len(parm_list) == 8:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2], parm_list[3], parm_list[4], parm_list[5], parm_list[6], parm_list[7])
    elif len(parm_list) == 9:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2], parm_list[3], parm_list[4], parm_list[5], parm_list[6], parm_list[7], parm_list[8])
    elif len(parm_list) == 10:
        return custom_function_inf[function_name](parm_list[0], parm_list[1], parm_list[2], parm_list[3], parm_list[4], parm_list[5], parm_list[6], parm_list[7], parm_list[8], parm_list[9])
    else:
        print('Error: current custom func max support 10 parameters, "%d" give!'%(len(parm_list)))
    return False



#--------------------------------------------------------------------------------
# custom function
#--------------------------------------------------------------------------------
# this function print module and all submodule's filelist
def print_module_filelist(module_name):
    if not G['OfflineActive']:
        print('Error: no vtags.db found !')
        return
    filelist = OfflineBaseLib.get_module_filelist(module_name)
    filelist.sort()
    for file_path in filelist:
        print(file_path)
    print('')


# this function get input module's instance trace
# user define parameter:
#    from_module : trace from this module, if not define, default is top module
#    to_module   : trace finish to this module
def print_module_trace(to_module, from_module = None):
    full_traces = []
    FileInfLib.recursion_get_module_trace(to_module, [], full_traces)
    print_strs = []
    i_offset = 0 # used to control multi same trace case
    for i, traces in enumerate(full_traces):
        c_trace_strs = [ traces[-1]['cur_module_name'] ]
        for t in traces[::-1]:
            c_str = '%s(%s)'%(t['instance_name'], t['submodule_name'])
            if c_str not in c_trace_strs:
                c_trace_strs.append(c_str)
            else:
                i_offset -= 1
        print_strs.append( '%d : %s'%(i + i_offset, ' -> '.join(c_trace_strs) ) )
    MountPrintLines(print_strs, label = 'Module Trace', Print = True)

# this function show module's topology
def print_module_topo(module_name, depth = 0, mask = 0, space = None):
    # valid when has vtags.db
    if not G['OfflineActive']:
        print('Error: no vtags.db found !')
        return
    depth = int(depth)
    mask  = int(mask)
    if not space:
        space = '    '
    def rec_print_module_topo(module_name, instance_name, cur_depth):
        if instance_name:
            print( '%s%s(%s)'%( space*cur_depth, instance_name, module_name) )
        else:
            print( '%s%s:'%( space*cur_depth, module_name) )
        if (cur_depth + 1 > depth) and (depth != 0):
            return
        tmp_module_inf = OfflineBaseLib.get_full_module_inf(module_name)
        # for the submodule set the masked module, and instance times
        mask_module_set  = set() | G['BaseModuleInf']['BaseModules']
        instance_times_count = {}
        module_instance_pair = []
        for subcall_inf in tmp_module_inf['subcall_instance_list']:
            submodule_name = subcall_inf['submodule_name']
            instance_name  = subcall_inf['instance_name']
            module_instance_pair.append( (submodule_name, instance_name ) )
            instance_times_count.setdefault(submodule_name, 0)
            instance_times_count[submodule_name] += 1
            if instance_times_count[submodule_name] >= mask and mask != 0:
                mask_module_set.add(submodule_name)
        # sep masked and unmasked module
        unmask_pairs  = []
        masked_module = set()
        for module,instance in module_instance_pair:
            if module in mask_module_set:
                masked_module.add(module)
            else:
                unmask_pairs.append( (module,instance) )
        # first print unmask topo
        for module,instance in unmask_pairs:
            rec_print_module_topo(module, instance, cur_depth + 1)
        # then for the masked module
        if masked_module:
            print( '%s------------'%( space*(cur_depth + 1)) )
        for module in masked_module:
            print( '%s%s(%d)'%( space*(cur_depth + 1),module, instance_times_count[module]) )
    rec_print_module_topo(module_name,'',0)


# this function fomat and print module's io
def print_module_io(module_name):
    # valid when has vtags.db
    if not G['OfflineActive']:
        print('Error: no vtags.db found !')
        return
    def extend(s,n):
        assert(len(s) <= n),'%s,%d'%(s,n)
        return s + ' '*(n-len(s))
    module_io_inf_list = OfflineBaseLib.get_module_io_inf(module_name)
    if not module_io_inf_list:
        print('Error: not found %s in vtags database !'%(module_name))
        return
    # get max len
    max_io_len    = len('name')
    max_range_len = len('range')
    max_type_len  = len('type')
    for io_inf in module_io_inf_list:
        if len(io_inf['name']) > max_io_len:
            max_io_len = len(io_inf['name'])
        io_range_len = len( str(io_inf['left']).strip() + ' : ' + str(io_inf['right']).strip() )
        if io_range_len > max_range_len:
            max_range_len = io_range_len
        if len(io_inf['io_type']) > max_type_len:
            max_type_len = len(io_inf['io_type'])
    # print io
    print('module: %s io inf:'%(module_name))
    print('--%s------%s------%s--'%( '-'*max_type_len, '-'*max_io_len, '-'*max_range_len ) )
    print('| %s    | %s    | %s |'%( extend('type',max_type_len), extend('name',max_io_len), extend('range', max_range_len) ) )
    print('|-%s----|-%s----|-%s-|'%( '-'*max_type_len, '-'*max_io_len, '-'*max_range_len ) )
    for io_inf in module_io_inf_list:
        c_type  = io_inf['io_type']
        c_name  = io_inf['name']
        c_range = (str(io_inf['left']).strip() + ' : ' + str(io_inf['right']).strip()).strip().strip(':')
        print('| %s    | %s    | %s |'%( extend(c_type,max_type_len), extend(c_name,max_io_len), extend(c_range, max_range_len) ) )
    print('--%s------%s------%s--'%( '-'*max_type_len, '-'*max_io_len, '-'*max_range_len ) )


#-------------------------------------------------------------------------------
# register vtags -func function
#-------------------------------------------------------------------------------
register_function( print_module_trace, description = 'this function get input module\'s instance trace' )
register_function( print_module_filelist, description = 'this function print module and all submodule\'s filelist' )
register_function( print_module_topo, description = 'this function print module topology!' )
register_function( print_module_io, description = 'this function print module io inf!' )
register_function( OfflineBaseLib.open_module_file, description = 'this function used to open module and go to some lines' )
