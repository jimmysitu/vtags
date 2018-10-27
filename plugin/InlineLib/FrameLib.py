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

import sys
import re
try:
    import vim
except: 
    pass
import os
import re
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
from InlineLib.ViewLib import *
import Lib.FileInfLib as FileInfLib

#-------------------------------------------------------------------------------
# topo/checkpoint/basemodule line range ,in frame file
#-------------------------------------------------------------------------------
def get_frame_range_inf():
    fram_file_link = []
    if G['Frame_Inf']['Frame_Path'] in G["VimBufferLineFileLink"]:
        fram_file_link = G["VimBufferLineFileLink"][G['Frame_Inf']['Frame_Path']]
    # get topo range , default 0,0
    has_topo          = False
    has_check_point   = False
    has_base_module   = False
    topo_range        = [0, 0]
    check_point_range = [0, 0]
    base_module_range = [0, 0]
    for i,link in enumerate(fram_file_link):
        if link and (link['action_parm_dic']['Type'] == 'topo'):
            if not has_topo:
                topo_range[0] = i
                has_topo      = True
            topo_range[1] = i
        if link and (link['action_parm_dic']['Type'] == 'check_point'):
            if not has_check_point:
                check_point_range[0] = i
                has_check_point      = True
            check_point_range[1] = i
        if link and (link['action_parm_dic']['Type'] == 'base_module'):
            if not has_base_module:
                base_module_range[0] = i
                has_base_module      = True
            base_module_range[1] = i
    # if no topo ,next topo start at [0,0]
    if not has_topo:
        topo_range = [0, 0]
    # check point initial start at topo end + 2 
    if not has_check_point:
        check_point_range[0] = topo_range[1] + 2
        check_point_range[1] = topo_range[1] + 2
    # base module initial at check point end + 2
    if not has_base_module:
        base_module_range[0] = check_point_range[1] + 2
        base_module_range[1] = check_point_range[1] + 2
    return { 'topo_range'        : tuple(topo_range)
            ,'check_point_range' : tuple(check_point_range)
            ,'base_module_range' : tuple(base_module_range) 
            ,'has_topo'          : has_topo
            ,'has_check_point'   : has_check_point
            ,'has_base_module'   : has_base_module }


#-------------------------------------------------------------------------------
# topo relate function
#-------------------------------------------------------------------------------
# for a module's submodule, sep function module and base module
def get_sub_func_base_module(module_name):
    func_instance_name_submodule_name_list   = []
    base_submodule_name_to_instance_list_dic = {}
    # first get current module inf
    module_inf        = FileInfLib.get_module_inf(module_name)
    if not module_inf:
        return func_instance_name_submodule_name_list, base_submodule_name_to_instance_list_dic
    # get the subcall inf list for current module
    if module_inf.setdefault('subcall_instance_list',None) == None:
        assert(FileInfLib.module_inf_add_subcall_instance_list(module_inf))
    subcall_instance_list = module_inf['subcall_instance_list']
    for subcall_inf in subcall_instance_list:
        instance_name  =  subcall_inf['instance_name']
        submodule_name =  subcall_inf['submodule_name']
        if submodule_name in G['BaseModuleInf']['BaseModules']:
            base_submodule_name_to_instance_list_dic.setdefault(submodule_name,[])
            base_submodule_name_to_instance_list_dic[submodule_name].append(instance_name)
        else:
            func_instance_name_submodule_name_list.append( (instance_name, submodule_name) )
    return func_instance_name_submodule_name_list, base_submodule_name_to_instance_list_dic


