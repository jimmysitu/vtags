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
from InlineLib.WinLib import *

# hyperlink action go_file_action
def go_file_action( go_path, go_pos = (), go_word = '', last_modify_time = 0.0, report_stale = True):
    if not os.path.exists(go_path):
        PrintReport('Warning: file not exists ! file:%s'%(go_path))
        return False
    if report_stale and (last_modify_time != 0.0):
        if not check_inf_valid(go_path, last_modify_time):
            PrintReport('Warning: file modified before, this link maybe stale ! file: %s'%(go_path))
    go_win( go_path, go_pos, go_word)
    return True
register_hyperlink_action( go_file_action, description = 'this link function goto the dest file position' )


#-------------------------------------------------------------------------------
# here used to temporary store current cursor location
# and return when need
#-------------------------------------------------------------------------------
SnapshotStack = []

# save cursor location
def snapshort_push():
    cur_cursor        = vim.current.window.cursor
    cur_pos           = (cur_cursor[0]-1, cur_cursor[1]) # minus 1 because cursor start from 1, and lines start from 0
    cur_line          = vim.current.buffer[cur_pos[0]]
    cur_word          = get_full_word(cur_line, cur_pos[1])
    cur_file_path     = vim.current.buffer.name
    cur_snapshort     = {"path": cur_file_path, "pos":cur_pos, "key":cur_word}
    SnapshotStack.append(cur_snapshort)

# reload cursor location
def snapshort_pop():
    pop_snapshort = SnapshotStack[-1]
    del SnapshotStack[-1]
    go_win( pop_snapshort['path'], pop_snapshort['pos'], pop_snapshort['key'])

#-------------------------------------------------------------------------------
# this function used to let the path show in window, but maybe not cursor window
#-------------------------------------------------------------------------------
def Show(path): # just show frame win , and not go to that window
    Act_Win = Cur_Act_Win()
    if path not in Act_Win:
        snapshort_push()
        Open(path)
        snapshort_pop()
    return

#-------------------------------------------------------------------------------
# this function used to add a trace point used by <Space><Left> , <Space><Right>
#-------------------------------------------------------------------------------
def add_trace_point():
    cur_cursor        = vim.current.window.cursor
    cur_file_path     = vim.current.buffer.name
    if cur_file_path in [ G['Frame_Inf']['Frame_Path'], G['Report_Inf']['Report_Path'] ]:
        return
    cur_pos           = (cur_cursor[0]-1, cur_cursor[1]) # minus 1 because cursor start from 1, and lines start from 0
    cur_line_num      = cur_pos[0] 
    cur_line          = vim.current.buffer[cur_line_num]
    cur_word          = get_full_word(cur_line, cur_pos[1])
    cur_trace_point   = {"path": cur_file_path, "pos":cur_pos, "key":cur_word}
    cur_nonius        = G['OpTraceInf']['Nonius']
    TracePoints       = G['OpTraceInf']['TracePoints']
    # when roll back, and add from middle of queue, just clear old trace point after cur insert index
    # |  0  |  1  |  2  |  3  |  4  |
    #                      ^           if len 5, nonius <= 3 then del 4 
    if cur_nonius <= (len(TracePoints) - 2):
        del TracePoints[cur_nonius + 1 : ]
    # add a new point to TracePoints
    # if cur add is equ to pre not add
    if not TracePoints:
        TracePoints.append(cur_trace_point)
    else:
        pre_point = TracePoints[-1]
        if cur_trace_point != pre_point:
            TracePoints.append(cur_trace_point)
    # if length bigger than TraceDepth del 
    TraceDepth        = G['OpTraceInf']['TraceDepth']
    while (len(TracePoints) > TraceDepth):
        del TracePoints[0]
    # if add new point ,nonius assign to len(TracePoints)
    # |  0  |  1  |  2  |  3  |  4  |
    #                                 ^  because roll back will first sub 1
    G['OpTraceInf']['Nonius'] = len(TracePoints)


