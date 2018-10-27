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

try:
    import vim
except: 
    pass
import sys
import re
import os
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *

# this fulction used to reset Frame win and Report win size to:
#-------------------------------------------------------------
#|                 |                                         |
#|                 |                                         |
#|                 |                                         |
#|                 |                                         |
#|                 |               Work                      |
#|      FRAME      |                                         |
#|                 |                                         |
#|                 |                                         |
#|                 |                                         |
#|                 |                                         |
#|                 |-----------------------------------------|-----------
#|                 |                                         |     |
#|                 |             Report                      | Report_Win_y
#|                 |                                         |     |
#|-----------------|------------------------------------------------------
#|<- Frame_Win_x ->|
def Reset_Win_Size():
    cur_act_wins = Cur_Act_Win()
    if G['Report_Inf']['Report_Path'] in cur_act_wins:
        Jump_To_Win(G['Report_Inf']['Report_Path'])
        vim.command('wincmd J')
        vim.current.window.height = G['Report_Inf']['Report_Win_y']
    if G['Frame_Inf']['Frame_Path'] in cur_act_wins:
        Jump_To_Win(G['Frame_Inf']['Frame_Path'])
        vim.command('wincmd H')
        vim.current.window.width = G['Frame_Inf']['Frame_Win_x']
    return

# this function used to del closed window in the open window trace
def Refresh_OpenWinTrace():
    cur_act_win_path      = Cur_Act_Win()
    cur_act_work_win_path = cur_act_win_path - set([ G["Report_Inf"]["Report_Path"], G["Frame_Inf"]["Frame_Path"] ])
    i = 0
    while i < len(G['WorkWin_Inf']['OpenWinTrace']) :
        c_path = G['WorkWin_Inf']['OpenWinTrace'][i]
        if c_path not in cur_act_work_win_path:
            del G['WorkWin_Inf']['OpenWinTrace'][i]
        else:
            i += 1
    return

# this function get all the opened window file path
def Cur_Act_Win():
    Act_Win = set()
    for w in vim.windows:
        Act_Win.add(w.buffer.name)
    return Act_Win

# this functhon used to open a file
# if file already open jump to that window
# if file not opened, and opened window not beyond max open win number, open a new window 
# if file not opened, and opened window beyond max open win number, close a old and open a new window 
def Open(path):
    Act_Win = Cur_Act_Win()
    if path in Act_Win: # win has open and just jump to than window
        Jump_To_Win(path)
    elif path == G['Frame_Inf']["Frame_Path"]:
        Open_Frame_Win()
        Reset_Win_Size()
    elif path == G['Report_Inf']["Report_Path"]:
        Open_Report_Win()
        Reset_Win_Size()
    else:
        Open_Work_Win(path)
    Jump_To_Win(path)
    assert(vim.current.buffer.name == path)

# if current path already opened, jump to the path windows
def Jump_To_Win(path):
    cur_act_wins = Cur_Act_Win()
    assert(path in cur_act_wins)
    start_path = vim.current.buffer.name
    if start_path == path:
        return
    vim.command('wincmd w')
    cur_path = vim.current.buffer.name
    while cur_path != start_path:
        if cur_path == path:
            break
        vim.command("wincmd w")
        cur_path = vim.current.buffer.name
    assert(vim.current.buffer.name == path),'vim.current.buffer.name: %s, path: %s'%(vim.current.buffer.name, path)

# open a new frame window at most left
def Open_Frame_Win():
    G['VimBufferLineFileLink'].setdefault(G["Frame_Inf"]["Frame_Path"],[{}])
    vim.command("vertical topleft sp " + G["Frame_Inf"]["Frame_Path"])

# open a new report window at most bottom
def Open_Report_Win():
    G['VimBufferLineFileLink'].setdefault(G["Report_Inf"]["Report_Path"],[{}])
    vim.command("bot sp " + G["Report_Inf"]["Report_Path"])
    if G["Frame_Inf"]["Frame_Path"] in Cur_Act_Win():
        Jump_To_Win(G["Frame_Inf"]["Frame_Path"])
    vim.command('wincmd H')
    Jump_To_Win(G["Report_Inf"]["Report_Path"])

# check if file already opened in other window
def has_swp_file(path):
    seprate_path_and_file = re.match('(?P<path>.*/)?(?P<file>[^/]+)$', path)
    assert(seprate_path_and_file)
    # get file path
    file_path = ''
    if seprate_path_and_file.group('path'):
        file_path = seprate_path_and_file.group('path')
    # get swp file name
    swp_file_name = '.%s.swp'%(seprate_path_and_file.group('file'))
    # check if exist swp file
    if os.path.exists(file_path + swp_file_name):
        return True
    return False