# this function used to get the subcall topo inf
def get_fram_topo_sub_inf(topo_module, cur_level):
    sub_level   = cur_level + 1
    topo_prefix = G['Frame_Inf']['FoldLevelSpace'] * sub_level
    topo_datas   = []
    topo_links   = []
    func_instance_name_submodule_name_list, base_submodule_name_to_instance_list_dic = get_sub_func_base_module(topo_module)
    # first deal sub func module, show "inst(module)"
    for instance_name, submodule_name in func_instance_name_submodule_name_list:
        # gen show data
        c_str      = '%s%s(%s)'%(topo_prefix, instance_name, submodule_name)
        topo_datas.append(c_str)
        # gen link
        c_topo_link_parm = {
             'Type'             : 'topo'         # fold_unfold_frame_action()
            ,'fold_level'       : sub_level      # fold_unfold_frame_action() 
            ,'fold_status'      : 'off'          # fold_unfold_frame_action()
            ,'topo_module'      : submodule_name # fold_unfold_frame_action()
            ,'go_module_name'   : submodule_name # for fold_unfold_frame_action()
        }
        c_topo_link = gen_hyperlink(['go_module_action', 'fold_unfold_frame_action'], c_topo_link_parm, Type = 'topo')
        c_topo_link['payload_dic']['topo_instance_name'] = instance_name
        submodule_inf = FileInfLib.get_module_inf(submodule_name)
        if submodule_inf:
            # show cur module, then all submodule, last call set to cur module
            FileInfLib.set_module_last_call_inf(submodule_name, topo_module, instance_name)
        topo_links.append(c_topo_link)
    # deal base modules 
    base_submodule_name_list = list(base_submodule_name_to_instance_list_dic)
    base_submodule_name_list.sort()
    if len(base_submodule_name_list) > 0:
        # deal base , show "module(n)"
        # add one to sep func and base
        topo_datas.append(topo_prefix+'------')
        c_topo_link_parm = {
             'Type'             : 'topo'         # fold_unfold_frame_action()
            ,'fold_level'       : sub_level      # fold_unfold_frame_action() 
            ,'fold_status'      : 'fix'          # fold_unfold_frame_action()
            ,'topo_module'      : ''             # fold_unfold_frame_action()
            ,'go_module_name'   : ''             # for fold_unfold_frame_action()
        }
        c_topo_link = gen_hyperlink(['go_module_action', 'fold_unfold_frame_action'], c_topo_link_parm, Type = 'topo')
        c_topo_link['payload_dic']['topo_instance_name'] = ''  
        topo_links.append(c_topo_link)
        for submodule_name in base_submodule_name_list:
            # deal data
            instance_num = len(base_submodule_name_to_instance_list_dic[submodule_name])
            c_str = '%s%s(%d)'%(topo_prefix, submodule_name, instance_num)
            topo_datas.append(c_str)
            # deal link
            c_topo_link_parm = {
                 'Type'             : 'topo'         # fold_unfold_frame_action()
                ,'fold_level'       : sub_level      # fold_unfold_frame_action() 
                ,'fold_status'      : 'off'          # fold_unfold_frame_action()
                ,'topo_module'      : submodule_name # fold_unfold_frame_action()
                ,'go_module_name'   : submodule_name # for fold_unfold_frame_action()
            }
            c_topo_link = gen_hyperlink(['go_module_action', 'fold_unfold_frame_action'], c_topo_link_parm, Type = 'topo')
            c_topo_link['payload_dic']['topo_instance_name'] = ''
            topo_links.append(c_topo_link)
    assert( len(topo_datas) == len(topo_links) )
    return topo_datas, topo_links

