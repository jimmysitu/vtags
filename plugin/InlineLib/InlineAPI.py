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
# import vim, when gen vtags it will no vim,so use try 
try:
    import vim
except: 
    pass
# import normal lib
import re
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
from InlineLib.ViewLib import *
import Lib.CodeLib as CodeLib
import InlineLib.FrameLib as FrameLib
import Lib.FileInfLib as FileInfLib

# open snapshort wins
if G['InlineActive'] and G['EnvSnapshortWinsInf']:
    # snapshort's work window trace
    OldOpenWinTrace = [p for p in G['WorkWin_Inf']['OpenWinTrace']]
    # add cur buffer in cur work window trace
    G['WorkWin_Inf']['OpenWinTrace'].insert(0,vim.current.buffer.name)
    # for all snapshort window(include work win, hold win ...)
    # first open saved window
    for w_inf in G['EnvSnapshortWinsInf']:
        c_path   = w_inf['path']
        c_cursor = w_inf['cursor']
        if os.path.isfile(c_path):
            Open(c_path)
            # if new open window not in old work win, del from new work win
            # trace , maybe hold win, reload need also hold
            if c_path not in OldOpenWinTrace:
                if G['WorkWin_Inf']['OpenWinTrace'] and G['WorkWin_Inf']['OpenWinTrace'][-1] == c_path:
                    del G['WorkWin_Inf']['OpenWinTrace'][-1]
        else:
            PrintReport('Note: reload file not exit ! file: %s'%(c_path))
    # resize the reload window
    for w_inf in G['EnvSnapshortWinsInf']:
        c_size   = w_inf['size']
        c_path   = w_inf['path']
        if os.path.isfile(c_path):
            Open(c_path)
            vim.current.window.width   = c_size[0]
            vim.current.window.height  = c_size[1]
    # because base module may be changed so refresh topo and show base
    if G['Frame_Inf']['Frame_Path'] in [ w.buffer.name for w in vim.windows]:
        FrameLib.refresh_topo()
        FrameLib.show_base_module()
    PrintReport('Note: reload snapshort finish !')
elif G['InlineActive']:
    # treat the first win as work win , if cur win is hdl code, and add first trace point
    first_cursor_inf = get_cur_cursor_inf()
    if first_cursor_inf['hdl_type'] == 'verilog':
        G['WorkWin_Inf']['OpenWinTrace'].append(first_cursor_inf['file_path'])
        add_trace_point()
    #print('vtags initialization successfully !')


# shortcut key: gi
def go_into_submodule(): 
    cursor_inf         = get_cur_cursor_inf()
    subcall_cursor_inf = CodeLib.get_subcall_pos_inf( cursor_inf['file_path'], cursor_inf['pos'], cursor_inf['codes'] )
    if not subcall_cursor_inf:
        PrintReport('Note: not found module instance at current cursor line, do-nothing !')
        return True
    assert(subcall_cursor_inf['subcall_inf'])
    # for case subcall recoginize not accuracy, may because of '`ifdef, `endif ...'
    if subcall_cursor_inf['subcall_inf']['inaccuracy']: 
        PrintReport('Warning: carefull the trace result, subcall module:%s, instance:%s inaccuracy !'%(subcall_cursor_inf['subcall_inf']['module_name'], subcall_cursor_inf['subcall_inf']['instance_name']))
    # it is subcall must go subcall, has 2 case:
    # case 1, cursor on valid io connect, go submodule io line
    # case 2, cursor not on valid io connect, just go submodule define line
    submodule_name = subcall_cursor_inf['subcall_inf']['submodule_name']
    submodule_inf  = FileInfLib.get_module_inf(submodule_name)
    if not submodule_inf:
        PrintReport('Warning: can not find module:%s define in design, do-nothing !'%(submodule_name))
        return True
    go_path = submodule_inf['file_path']
    go_word = submodule_name
    go_pos  = submodule_inf['module_name_match_pos']
    if subcall_cursor_inf['submodule_io_inf']: # case 1
        go_word = subcall_cursor_inf['submodule_io_inf']['name']
        go_pos  = subcall_cursor_inf['submodule_io_inf']['name_pos']
    # note upper module information
    subcall_instance_name = subcall_cursor_inf['subcall_inf']['instance_name']
    cur_module_inf  = subcall_cursor_inf['module_inf']
    cur_module_name = cur_module_inf['module_name']
    FileInfLib.set_module_last_call_inf(submodule_name, cur_module_name, subcall_instance_name)
    # go submodule
    add_trace_point()
    go_win( go_path, go_pos, go_word)