#-------------------------------------------------------------------------------
# this function used to get current cursor information
#-------------------------------------------------------------------------------
def get_cur_cursor_inf():
    cur_cursor       = vim.current.window.cursor
    cur_line_num     = cur_cursor[0] - 1 # minus 1 because cursor start from 1, and lines start from 0
    cur_colm_num     = cur_cursor[1]
    cur_line         = vim.current.buffer[cur_line_num]
    cur_word         = get_full_word(cur_line, cur_cursor[1])
    cur_codes        = vim.current.buffer
    cur_file_path    = vim.current.buffer.name
    cur_hdl_type     = get_file_hdl_type(cur_file_path)
    return {  'cursor'           : cur_cursor
             ,'pos'              : (cur_line_num, cur_colm_num)
             ,'line_num'         : cur_line_num
             ,'colm_num'         : cur_colm_num
             ,'line'             : cur_line
             ,'word'             : cur_word
             ,'file_path'        : cur_file_path
             ,'hdl_type'         : cur_hdl_type
             ,'codes'            : cur_codes }


#-------------------------------------------------------------------------------
# this function edit the vim buffer and corresponding file_links
# 
#     vim_buffer                file_links
#  ----------------          ----------------------------
# |0:              |        |0: {}                        |
# |1: topo_module  |        |1: {type:topo,....}          |
# |2: check_point  |        |2: {type:check_point,...}    |
# |3: ...          | ---->  |3: {}                        |
# |4: trace_result |        |4: {type:trace_result,...}   |
# |                |        |                             |
# |                |        |                             |
#  ----------------          -----------------------------
# 
# mode : add/del
# add_index: 0 add to top, -1: add to bottom, -2: clear all and add, other add to line n
# del_range: int del line, range del reange
#
# care file_link add when valid in, so before will no filelink or on file_link index
#-------------------------------------------------------------------------------
def edit_vim_buffer_and_file_link(path = '', data = [], file_link = [], mode = 'add', add_index = -1, del_range = None):
    if mode == 'add' and add_index != 2 and data == []:
        return
    # because of vim bug reason, edit buffer not current cursor in may
    # happen add line to current cursor buffer, so we make sure when edit, cursor
    # must in current buffer win, after edit will go back to pre cousor pos
    edit_current_buffer = False
    if path == vim.current.buffer.name:
        edit_current_buffer = True
    if not edit_current_buffer:
        snapshort_push()
        Open(path)
    assert(path == vim.current.buffer.name)
    edit_buffer = vim.current.buffer
    if mode == 'del':  # deal delete case
        # if del buffer has valid file_link, del too
        if type(del_range) is int:
            del_range = [del_range, del_range]
        assert(type(del_range) in [ tuple, list ]),'Error: unsupport del_range: %s.'%(del_range.__str__())
        if path in G["VimBufferLineFileLink"]: 
            del G["VimBufferLineFileLink"][path][ del_range[0] : del_range[1]+1 ]
        del edit_buffer[ del_range[0] : del_range[1]+1 ]
    elif mode == 'add': # deal add/insert case
        # if data is a string, put in list
        if type(data) == str:
            data = [ data ]
        # start add file_link when the first valid file_link comes with data.
        # if a valid file_link comes, file_link will align to buffer data,
        # for empty line file_link set to None
        need_add_file_link = False
        if file_link:
            assert( len(data) == len(file_link) ),'%s,%s'%(data.__str__(),file_link.__str__())
            # if current path no file link before, or buffer length > file_link length
            # add file_link and align it
            G["VimBufferLineFileLink"].setdefault(path, [] )
            G["VimBufferLineFileLink"][path] = G["VimBufferLineFileLink"][path] + [None]*( len(edit_buffer) - len(G["VimBufferLineFileLink"][path]) )
            need_add_file_link = True
        if add_index == 0: # add to top
            edit_buffer.append(data, 0)
            if need_add_file_link:
                G["VimBufferLineFileLink"][path] = file_link + G["VimBufferLineFileLink"][path]
        elif add_index == -1: # add to bottom
            edit_buffer.append(data)
            if need_add_file_link:
                G["VimBufferLineFileLink"][path] = G["VimBufferLineFileLink"][path] + file_link
        elif add_index == -2: # clear all and add top
            del edit_buffer[:]
            if data != []:
                edit_buffer.append(data)
            del edit_buffer[:1]
            if need_add_file_link and data != []:
                G["VimBufferLineFileLink"][path] = file_link
        else: # insert to add_index
            assert(type(add_index) == int and add_index > 0)
            # careful insert maybe insert to n, which n > len(buffer) need add ''
            edit_buffer_len = len(edit_buffer)
            if edit_buffer_len < add_index :
                edit_buffer.append( ['']*(add_index - edit_buffer_len + 1) ) # add 1 because when fold last line, first del then add, del will change cursor if no empty line below
                if need_add_file_link:
                    G["VimBufferLineFileLink"][path] = G["VimBufferLineFileLink"][path] + [None]*(add_index - edit_buffer_len + 1)
            # insert data
            edit_buffer.append(data, add_index)
            if need_add_file_link:
                G["VimBufferLineFileLink"][path] = G["VimBufferLineFileLink"][path][:add_index] + file_link + G["VimBufferLineFileLink"][path][add_index:]
    else:
        assert(0),'Error: unsupport mode: %s.'%(mode.__str__())
    # save the change for frame and report
    # if cur_in_frame() or cur_in_report():
    #     vim.command('w!')
    # go back to pre cursor if not edit current buffer
    if not edit_current_buffer:
        snapshort_pop()


