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
from Lib.ExceptionLib import *

#-------------------------------------------------------------------------------
# get next empty frame, report,log report index, first try del Frame, Report
#-------------------------------------------------------------------------------
# this function used to del not used old run.log in vtags.db
def del_old_logs(vtags_db_folder_path):
    ls_a_f = [ f.strip('\n') for f in os.popen('ls -a ' + vtags_db_folder_path).readlines() ]
    used_log_index = set()
    for f in ls_a_f:
        match_swp = re.match('\.(Frame|Report|run)(?P<idx>\d+)(\.ZL|\.log)(\.v)?\.swp',f)
        if match_swp:
            used_log_index.add(int(match_swp.group('idx')))
    ls_f   = [ f.strip('\n') for f in os.popen('ls ' + vtags_db_folder_path).readlines() ]
    for f in ls_f:
        match_idx = re.match('(Frame|Report|run)(?P<idx>\d+)(\.ZL|\.log)(\.v)?', f)
        if not match_idx:
            continue
        cur_index = int(match_idx.group('idx'))
        if cur_index in used_log_index:
            continue
        os.system('rm %s/%s'%(vtags_db_folder_path,f) )
    return

#-------------------------------------------------------------------------------
# this function used to get the path postfix
#-------------------------------------------------------------------------------
def get_file_path_postfix(file_path):
    split_by_dot = file_path.split('.')
    if len(split_by_dot) < 2: # which means file_path has no postfix
        return ''
    post_fix = split_by_dot[-1]          # postfix care case
    return post_fix

# this function used to save env snapshort
def save_env_snapshort():
    snapshort = {}
    # 0: save cur dir path, used to quality opne snapshort
    snapshort['snapshort_dir_path'] = os.getcwd()
    # 1: save Frame
    snapshort['frame_file_lines'] = []
    if os.path.isfile(G['Frame_Inf']['Frame_Path']):
        snapshort['frame_file_lines'] = open(G['Frame_Inf']['Frame_Path'],'r').readlines()
    # 2: save Report
    snapshort['report_file_lines'] = []
    if os.path.isfile(G['Report_Inf']['Report_Path']):
        snapshort['report_file_lines'] = open(G['Report_Inf']['Report_Path'],'r').readlines()
    # 3: save G
    snapshort['G'] = {}
    snapshort['G']['OpTraceInf']                   = {}
    snapshort['G']['OpTraceInf']['TracePoints']    = G['OpTraceInf']['TracePoints'] 
    snapshort['G']['OpTraceInf']['Nonius'     ]    = G['OpTraceInf']['Nonius'     ]
    snapshort['G']['WorkWin_Inf']                  = {}
    snapshort['G']['WorkWin_Inf']['OpenWinTrace']  = G['WorkWin_Inf']['OpenWinTrace']
    snapshort['G']['VimBufferLineFileLink' ]       = G["VimBufferLineFileLink" ]
    snapshort['G']["TraceInf"              ]       = G['TraceInf']
    snapshort['G']['CheckPointInf']                = {}
    snapshort['G']['CheckPointInf']['CheckPoints'] = G['CheckPointInf']['CheckPoints']
    snapshort['G']['TopoInf']                      = {}
    snapshort['G']['TopoInf']['CurModule']         = G['TopoInf']['CurModule']
    snapshort['G']['ModuleLastCallInf']            = G['ModuleLastCallInf']
    snapshort['G']['Frame_Inf']                    = {}
    snapshort['G']['Frame_Inf']['Frame_Path']      = G['Frame_Inf']['Frame_Path']
    snapshort['G']['Report_Inf']                   = {}
    snapshort['G']['Report_Inf']['Report_Path']    = G['Report_Inf']['Report_Path']
    # 4: save act windows inf
    act_win_inf = []
    for w in vim.windows:
        c_file_path = w.buffer.name
        if c_file_path == vim.current.buffer.name:
            continue
        c_cursor    = w.cursor
        c_size      = (w.width, w.height)
        act_win_inf.append({'path': c_file_path, 'cursor': c_cursor, 'size': c_size })
    # last is current window
    cur_file_path  = vim.current.buffer.name
    cur_cursor     = vim.current.window.cursor   
    cur_size       = (vim.current.window.width, vim.current.window.height)
    act_win_inf.append({'path': cur_file_path, 'cursor': cur_cursor, 'size': cur_size })
    snapshort['act_win_inf'] = act_win_inf
    pkl_output = open(G['VTagsPath'] + '/pickle/env_snapshort.pkl','wb')
    pickle.dump(snapshort, pkl_output)
    pkl_output.close()
    return True