def try_go_into_submodule():
    if not G['InlineActive']: return
    if G['Debug']:
        go_into_submodule()
    else:
        try: go_into_submodule()
        except: pass


# shortcut key: gu
def go_upper_module(): 
    cursor_inf         = get_cur_cursor_inf()
    # get cur module name
    cur_module_name    = ''
    cur_module_inf     = None
    cur_line_inf       = FileInfLib.get_file_line_inf(cursor_inf['line_num'], cursor_inf['file_path'])
    if cur_line_inf:
        cur_module_inf = cur_line_inf['module_inf']    
    if not cur_module_inf:
        PrintReport('Note: current cursor not in valid module, do-nothing !')
        return
    cur_module_name = cur_module_inf['module_name']
    # get cur module last call upper module inf
    cur_last_call_inf   = FileInfLib.get_module_last_call_inf(cur_module_name)
    already_get_upper = False
    if cur_last_call_inf:
        upper_subcall_inf              = cur_last_call_inf['upper_subcall_inf']
        upper_module_path              = upper_subcall_inf['file_path']
        upper_submodule_name_match_pos = upper_subcall_inf['submodule_name_match_pos']
        upper_instance_name            = upper_subcall_inf['instance_name']
        add_trace_point()
        go_win( upper_module_path, upper_submodule_name_match_pos, upper_instance_name)
        already_get_upper = True
    # even has upper, also should list all the poss upper
    line_and_link_list = CodeLib.get_upper_module_line_and_link_list( cur_module_name )
    if line_and_link_list:
        # i = 0 
        link_list = []
        line_list = []
        # pre inf
        line_list.append('Knock "<Space>" to choise upper module you want: ')
        line_list.append('')
        link_list.append( {} )
        link_list.append( {} )
        line_list += line_and_link_list['line_list']
        link_list += line_and_link_list['link_list']
        mounted_line_inf  = MountPrintLines(line_list, label = 'Possible Upper', link_list = link_list)
        mounted_line_list = mounted_line_inf['line_list']
        mounted_link_list = mounted_line_inf['link_list']
        # add a empty line below
        mounted_line_list.append('')
        mounted_link_list.append({})
        if link_list:
            add_trace_point()
            assert( len(mounted_line_list) == len(mounted_link_list) )
            PrintReport(mounted_line_list, mounted_link_list, MountPrint = True )
            if not already_get_upper:
                if len(line_and_link_list['line_list']) == 1:
                    for link in link_list:
                        if link:
                            do_hyperlink(link, ['go_file_action', 'add_module_last_call_action']) # first valid link
                            break
                else:
                    # len(mounted_line_list) + 1 is the lines relative to the last report line
                    # -4 is skip first 4 unused line
                    go_win( G['Report_Inf']['Report_Path'] , (-(len(mounted_line_list) + 1 -4), 49) )
    else:
        PrintReport('Note: module %s not called by upper module before !'%(cur_module_name))
    return

def try_go_upper_module():
    if not G['InlineActive']: return
    if G['Debug']:
        go_upper_module()
    else:
        try: go_upper_module()
        except: pass

# shortcut key: mt
def print_module_trace(): 
    cursor_inf         = get_cur_cursor_inf()
    # get cur module name
    cur_module_name    = ''
    cur_module_inf     = None
    cur_line_inf       = FileInfLib.get_file_line_inf(cursor_inf['line_num'], cursor_inf['file_path'])
    if cur_line_inf:
        cur_module_inf = cur_line_inf['module_inf']    
    if not cur_module_inf:
        PrintReport('Note: current cursor not in valid module, do-nothing !')
        return
    cur_module_name = cur_module_inf['module_name']
    # recursion get all trace
    full_traces = []
    FileInfLib.recursion_get_module_trace(cur_module_name, [], full_traces)
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
    mounted_line_list = MountPrintLines(print_strs, label = 'Module Trace')['line_list']
    mounted_line_list.append('')
    mounted_line_list.append('')
    PrintReport(mounted_line_list, MountPrint = True )
    # edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], mounted_line_list)
    return