def cur_in_frame():
    return vim.current.buffer.name == G['Frame_Inf']['Frame_Path']

def cur_in_report():
    return vim.current.buffer.name == G['Report_Inf']['Report_Path']


# this function used to show report to report window
# because of vim bug reason, edit buffer not current cursor in may
# happen add line to current cursor buffer, so we make sure when edit, cursor
# must in current buffer win, after edit will go back to pre cousor pos
def PrintReport(show = '', file_link = {}, spec_case = '', mode = 'a', report_level = 0, MountPrint = False ):
    if report_level > 0 or (not G['InlineActive']):
        PrintDebug(show)
        return
    # config use this control weather print report
    if not G['ShowReport']:
        return
    # jump to report file, before edit
    has_self_snap_short = False
    if not cur_in_report():
        snapshort_push()
        Open(G['Report_Inf']['Report_Path'])
        has_self_snap_short = True
    # MountPrint
    if MountPrint:
        if file_link:
            assert(len(show) == len(file_link))
            edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], show, file_link)
        else:
            edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], show)
    elif show: # show_str = show
        assert(type(show) == str)
        if show[0:8] == 'Warning:' or show[0:6] == 'Error:':
            edit_vim_buffer_and_file_link( G['Report_Inf']['Report_Path'], '' )
            show_len = len(show)
            edit_vim_buffer_and_file_link( G['Report_Inf']['Report_Path'], '*'*(80) )
            edit_vim_buffer_and_file_link( G['Report_Inf']['Report_Path'], show )
            edit_vim_buffer_and_file_link( G['Report_Inf']['Report_Path'], '*'*(80) )
            edit_vim_buffer_and_file_link( G['Report_Inf']['Report_Path'], '' )
        else:
            edit_vim_buffer_and_file_link( G['Report_Inf']['Report_Path'], show )
    # show trace source result
    if spec_case == 'source':
        line_list = []
        link_list = []
        for Sure in G['TraceInf']['LastTraceSource']['Sure']:
            line_list.append( Sure['show'].strip('\n') )
            link_list.append( Sure['file_link'] )
        line_list.append('')
        link_list.append({})
        if G['TraceInf']['LastTraceSource']['Maybe']:
            line_list.append('\nlable\n:Maybe Source') 
            link_list.append({})
        for Maybe in G['TraceInf']['LastTraceSource']['Maybe']:
            line_list.append( Maybe['show'] )
            link_list.append( Maybe['file_link'] )
        MountPrint = MountPrintLines(line_list, 'Trace Source', link_list, end_star = False)
        edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], "")
        edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], MountPrint['line_list'], MountPrint['link_list'])
        edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], "")
    # show trace dest result
    elif spec_case == 'dest':
        line_list = []
        link_list = []
        for Sure in G['TraceInf']['LastTraceDest']['Sure']:
            line_list.append( Sure['show'].strip('\n') )
            link_list.append( Sure['file_link'] )
        line_list.append('')
        link_list.append({})
        if G['TraceInf']['LastTraceDest']['Maybe']:
            line_list.append('\nlable\n:Maybe Dest') 
            link_list.append({})
        for Maybe in G['TraceInf']['LastTraceDest']['Maybe']:
            line_list.append( Maybe['show'] )
            link_list.append( Maybe['file_link'] )
        MountPrint = MountPrintLines(line_list, 'Trace Dest', link_list, end_star = False)
        edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], "")
        edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], MountPrint['line_list'], MountPrint['link_list'])
        edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], "")
    # go report to the last line, and return
    assert(cur_in_report())
    vim.current.window.cursor = (len(vim.current.buffer) - 1 , 0)
    # vim.command('w!')
    vim.command('hid')
    Open(G['Report_Inf']['Report_Path'])
    if has_self_snap_short:
        snapshort_pop()