def reload_env_snapshort(snapshort):
    # 1: reload G
    snapshort_G = snapshort['G']
    G['OpTraceInf']['TracePoints']    = snapshort_G['OpTraceInf']['TracePoints'] 
    G['OpTraceInf']['Nonius'     ]    = snapshort_G['OpTraceInf']['Nonius'     ]
    G['WorkWin_Inf']['OpenWinTrace']  = snapshort_G['WorkWin_Inf']['OpenWinTrace']
    G['VimBufferLineFileLink' ]       = snapshort_G["VimBufferLineFileLink" ]
    G["TraceInf"              ]       = snapshort_G['TraceInf']
    G['CheckPointInf']['CheckPoints'] = snapshort_G['CheckPointInf']['CheckPoints']
    G['TopoInf']['CurModule']         = snapshort_G['TopoInf']['CurModule']
    G['ModuleLastCallInf']            = snapshort_G['ModuleLastCallInf']
    G['Frame_Inf']['Frame_Path']      = snapshort_G['Frame_Inf']['Frame_Path']
    G['Report_Inf']['Report_Path']    = snapshort_G['Report_Inf']['Report_Path']
    # 2: reload Frame
    os.system('touch ' + G['Frame_Inf']['Frame_Path'])
    assert(os.path.isfile(G['Frame_Inf']['Frame_Path']))
    frame_fp = open(G['Frame_Inf']['Frame_Path'],'w')
    for l in snapshort['frame_file_lines']:
        frame_fp.write(l)
    frame_fp.close()
    # 3: reload Report
    os.system('touch ' + G['Report_Inf']['Report_Path'])
    assert(os.path.isfile(G['Report_Inf']['Report_Path']))
    report_fp = open(G['Report_Inf']['Report_Path'],'w')
    for l in snapshort['report_file_lines']:
        report_fp.write(l)
    report_fp.close()
    # 4: reload act windows inf need re open at API.py
    G['EnvSnapshortWinsInf'] = snapshort['act_win_inf']
    return