# used to generate topo data and file_link for current module
def gen_top_topo_data_link(topo_module):
    topo_datas   = []
    topo_links   = []
    topo_module_inf = FileInfLib.get_module_inf(topo_module)
    if not topo_module_inf:
        PrintDebug('Error: get topo module name %s, should has module inf !'%(topo_module))
        return topo_datas, topo_links
    TopTopoLevel    = G['TopoInf']['TopFoldLevel']
    TopTopoPrefix   = G['Frame_Inf']['FoldLevelSpace'] * TopTopoLevel
    # add first topo line 
    topo_datas.append(TopTopoPrefix + 'ModuleTopo:')
    topo_link_parm = {
         'Type'             : 'topo'            # fold_unfold_frame_action()
        ,'fold_level'       : TopTopoLevel - 1  # fold_unfold_frame_action() 
        ,'fold_status'      : 'on'              # fold_unfold_frame_action()
        ,'topo_module'      : ''                # fold_unfold_frame_action()
        ,'go_module_name'   : ''                # for fold_unfold_frame_action()
    }
    topo_link = gen_hyperlink(['go_module_action', 'fold_unfold_frame_action'], topo_link_parm, Type = 'topo')
    topo_link['payload_dic']['topo_instance_name'] = ''
    topo_links.append(topo_link)
    # add cur module name
    topo_datas.append(TopTopoPrefix + topo_module + ':')
    topo_link_parm = {
         'Type'             : 'topo'            # fold_unfold_frame_action()
        ,'fold_level'       : TopTopoLevel      # fold_unfold_frame_action() 
        ,'fold_status'      : 'on'              # fold_unfold_frame_action()
        ,'topo_module'      : topo_module       # fold_unfold_frame_action()
        ,'go_module_name'   : topo_module       # for fold_unfold_frame_action()
    }
    topo_link = gen_hyperlink(['go_module_action', 'fold_unfold_frame_action'], topo_link_parm, Type = 'topo')
    topo_link['payload_dic']['topo_instance_name'] = ''
    topo_links.append(topo_link)
    # gen current module sub function module, and base module topo inf
    sub_module_data, sub_module_link = get_fram_topo_sub_inf(topo_module, 0)
    topo_datas = topo_datas + sub_module_data
    topo_links = topo_links + sub_module_link
    assert( len(topo_datas) == len(topo_links) )
    return topo_datas, topo_links

# this function used to show the module's topo
def show_topo(topo_module_name = ''):
    if not topo_module_name:
        cursor_inf      = get_cur_cursor_inf()
        if cursor_inf['hdl_type'] != 'verilog':
            # if not in support file type(verilog,vhdl) just return
            PrintReport("Note: Current only support verilog !")
            return False
        # get current module inf
        cur_module_inf   = None
        cur_line_inf     = FileInfLib.get_file_line_inf(cursor_inf['line_num'], cursor_inf['file_path'])
        if cur_line_inf:
            cur_module_inf = cur_line_inf['module_inf']  
        # current not at module lines, just return
        if not cur_module_inf:
            PrintReport("Note: Current cursor not in valid module !")
            return False
        topo_module_name = cur_module_inf['module_name']
    else:
        topo_module_inf = FileInfLib.get_module_inf(topo_module_name)
        if not topo_module_inf:
            PrintReport("Note: show topo module %s not have database !"%(topo_module_name))
            return False
    # if frame not show ,show it
    Show(G['Frame_Inf']['Frame_Path'])
    # current module must has module inf
    G['TopoInf']['CurModule']  = topo_module_name  # note cur topo name for refresh
    range_inf                  = get_frame_range_inf()
    has_topo                   = range_inf['has_topo']
    topo_range                 = range_inf['topo_range']
    topo_data, topo_link       = gen_top_topo_data_link(topo_module_name)
    # del old topo, add new topo
    if has_topo: # del
        edit_vim_buffer_and_file_link( path = G['Frame_Inf']['Frame_Path'], mode = 'del', del_range = topo_range )
    edit_vim_buffer_and_file_link( G['Frame_Inf']['Frame_Path'], topo_data, topo_link, add_index = topo_range[0] )
    return True

# this function call by refrech_topo , to iteration open fold
def iteration_fold_on_module(inst_module_pairs, base_modules):
    c_frame_range_inf = get_frame_range_inf()
    if not c_frame_range_inf['has_topo']:
        return
    frame_path   = G['Frame_Inf']['Frame_Path']
    c_topo_range = c_frame_range_inf['topo_range']
    assert( frame_path in G['VimBufferLineFileLink'] )
    c_topo_links = G['VimBufferLineFileLink'][frame_path][c_topo_range[0] : c_topo_range[1] + 1]
    for i,lk in enumerate(c_topo_links):
        if not( lk and (lk['action_parm_dic']['fold_status'] == 'off') and lk['action_parm_dic']['topo_module'] ):
            continue
        if lk['payload_dic']['topo_instance_name']:
            c_inst_module_pair = (lk['payload_dic']['topo_instance_name'], lk['action_parm_dic']['topo_module'])
            if c_inst_module_pair in inst_module_pairs:
                fold_frame_line(i+c_topo_range[0], lk['action_parm_dic']['fold_level'], 'topo', lk['action_parm_dic']['topo_module'])
                iteration_fold_on_module(inst_module_pairs, base_modules)
                return
        else:
            if lk['action_parm_dic']['topo_module'] in base_modules:
                fold_frame_line(i+c_topo_range[0], lk['action_parm_dic']['fold_level'], 'topo', lk['action_parm_dic']['topo_module'])
                iteration_fold_on_module(inst_module_pairs, base_modules)
                return
    return