def try_print_module_trace():
    if not G['InlineActive']: return
    if G['Debug']:
        print_module_trace()
    else:
        try: print_module_trace()
        except: pass

# shortcut key: <Space><Left>
def trace_signal_sources():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cursor_inf        = get_cur_cursor_inf()
    trace_signal_name = cursor_inf['word']
    if not trace_signal_name:
        PrintReport("Note: current cursor not on signal name, do-nothing !")
        return
    # case0: if cur cursor on a macro, go macro define
    if CodeLib.trace_glb_define_signal('source', cursor_inf): return
    # case1: if cur cursor on io signal, need cross to upper module
    if CodeLib.trace_io_signal('source', cursor_inf, report_level = 0 ): return
    # case2: if cur cursor on module call io line go to submodule io
    if CodeLib.trace_signal_at_subcall_lines('source', cursor_inf, report_level = 0 ): return
    # case3: trace signal same as pre trace signal, just show next result
    if (G['TraceInf']['LastTraceSource']['Path'] == cursor_inf['file_path']) \
        and (G['TraceInf']['LastTraceSource']['SignalName'] == trace_signal_name) \
        and (G['TraceInf']['LastTraceSource']['ValidLineRange'][0] <= cursor_inf['line_num']) \
        and (G['TraceInf']['LastTraceSource']['ValidLineRange'][1] >= cursor_inf['line_num']) :
        show_next_trace_result('source')
        PrintDebug('Trace: trace_signal_sources, just show next result!')
        return
    # case4: trace a new normal(not io, sub call io) signal
    if CodeLib.trace_normal_signal('source', cursor_inf): return

def try_trace_signal_sources():
    if not G['InlineActive']: return
    if G['Debug']:
        trace_signal_sources()
    else:
        try: trace_signal_sources()
        except: pass


# shortcut key: <Space><Right>
def trace_signal_destinations():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cursor_inf = get_cur_cursor_inf()
    trace_signal_name = cursor_inf['word']
    if not trace_signal_name:
        PrintReport("Note: Current cursor not on signal name, can not trace dest!")
        return
    # case0: if cur cursor on io signal, need cross to upper module
    if CodeLib.trace_io_signal('dest', cursor_inf, report_level = 0 ): return
    # case1: if cur cursor on module call io line go to submodule io
    if CodeLib.trace_signal_at_subcall_lines('dest', cursor_inf): return
    # case2: trace signal same as pre trace signal, just show next result
    if (G['TraceInf']['LastTraceDest']['Path'] == cursor_inf['file_path']) \
        and (G['TraceInf']['LastTraceDest']['SignalName'] == trace_signal_name) \
        and (G['TraceInf']['LastTraceDest']['ValidLineRange'][0] <= cursor_inf['line_num']) \
        and (G['TraceInf']['LastTraceDest']['ValidLineRange'][1] >= cursor_inf['line_num']) :
        show_next_trace_result('dest')
        return
    # case3: if cur cursor on a macro, go macro define
    if CodeLib.trace_glb_define_signal('dest', cursor_inf): return
    # case4: trace a new normal(not io, sub call io) signal
    CodeLib.trace_normal_signal('dest', cursor_inf)

def try_trace_signal_destinations():
    if not G['InlineActive']: return
    if G['Debug']:
        trace_signal_destinations()
    else:
        try: trace_signal_destinations()
        except: pass