def init_G_from_vtagsDB( vtags_db_folder_path = '', RaiseExcept = False ):
    #-------------------------------------------------------------------------------
    # get vtags.db
    # find most resent vtags path from current folder to upper
    #-------------------------------------------------------------------------------
    if not vtags_db_folder_path:
        cur_path = os.getcwd()
        while cur_path and cur_path[0] == '/':
            if os.path.isdir(cur_path + '/vtags.db'):
                vtags_db_folder_path = cur_path + '/vtags.db'
                break
            cur_path = re.sub('/[^/]*$','',cur_path)
    # if not found a valid vtags db and need raise except to speed up 
    # none vtags vim open
    if RaiseExcept and (not os.path.isdir(vtags_db_folder_path)):
        raise VtagsDBNotFoundExcept
    #-------------------------------------------------------------------------------
    # get config
    # get finial config, if has vtag.db local config use local, if not use install
    # path glable config 
    #-------------------------------------------------------------------------------
    # first import vim glable config in install path
    sys.path.append('../')
    import vim_glb_config as glb_config
    config        = glb_config
    if vtags_db_folder_path:
        vtags_db_folder_path = os.path.realpath(vtags_db_folder_path) # incase for link
        sys.path.insert(0,vtags_db_folder_path)
        # if already import vim_local_config del it
        try:
            del vim_local_config
        except:
            pass
        # re import vim_local_config
        try:
            import vim_local_config
            config = vim_local_config
        except:
            pass
    #-------------------------------------------------------------------------------
    # init get the supported design file postfix
    # real supported postfix is config.support_verilog_postfix add postfix geted by 
    # the input file list
    #-------------------------------------------------------------------------------
    file_list_postfix = set()
    try:
        pkl_input           = open(vtags_db_folder_path + '/file_list_postfix.pkl','rb')
        file_list_postfix   = pickle.load(pkl_input)
        pkl_input.close()
    except:
        pass
    support_design_postfix_set = file_list_postfix | set(config.support_verilog_postfix)
    # find the minimum number current not used as the next log postfix
    valid_log_index = 0
    if vtags_db_folder_path:
        del_old_logs(vtags_db_folder_path)
        all_file_names_in_vtags_db = " ".join( os.listdir(vtags_db_folder_path) )
        while re.search( "(^|\s)(\.)?(((Frame|Report)%d\.ZL)|(run%d\.log))(\W|$)"%(valid_log_index, valid_log_index), all_file_names_in_vtags_db):
            valid_log_index += 1
    # stale now # file link used as a link to space option:
    # stale now # ----------------------------------------------------------------------------------------------------------------------
    # stale now # | type        | go_path       | go_pos          | go_word     | fold_status | fold_level | last_modify_time | discription
    # stale now # |-------------|---------------|-----------------|-------------|-------------|------------|------------------|--------------
    # stale now # | topo        | module path   | module name pos | module name | on/off      | n          | n                | Frame : link to topo line module
    # stale now # | base_module | module path   | module name pos | module name | on/off      | n          | n                | Frame : link to base module
    # stale now # | check_point | cp added path | cursor pos      | cursor word | on/off      | n          | n                | Frame : link to check point location
    # stale now # | trace result| result path   | result match pos| trace signal|             |            |                  | Report: link to trace source dest
    # stale now # ---------------------------------------------------------------------------------------------------------------------------
    # stale now # all vim buffer line file link, a path to file link list dic
    VimBufferLineFileLink = {}
    
    
    Frame_Inf = {
         "Frame_Win_x"        : config.frame_window_width      # frame window width
        ,"Frame_Path"         : ''
        ,"FoldLevelSpace"     : config.frame_fold_level_space
    }
    Frame_Inf['Frame_Path'] = vtags_db_folder_path + '/' + "Frame" + str(valid_log_index) + '.ZL'
    
    
    Report_Inf = {
         "Report_Win_y"       : config.report_window_height        # report window height
        ,"Report_Path"        : ''
    }
    Report_Inf['Report_Path'] = vtags_db_folder_path + '/' + "Report" + str(valid_log_index) + '.ZL.v'
    
    
    WorkWin_Inf ={
         "MaxNum"       : config.max_open_work_window_number
        ,"OpenWinTrace" : []
    }
    
    TraceInf = {
         'LastTraceSource' : {'Maybe':[], 'Sure':[], 'ShowIndex': 0, 'SignalName':'', 'ValidLineRange':[-1,-1], 'Path':'' } # Maybe[{'show':'', 'file_link':{ 'key':'','pos':(l,c),'path':'' } }] 
        ,'LastTraceDest'   : {'Maybe':[], 'Sure':[], 'ShowIndex': 0, 'SignalName':'', 'ValidLineRange':[-1,-1], 'Path':'' }
        ,'TraceSourceOptimizingThreshold' : config.trace_source_optimizing_threshold
    }
    
    # operation trace
    OpTraceInf = {
         'TracePoints' : [] # {'path':'', "pos":(line, colum), 'key':''}
        ,'TraceDepth'  : config.max_roll_trace_depth
        ,'Nonius'      : -1  # roll nonius 
    }
    
    TopoInf       = {
         'CurModule'    : ''
        ,'TopFoldLevel' : 0
    }
    
    CheckPointInf = {
         "MaxNum"         : config.max_his_check_point_num
        ,"CheckPoints"    : []  #{}--- key: '', link: {}
        ,"TopFoldLevel"   : 0
    }
    
    #-------------------------------------------------------------------------------
    # init the base module inf
    #-------------------------------------------------------------------------------
    BaseModules   = set()
    # get base module inf
    try:
        pkl_input     = open(vtags_db_folder_path + '/pickle/all_basemodule_name_set.pkl','rb')
        BaseModules   = pickle.load(pkl_input)
        pkl_input.close()
    except:
        pass
    
    BaseModuleInf = {
         "BaseModuleThreshold"  : config.base_module_threshold  # when module inst BaseModuleThreshold times, then default set it to base module
        ,"BaseModules"          : BaseModules # module name set()
        ,"TopFoldLevel"         : 0
    }

    CallMeSubcallInf = {
         "AddUpperThreshold"                   : None
        ,"ModuleNameToCallMeSubcallInfListDic" : None
        ,"MaskedCallMeSubmoduleSet"            : None
    }
    try: # valid in vtags-2.20
        CallMeSubcallInf["AddUpperThreshold"] = config.module_add_upper_threshold
    except: # for pre version's local config
        CallMeSubcallInf["AddUpperThreshold"] = glb_config.module_add_upper_threshold

    # max file name length in current os    
    try: # valid in vtags-2.22
        MaxFileNameLength = config.max_file_name_length # max file file name length
    except: # for pre version's local config
        MaxFileNameLength = glb_config.max_file_name_length

    G = {
         'InlineActive'                        : True
        ,'OfflineActive'                       : True
        ,'SupportVHDLPostfix'                  : set([])
        ,'SupportVerilogPostfix'               : support_design_postfix_set # 1.23 add filelist postfix and config postfix
        ,'ModuleNameToModuleInfListDic'        : {}
        ,'ModuleNameToFilePathListDic'         : None
        ,'ModuleLastCallInf'                   : {}    # {module_name:{ upper_module_name:'', 'upper_inst_name':inst_name} }
        ,'FileInf'                             : {}
        ,'MacroNameToMacroInfListDic'          : None  # {name: [ {name path pos code_line} ]}
        ,'OpTraceInf'                          : OpTraceInf
        ,"Debug"                               : config.debug_mode    # debug mode
        ,"RefreshDBValid"                      : config.dynamic_update_vtags_db
        ,"ShowReport"                          : config.show_report
        ,"PrintDebug_F"                        : None         # function to print debug
        ,"Frame_Inf"                           : Frame_Inf    # Frame window inf
        ,"Report_Inf"                          : Report_Inf   # report window inf
        ,"WorkWin_Inf"                         : WorkWin_Inf  # win config
        ,"VimBufferLineFileLink"               : VimBufferLineFileLink
        ,"TraceInf"                            : TraceInf
        ,"CheckPointInf"                       : CheckPointInf
        ,"BaseModuleInf"                       : BaseModuleInf
        ,'TopoInf'                             : TopoInf
        ,"FixExtraSpace"                       : True         # some situation come extra space, need do nonthing
        ,"IgnoreNextSpaceOp"                   : False        # just fold has a else space, not do space op
        ,"EnvSnapshortWinsInf"                 : []
        ,"SaveEnvSnapshort_F"                  : save_env_snapshort
        ,"VTagsPath"                           : vtags_db_folder_path
        ,"RunLogPath"                          : vtags_db_folder_path + '/run.log'+str(valid_log_index)
        ,"CallMeSubcallInf"                    : CallMeSubcallInf
        # add for path reduce
        ,"Short2RealPathMap"                   : None # some times pickle file name is too long to creat a file, so use this map to reduce it.
        ,"Real2ShortPathMap"                   : {}
        ,"MaxFileNameLength"                   : MaxFileNameLength # max file file name length
    }
    return G