# this function used refresh topo, when add a base module
def refresh_topo():
    # get all folded module or inst pair
    old_frame_range_inf = get_frame_range_inf()
    if not old_frame_range_inf['has_topo']:
        return
    frame_path     = G['Frame_Inf']['Frame_Path']
    old_topo_range = old_frame_range_inf['topo_range']
    assert(frame_path in G['VimBufferLineFileLink'])
    old_topo_links = G['VimBufferLineFileLink'][frame_path][old_topo_range[0] + 2 : old_topo_range[1] + 1]
    old_fold_inst_module_pairs = set()
    old_fold_base_modules      = set()
    for lk in old_topo_links:
        if not( lk and (lk['action_parm_dic']['fold_status'] == 'on') and lk['action_parm_dic']['topo_module'] ):
            continue
        if lk['payload_dic']['topo_instance_name']:
            old_fold_inst_module_pairs.add( (lk['payload_dic']['topo_instance_name'], lk['action_parm_dic']['topo_module']) )
        else:
            if lk['action_parm_dic']['topo_module'] in G['BaseModuleInf']['BaseModules']:
                old_fold_base_modules.add(lk['action_parm_dic']['topo_module'])
    # start new topo
    new_topo_module_name = G['TopoInf']['CurModule']
    show_topo(new_topo_module_name)
    # iteration opened old folded topo
    iteration_fold_on_module(old_fold_inst_module_pairs, old_fold_base_modules)

#-------------------------------------------------------------------------------
# checkpoint relate function
#-------------------------------------------------------------------------------
# this function used to show check points
def show_check_point(fold = True):
    frame_data   = []
    frame_link   = []
    # if frame not show ,show it
    Show(G['Frame_Inf']['Frame_Path'])
    # add initial line
    level        = G['CheckPointInf']['TopFoldLevel']
    show_str     = G['Frame_Inf']['FoldLevelSpace']*level + 'CheckPoints:'
    file_link_parm = {
         'Type'             : 'check_point' # fold_unfold_frame_action()
        ,'fold_level'       : level         # fold_unfold_frame_action() 
        ,'fold_status'      : 'on'          # fold_unfold_frame_action()
        ,'go_path'          : ''            # go_file_action()
        ,'go_pos'           : ()            # go_file_action()
        ,'go_word'          : ''            # go_file_action()
    }
    file_link = gen_hyperlink(['go_file_action', 'fold_unfold_frame_action'], file_link_parm, Type = 'check_point')
    frame_data.append(show_str)
    frame_link.append(file_link)
    # add check points
    range_inf         = get_frame_range_inf()
    has_check_point   = range_inf['has_check_point']
    check_point_range = range_inf['check_point_range']
    if fold:
        for cp in G['CheckPointInf']['CheckPoints']:
            frame_data.append(cp['key'])  
            frame_link.append(cp['link'])
    else:
        frame_link[-1]['fold_status'] = 'off'
    assert(len(frame_data)==len(frame_link))
    # del old cp, add new cp
    if has_check_point: # del
        edit_vim_buffer_and_file_link( path = G['Frame_Inf']['Frame_Path'], mode = 'del', del_range = check_point_range )
    edit_vim_buffer_and_file_link( G['Frame_Inf']['Frame_Path'], frame_data, frame_link, add_index = check_point_range[0] )
    return True