# shortcut key: <Space><Down> 
def roll_back():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cur_nonius        = G['OpTraceInf']['Nonius'] - 1
    TracePoints       = G['OpTraceInf']['TracePoints']
    # if reach to the oldest trace point just return
    if cur_nonius < 0:
        PrintReport("Note: roll backed to the oldest trace point now !")
        return
    # go to the trace point
    cur_point = TracePoints[cur_nonius]
    G['OpTraceInf']['Nonius'] = cur_nonius
    go_win( cur_point['path'], cur_point['pos'], cur_point['key'])
    return

def try_roll_back():
    if not G['InlineActive']: return
    if G['Debug']:
        roll_back()
    else:
        try: roll_back()
        except: pass


# shortcut key: <Space><Up> 
def go_forward():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cur_nonius        = G['OpTraceInf']['Nonius'] + 1
    TracePoints       = G['OpTraceInf']['TracePoints']
    if cur_nonius >= len(TracePoints):
        PrintReport("Note: go forward to the newest trace point now !")
        return
    cur_point = TracePoints[cur_nonius]
    G['OpTraceInf']['Nonius'] = cur_nonius
    go_win( cur_point['path'], cur_point['pos'], cur_point['key'])
    return

def try_go_forward():
    if not G['InlineActive']: return
    if G['Debug']:
        go_forward()
    else:
        try: go_forward()
        except: pass


# shortcut key: <space>
def space_operation():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cursor_inf = get_cur_cursor_inf()
    # if cur in Frame or Report, show file link files
    if cursor_inf['file_path'] in [ G['Frame_Inf']['Frame_Path'], G['Report_Inf']['Report_Path'] ]:
        # bug fix if no link add before here will out of range
        cur_frame_link = {}
        if cursor_inf['line_num'] < len( G['VimBufferLineFileLink'][cursor_inf['file_path']] ):
            cur_frame_link = G['VimBufferLineFileLink'][cursor_inf['file_path']][cursor_inf['line_num']]
        add_trace_point()
        if not cur_frame_link:
            PrintReport('Note: No file link in current line ! ')
            return
        # for single_action_link
        if cur_frame_link['type'] == 'single_action_link':
            do_hyperlink(cur_frame_link)
            add_trace_point()
            return
        # for topo and base_module, need refresh
        if cur_frame_link['type'] in ['topo', 'base_module']:
            do_hyperlink(cur_frame_link, 'go_module_action')
            add_trace_point()
            return
        # for check_point
        if cur_frame_link['type'] == 'check_point':
            do_hyperlink(cur_frame_link, 'go_file_action')
            add_trace_point()
            return
        # for possible_upper
        if cur_frame_link['type'] == 'possible_upper':
            do_hyperlink(cur_frame_link, ['go_file_action', 'add_module_last_call_action'])
            add_trace_point()
            return
        # for possible_trace_upper
        if cur_frame_link['type'] == 'possible_trace_upper':
            do_hyperlink(cur_frame_link, ['add_module_last_call_action', 'trace_io_signal_action'])
            add_trace_point()
            return
    return

def try_space_operation():
    if not G['InlineActive']: return
    if G['Debug']:
        space_operation()
    else:
        try: space_operation()
        except: pass


# shortcut key: <Space>v
def show_frame():
    G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
    if cur_in_frame():
        cursor_line = vim.current.window.cursor[0] - 1 
        FrameLib.frame_line_fold_operation(cursor_line)
    else:
        FrameLib.show_topo()
        FrameLib.show_check_point(False)
        FrameLib.show_base_module(False)
    return

def try_show_frame():
    if not G['InlineActive']: return
    if G['Debug']:
        show_frame()
    else:
        try: show_frame()
        except: pass
    return


# shortcut key: <Space>h
def hold_current_win():
    cur_path = vim.current.buffer.name
    # just del current win frome work win, then will not auto close current win
    for i,path in enumerate(G['WorkWin_Inf']['OpenWinTrace']):
        if cur_path == path:
            del G['WorkWin_Inf']['OpenWinTrace'][i]
            break

def try_hold_current_win():
    if not G['InlineActive']: return
    if G['Debug']:
        hold_current_win()
    else:
        try: hold_current_win()
        except: pass