#-------------------------------------------------------------------------------
# if not open vim inline turn off
# if open a empty file, try reload snapshort
# if open a unsupport rtl inline turn off
#-------------------------------------------------------------------------------
vim_opened           = False
try_reload_snapshort = False
vim_start_open_file  = ''
try:
    import vim
    vim_start_open_file = vim.current.buffer.name
    if not vim_start_open_file: # if vim opened and open a empty file, means need reload snapshort
        try_reload_snapshort = True
    vim_opened  = True
except:
    pass

#-------------------------------------------------------------------------------
# init G 
#-------------------------------------------------------------------------------
# if no vim opened means it's Offline function, so even if no vtags.db
# found in init_G_from_vtagsDB() it must not raise VtagsDBNotFoundExcept 
# except because user can set vtags db use set_vtags_db_path()
# if vim has opened, must has a valid vtags db, if not found just raise
# VtagsDBNotFoundExcept and terminate the python run
G = None
if vim_opened:
    G = init_G_from_vtagsDB( RaiseExcept = True )
else:
    G = init_G_from_vtagsDB()
    G['InlineActive']  = False  # if no vim opened must not active inline function

#-------------------------------------------------------------------------------
# if not found vtags db nonthing can work
#-------------------------------------------------------------------------------
if not os.path.isdir(G['VTagsPath']):
    G['OfflineActive'] = False
    G['InlineActive']  = False