#-------------------------------------------------------------------------------
# basemodule relate function
#-------------------------------------------------------------------------------
# update function base information, no need added each times
def update_base_module_pickle():
    pkl_output = open(G['VTagsPath'] + '/pickle/all_basemodule_name_set.pkl','wb')
    pickle.dump(G['BaseModuleInf']['BaseModules'], pkl_output)
    pkl_output.close()

# this function used to get base module frame data/link
def get_fram_base_module_inf():
    datas = []
    links = []
    base_module_level = G['BaseModuleInf']['TopFoldLevel'] + 1
    base_module_space = G['Frame_Inf']['FoldLevelSpace'] * base_module_level
    base_module_name_list      = list(G['BaseModuleInf']['BaseModules'])
    base_module_name_list.sort()
    for base_module_name in base_module_name_list:
        show_str  = base_module_space + base_module_name
        file_link_parm = {
             'Type'             : 'base_module'          # fold_unfold_frame_action()
            ,'fold_level'       : base_module_level      # fold_unfold_frame_action() 
            ,'fold_status'      : 'fix'                  # fold_unfold_frame_action()
            ,'go_module_name'   : base_module_name       # for fold_unfold_frame_action()
        }
        file_link = gen_hyperlink(['go_module_action', 'fold_unfold_frame_action'], file_link_parm, Type = 'base_module')
        datas.append(show_str)
        links.append(file_link)
    assert(len(datas) == len(links))
    return datas, links

# this function used to show the current base module
def show_base_module(fold = True):
    frame_data   = []
    frame_link   = []
    # if frame not show ,show it
    Show(G['Frame_Inf']['Frame_Path'])
    # add initial line
    level     = G['BaseModuleInf']['TopFoldLevel']
    show_str  = G['Frame_Inf']['FoldLevelSpace']*level + 'BaseModules:'
    file_link_parm = {
         'Type'             : 'base_module'  # fold_unfold_frame_action()
        ,'fold_level'       : level          # fold_unfold_frame_action() 
        ,'fold_status'      : 'on'           # fold_unfold_frame_action()
        ,'go_module_name'   : ''             # for fold_unfold_frame_action()
    }
    file_link = gen_hyperlink(['go_module_action', 'fold_unfold_frame_action'], file_link_parm, Type = 'base_module')
    frame_data.append(show_str)
    frame_link.append(file_link)
    # add check points
    range_inf         = get_frame_range_inf()
    has_base_module   = range_inf['has_base_module']
    base_module_range = range_inf['base_module_range']
    cp_data = []
    cp_link = []
    if fold:
        cp_data, cp_link  = get_fram_base_module_inf()
    else:
        frame_link[-1]['fold_status'] = 'off'
    frame_data = frame_data + cp_data
    frame_link = frame_link + cp_link
    assert(len(frame_data) == len(frame_link))
    # del old cp, add new cp
    if has_base_module: # del
        base_module_range = ( base_module_range[0] + 1, base_module_range[1] )
        frame_data = frame_data[1:]
        frame_link = frame_link[1:]
        edit_vim_buffer_and_file_link( path = G['Frame_Inf']['Frame_Path'], mode = 'del', del_range = base_module_range )
    edit_vim_buffer_and_file_link( G['Frame_Inf']['Frame_Path'], frame_data, frame_link, add_index = base_module_range[0] )
    return True

#-------------------------------------------------------------------------------
# fold/unfold function
#-------------------------------------------------------------------------------
def unfold_frame_line(frame_links, frame_line, cur_frame_level, cur_frame_type):
    assert(frame_links[frame_line]['action_parm_dic']['fold_status'] == 'on')
    assert(G['Frame_Inf']['Frame_Path'] in G['VimBufferLineFileLink'])
    G['VimBufferLineFileLink'][ G['Frame_Inf']['Frame_Path'] ][frame_line]['action_parm_dic']['fold_status'] = 'off'
    unfold_end_line_num =  frame_line
    for i in range(frame_line+1, len(frame_links)):
        # if cur not have file link, then cur is unflod end
        if not frame_links[i]:
            unfold_end_line_num = i - 1
            break
        # if has file link ,but not topo inf then unflod end
        if frame_links[i]['action_parm_dic']['Type'] != cur_frame_type:
            unfold_end_line_num = i - 1
            break
        # if is topo , but level <= cur level then unflod end
        if frame_links[i]['action_parm_dic']['fold_level'] <= cur_frame_level:
            unfold_end_line_num = i - 1
            break
        unfold_end_line_num = i
    # if cur module has no sub module then just return
    if unfold_end_line_num == frame_line:
        return True
    # else edit the frame buffer and file link, del the unflod lines
    if unfold_end_line_num > frame_line:
        edit_vim_buffer_and_file_link( path = G['Frame_Inf']['Frame_Path'], mode = 'del', del_range = (frame_line + 1, unfold_end_line_num) )
        return True
    # else some trouble
    assert(0),'shold not happen !'