# this function used to go next trace result, when repeat use trace option to
# same signal
def show_next_trace_result( trace_type ):
    if trace_type == 'source':
        cur_show_index   = G['TraceInf']['LastTraceSource']["ShowIndex"]
        sure_source_len  = len(G['TraceInf']['LastTraceSource']['Sure'])
        maybe_source_len = len(G['TraceInf']['LastTraceSource']['Maybe'])
        if (sure_source_len + maybe_source_len) == 0:
            PrintReport('Note: not find source !')
            return
        cur_file_link = {}
        if cur_show_index < sure_source_len:
            cur_file_link = G['TraceInf']['LastTraceSource']['Sure'][cur_show_index]['file_link']
        else:
            cur_file_link = G['TraceInf']['LastTraceSource']['Maybe'][cur_show_index - sure_source_len]['file_link']
        G['TraceInf']['LastTraceSource']["ShowIndex"] = (cur_show_index + 1) % (sure_source_len + maybe_source_len)
        add_trace_point()
        do_hyperlink(cur_file_link)
        # go_win( cur_file_link['go_path'], cur_file_link['go_pos'], cur_file_link['go_word'] )
    elif trace_type == 'dest':
        cur_show_index   = G['TraceInf']['LastTraceDest']["ShowIndex"]
        sure_dest_len  = len(G['TraceInf']['LastTraceDest']['Sure'])
        maybe_dest_len = len(G['TraceInf']['LastTraceDest']['Maybe'])
        if (sure_dest_len + maybe_dest_len) == 0:
            PrintReport('Note: not find dest !')
            return
        cur_file_link = {}
        if cur_show_index < sure_dest_len:
            cur_file_link = G['TraceInf']['LastTraceDest']['Sure'][cur_show_index]['file_link']
        else:
            cur_file_link = G['TraceInf']['LastTraceDest']['Maybe'][cur_show_index - sure_dest_len]['file_link']
        G['TraceInf']['LastTraceDest']["ShowIndex"] = (cur_show_index + 1) % (sure_dest_len + maybe_dest_len)
        add_trace_point()
        do_hyperlink(cur_file_link)
        # go_win( cur_file_link['go_path'], cur_file_link['go_pos'], cur_file_link['go_word'])
    else:
        assert(0)