# if vim opened and not reload snapshort and not open a supported rtl design
# not active inline function
if vim_opened and (not try_reload_snapshort) \
    and (get_file_path_postfix(vim_start_open_file) not in G['SupportVerilogPostfix']):
    G['InlineActive'] = False
    # if not a valid vtags recgnize file and need raise except to speed up 
    # none vtags vim open
    raise VtagsUnsupportFileExcept

#-------------------------------------------------------------------------------
# this function used to print debug inf:
# (1) generate vtags.db generate vtags.db/vtags_db.log
# (2) when debug = True generate run.logN when gvim run
#-------------------------------------------------------------------------------
# if run cmd:"vtags" in generate vtags situation, print log to vtags.db/vtags_run.log
vtags_db_log_path = ['']
# run log path
def PrintDebug( str, out_path = ''):
    if vtags_db_log_path[0]:
        output = open( vtags_db_log_path[0], 'a')
        output.write(str+'\n')
        output.close()
        return
    if not G['InlineActive'] and G['OfflineActive'] and G['Debug']:
        print(str)
    if out_path and G['Debug']:
        output = open( out_path, 'a')
        output.write(str+'\n')
        output.close()
        return
    if G['InlineActive'] and G['Debug']:
        output = open( G['RunLogPath'] ,'a')
        output.write(str+'\n')
        output.close()
G['PrintDebug_F'] = PrintDebug

#-------------------------------------------------------------------------------
# if gvim without file and has saved history sence then just replay it
#-------------------------------------------------------------------------------
if try_reload_snapshort:
    env_snapshort_path = G['VTagsPath'] + '/pickle/env_snapshort.pkl'
    if os.path.isfile(env_snapshort_path):
        pkl_input        = open(G['VTagsPath'] + '/pickle/env_snapshort.pkl','rb')
        loaded_snapshort = pickle.load(pkl_input)
        pkl_input.close()
        if loaded_snapshort['snapshort_dir_path'] == os.getcwd(): # make sure save dir is the same to open dir
            os.system('echo \'do you want reload vim snapshort ? (y/n): \'')
            yes_or_no = raw_input()
            if yes_or_no.lower() in ['y','yes']:
                reload_env_snapshort(loaded_snapshort)

def set_vtags_db_path(vtags_db_folder_path):
    vtags_db_folder_path = vtags_db_folder_path.rstrip('/')
    if vtags_db_folder_path[-8:] != 'vtags.db' or (not os.path.isdir(vtags_db_folder_path)):
        return False
    new_G = init_G_from_vtagsDB( vtags_db_folder_path )
    for key in G:
        G[key] = new_G[key]
    G['InlineActive']  = False
    return True