# this function used to fold frame line
def fold_frame_line(frame_line, cur_frame_level, cur_frame_type, cur_module_name = ''):
    assert(G['Frame_Inf']['Frame_Path'] in G['VimBufferLineFileLink'])
    G['VimBufferLineFileLink'][ G['Frame_Inf']['Frame_Path'] ][frame_line]['action_parm_dic']['fold_status'] = 'on'
    if cur_frame_type == 'topo':
        # if cur is ModuleTopo: line, show refresh topo
        if cur_frame_level == G['TopoInf']['TopFoldLevel'] - 1:
            topo_module_name = G['TopoInf']['CurModule']
            show_topo(topo_module_name)
            return
        if not cur_module_name:
            PrintReport('Note: cur topo line has no module name !')
            return 
        if not FileInfLib.get_module_inf(cur_module_name):
            PrintReport('Note: current module: \"%s\" not found in design !'%(cur_module_name))
            return
        # get cur module sub module inf
        sub_topo_data, sub_topo_link = get_fram_topo_sub_inf(cur_module_name, cur_frame_level)
        # add cur module topo inf to frame
        edit_vim_buffer_and_file_link( G['Frame_Inf']['Frame_Path'], sub_topo_data, sub_topo_link, add_index = frame_line + 1 )
    elif cur_frame_type == 'check_point':
        show_check_point()
    elif cur_frame_type == 'base_module':
        show_base_module()
    else:
        PrintReport('Note: no operation in this line !')
    return

# this function used to the frame window fold
def frame_line_fold_operation(frame_line):
    frame_path     = G['Frame_Inf']['Frame_Path']
    if frame_path not in G['VimBufferLineFileLink']:
        PrintReport('Note: cur frame line no fold operation !')
        return
    frame_links    = G['VimBufferLineFileLink'][frame_path]
    if frame_line >= len(frame_links):
        PrintReport('Note: cur frame line no fold operation !')
        return
    cur_line_link  = frame_links[frame_line]
    if not cur_line_link :
        PrintReport('Note: cur frame line no fold operation !')
        return
    intime_parms_dic = {
         'frame_line'  : frame_line
        ,'frame_links' : frame_links }
    cur_line_link['intime_parms_dic'] = intime_parms_dic
    do_hyperlink(cur_line_link, 'fold_unfold_frame_action')

def fold_unfold_frame_action(intime_parms_dic, Type, fold_level, fold_status, topo_module = ''):
    frame_line  = intime_parms_dic['frame_line']
    frame_links = intime_parms_dic['frame_links']
    if fold_status == 'off':
        fold_frame_line(frame_line, fold_level, Type, topo_module)
    elif fold_status == 'on':
        unfold_frame_line(frame_links, frame_line, fold_level, Type)
    else:
        PrintReport('Note: cur frame line no fold operation !')
    return
register_hyperlink_action( fold_unfold_frame_action, description = 'this link function fold or unfold frame lines' )

# hyperlink action go_module_action
def go_module_action( go_module_name ):
    module_inf  = FileInfLib.get_module_inf(go_module_name)
    if not module_inf:
        PrintReport('Warning: module:%s not find in design !'%(go_module_name))
        return False
    go_win( module_inf['file_path'], module_inf['module_name_match_pos'], go_module_name)
    return True
register_hyperlink_action( go_module_action, description = 'this link function goto the module define position' )