# open a new work window, if opened beyond threshold, close a old win for new
def Open_Work_Win(path):
    # weather need resize report and frame win
    need_resize_frame_report_win = False
    # path must valid
    assert(os.path.isfile(path))
    # refresh open work win trace
    Refresh_OpenWinTrace()
    # leave at most G['WorkWin_Inf']['MaxNum'] work win
    win_num_need_to_close = len(G['WorkWin_Inf']['OpenWinTrace']) - G['WorkWin_Inf']['MaxNum']
    for i in range(win_num_need_to_close):
        win_path_need_close = G['WorkWin_Inf']['OpenWinTrace'][i]
        Jump_To_Win(win_path_need_close)
        vim.command('q')
        need_resize_frame_report_win = True
        del G['WorkWin_Inf']['OpenWinTrace'][i]
    # if has work win
    cur_work_win_num = len(G['WorkWin_Inf']['OpenWinTrace'])
    if cur_work_win_num > 0:
        # case 0: has work win, and num less than max
        #         just go last work win, and vsp a new win
        if cur_work_win_num < G['WorkWin_Inf']['MaxNum']:
            Jump_To_Win(G['WorkWin_Inf']['OpenWinTrace'][-1])
            # special for file already opened just open in read only mode
            if has_swp_file(path):
                print('found ".%s.swp" so open in read only mode !'%(path))
                vim.command('vsp | view '+path)
            else:
                vim.command('vsp '+path)
            need_resize_frame_report_win = True
        else: # case 1: opened all work win, just replace the oldest open work win
            Jump_To_Win(G['WorkWin_Inf']['OpenWinTrace'][0])
            # special for file already opened just open in read only mode
            if has_swp_file(path):
                print('found ".%s.swp" so open in read only mode !'%(path))
                vim.command('e | view '+path)
            else:
                vim.command('e '+path)
            del G['WorkWin_Inf']['OpenWinTrace'][0] # replace [0], just del old
    else: # cur no work win
        cur_act_win_paths = Cur_Act_Win()
        cur_act_hold_wins = cur_act_win_paths - set([G["Report_Inf"]["Report_Path"], G["Frame_Inf"]["Frame_Path"]])
        # if has hold win, go hold win, vsp
        if cur_act_hold_wins:
            Jump_To_Win(list(cur_act_hold_wins)[0])
            # special for file already opened just open in read only mode
            if has_swp_file(path):
                print('found ".%s.swp" so open in read only mode !'%(path))
                vim.command('vsp | view '+path)
            else:
                vim.command('vsp '+path)
            need_resize_frame_report_win = True
        elif G["Report_Inf"]["Report_Path"] in cur_act_win_paths:
            # if no hold win, has report , go report sp new
            Jump_To_Win(G["Report_Inf"]["Report_Path"])
            # special for file already opened just open in read only mode
            if has_swp_file(path):
                print('found ".%s.swp" so open in read only mode !'%(path))
                vim.command('sp | view '+path)
            else:
                vim.command('sp '+path)
            need_resize_frame_report_win = True
        else:
            vim.command('vsp '+path)
            need_resize_frame_report_win = True
    if need_resize_frame_report_win:
        Reset_Win_Size()
        Jump_To_Win(path)
    # finial add path to trace
    assert(vim.current.buffer.name == path)
    G['WorkWin_Inf']['OpenWinTrace'].append(path)

# go to the window and cursor to pos, and used search highlight word
def go_win( path = '', pos = (), highlight_word = ''):
    if not path or not os.path.isfile(path):
        return
    Open(path)
    # fix bug for search instance_name[4:0]
    valid_highlight = re.search('\w+',highlight_word)
    if valid_highlight:
        valid_highlight_word = valid_highlight.group()
        vim.current.window.cursor = (1,0) # search from top in case match to left vim warning
        vim.command('/\c\<'+valid_highlight_word+'\>')
    if pos:
        max_x     = len( vim.current.buffer ) - 1 #  len( vim.current.buffer[ len(vim.current.buffer) - 1 ] ) )
        valid_pos = [max_x, None]
        # row
        if (pos[0] < 0) and ((max_x + pos[0]) >= 0):
            valid_pos[0] = max_x + pos[0] + 1 # -1 is the last line
        if (pos[0] >= 0) and (pos[0] <= max_x):
            valid_pos[0] = pos[0]
        # colum
        max_y        = len( vim.current.buffer[ valid_pos[0] ] )
        valid_pos[1] = max_y
        if (pos[1] < 0) and ((max_y + pos[1]) >= 0):
            valid_pos[1] = max_y + pos[1] + 1 # -1 is the last char
        if (pos[1] >= 0) and (pos[1] <= max_y):
            valid_pos[1] = pos[1]
        vim.current.window.cursor = (valid_pos[0] + 1, valid_pos[1] )


# this function used to open file and go to file lines
def open_file_separately(file_path, jump_to_line):
    assert(os.path.isfile(file_path))
    assert(type(jump_to_line) == int and jump_to_line >= 0 )
    os.system('gvim %s +%d'%(file_path, jump_to_line + 1)) # add 1 because gvim line start from 1
    return True