# shortcut key: <Space>c
def add_check_point():
    G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
    cursor_inf   = get_cur_cursor_inf()
    level        = G['CheckPointInf']['TopFoldLevel'] + 1 
    key          = G['Frame_Inf']['FoldLevelSpace']*level + cursor_inf['word']
    link_parm = {
         'Type'             : 'check_point'            # fold_unfold_frame_action()
        ,'fold_level'       : level                    # fold_unfold_frame_action() 
        ,'fold_status'      : 'fix'                    # fold_unfold_frame_action()
        ,'go_path'          : cursor_inf['file_path']  # go_file_action()
        ,'go_pos'           : cursor_inf['pos']        # go_file_action()
        ,'go_word'          : cursor_inf['word']       # go_file_action()
        ,'last_modify_time' : os.path.getmtime( cursor_inf['file_path'] )
    }
    link = gen_hyperlink(['go_file_action', 'fold_unfold_frame_action'], link_parm, Type = 'check_point')
    G['CheckPointInf']['CheckPoints'].insert(0, {'key': key, 'link': link })
    if len(G['CheckPointInf']['CheckPoints']) > G['CheckPointInf']['MaxNum']:
        del G['CheckPointInf']['CheckPoints'][-1]
    FrameLib.show_check_point()

def try_add_check_point():
    if not G['InlineActive']: return
    if G['Debug']:
        add_check_point()
    else:
        try: add_check_point()
        except: pass


# shortcut key: <Space>b
def add_base_module():
    G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
    cursor_inf    = get_cur_cursor_inf()
    cursor_module = cursor_inf['word']
    if not cursor_module:
        PrintReport('Note: cursor not on a valid word ! ')
        return
    if cursor_module in G['BaseModuleInf']['BaseModules']:
        PrintReport('Note: module %s is already base module ! '%(cursor_module))
        return
    G['BaseModuleInf']['BaseModules'].add(cursor_module)
    FrameLib.update_base_module_pickle()
    FrameLib.show_base_module()
    FrameLib.refresh_topo()

def try_add_base_module():
    if not G['InlineActive']: return
    if G['Debug']:
        add_base_module()
    else:
        try: add_base_module()
        except: pass


# shortcut key: <Space>d
def del_operation():
    if not cur_in_frame():
        PrintReport('Note: Cur file no del function ! ')
        return
    cur_path      = vim.current.buffer.name
    cur_line_num  = vim.current.window.cursor[0] - 1
    cur_file_link = G['VimBufferLineFileLink'][cur_path][cur_line_num]
    if not cur_file_link:
        PrintReport('Note: Cur line no del function ! ')
        return
    # delete a check point, if link has path means a valid link
    if (cur_file_link['action_parm_dic']['Type'] == 'check_point') and (cur_file_link['action_parm_dic']['fold_level'] > G['CheckPointInf']['TopFoldLevel']):
        G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
        check_point_begin_line_num = FrameLib.get_frame_range_inf()['check_point_range'][0]
        del_index = cur_line_num - check_point_begin_line_num - 1
        del G['CheckPointInf']['CheckPoints'][ del_index ]
        FrameLib.show_check_point()
        return
    # del a base module
    if (cur_file_link['action_parm_dic']['Type'] == 'base_module') and (cur_file_link['action_parm_dic']['fold_level'] > G['BaseModuleInf']['TopFoldLevel']): 
        G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
        G['BaseModuleInf']['BaseModules'].remove(cur_file_link['action_parm_dic']['go_module_name'])
        FrameLib.update_base_module_pickle()
        FrameLib.show_base_module()
        FrameLib.refresh_topo()
        return
    PrintReport('Note: Cur line no del function ! ')

def try_del_operation():
    if not G['InlineActive']: return
    if G['Debug']:
        del_operation()
    else:
        try: del_operation()
        except: pass

# shortcut key: <Space>s
def try_save_env_snapshort():
    if not G['InlineActive']: return
    if G['Debug']:
        if G['SaveEnvSnapshort_F']():
            PrintReport('Note: save env snapshort success !')
    else:
        try: 
            if G['SaveEnvSnapshort_F']():
                PrintReport('Note: save env snapshort success !')
        except: pass
