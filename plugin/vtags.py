#!/usr/bin/python3
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
__version__ = "2.24.1"
__project_url__ = "http://www.vim.org/scripts/script.php?script_id=5494"

import os
import sys
import re
import pickle

#-------------------------------------------------------------------------------
#print help
#-------------------------------------------------------------------------------
help = ''
try:
    help = sys.argv[1]
except:
    pass

#-------------------------------------------------------------------------------
# get the install folder path
#-------------------------------------------------------------------------------
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
# Offline function
#-------------------------------------------------------------------------------
offline_function_parms = None
try:
    if sys.argv[1] == '-func':
        offline_function_parms = sys.argv[2:]
except:
    pass
sys.path.insert(0,vtags_install_path)
import OfflineLib.OfflineFuncLib as OfflineFuncLib
if offline_function_parms != None:
    OfflineFuncLib.function_run(offline_function_parms)
    exit()

#-------------------------------------------------------------------------------
# when run vtags.py, create a folder named vtag.db at current dir
# and also rm the old vtags_db.log if exist.
#-------------------------------------------------------------------------------
vtags_db_folder_path = os.getcwd() + '/vtags.db'

#-------------------------------------------------------------------------------
# import lib used in generate vtags.db
#-------------------------------------------------------------------------------
# add install dir path to python search path, to import all the needed python module
sys.path.insert(0,vtags_install_path)
# import the module used to generate vtags.db database
import Lib.GLB as GLB
G = GLB.G
GLB.vtags_db_log_path[0] = vtags_db_folder_path + '/vtags_db.log'
from Lib.BaseLib import *
import Lib.FileInfLib as FileInfLib

#-------------------------------------------------------------------------------
# print help information
#-------------------------------------------------------------------------------
if help in ['-h','-help']:
    help_str_list = []
    help_str_list.append("(1) generate vtags at code dir, use command \"vtags\" or \"vtags -f folder_list\";"          )
    help_str_list.append("(2) config vtags vim at vtags gen dir \"/vtags.db/vim_local_config.py\","                    )
    help_str_list.append("    config items and detail look vim_local_config.py notes;"                                 )
    help_str_list.append("(3) support action in vim window:"                                                           )
    help_str_list.append("        1)  mt             : print the module trace from top module;"                        )
    help_str_list.append("        2)  gi             : if cursor on module call, go in submodule;"                     )
    help_str_list.append("        3)  gu             : if cur module called before, go upper module;"                  )
    help_str_list.append("        4)  <Space><Left>  : trace cursor word signal source;"                               )
    help_str_list.append("        5)  <Space><Right> : trace cursor word signal dest;"                                 )
    help_str_list.append("        6)  <Space><Down>  : roll back;"                                                     )
    help_str_list.append("        7)  <Space><Up>    : go forward;"                                                    )
    help_str_list.append("        8)  <Space>v       : show current module topo "                                      )
    help_str_list.append("                             or fold/unfold sidebar items;"                                  )
    help_str_list.append("        9)  <Space>c       : add current cursor as checkpoint, can go back directly;"        )
    help_str_list.append("        10)  <Space>b      : add current cursor module as basemodule, not show in topo;"     )
    help_str_list.append("        11) <Space>        : in sidebar or report win, just go cursor line link;"            )
    help_str_list.append("        12) <Space>h       : hold cursor win, will not auto close it;"                       )
    help_str_list.append("        13) <Space>d       : in sidebar, delete valid items(base_module, checkpoint...);"    )
    help_str_list.append("        14) <Space>s       : save current vim snapshort,"                                    )
    help_str_list.append("                             use \"gvim/vim\" without input file to reload snapshort;"       )
    help_str_list += OfflineFuncLib.offline_func_help()
    MountPrintLines(help_str_list, label = 'Vtags Help', Print = True)
    exit()

# special warning for case only use default 'v' as postfix
if len(G['SupportVerilogPostfix']) == 1 and 'v' in G['SupportVerilogPostfix']:
    warning_line_list = []
    warning_line_list.append('Default config only treat "xxx.v" as verilog design files.')
    warning_line_list.append('If you have other valid postfix please add it to :')
    warning_line_list.append('  vtags.db/vim_local_config.py   : support_verilog_postfix= [...] (only change local config)')
    warning_line_list.append('  or')
    warning_line_list.append('  vtags-2.xx/vim_local_config.py : support_verilog_postfix= [...] (change global config)')
    warning_line_list.append('Such as:')
    warning_line_list.append('  support_verilog_postfix= [\'v\', \'V\', \'d\'] // add xxx.V, xxx.d as valid verilog design files' )
    MountPrintLines(warning_line_list, label = 'Add Support Postfix', Print = True)
    print('')

#-------------------------------------------------------------------------------
# when run vtags.py, create a folder named vtag.db at current dir
# and also rm the old vtags_db.log if exist.
#-------------------------------------------------------------------------------
os.system('mkdir -p %s'%(vtags_db_folder_path))
if os.path.isfile(vtags_db_folder_path + '/vtags_db.log'):
    os.system('rm -rf '+vtags_db_folder_path+'/vtags_db.log')

#-------------------------------------------------------------------------------
# filelist support
#-------------------------------------------------------------------------------
# current vtags.db real_filelist
vtags_file_list     = vtags_db_folder_path + '/design.filelist'
filelist_filehandle = open(vtags_file_list, 'w')

file_list = ''
try:
    if sys.argv[1] == '-f':
        file_list = sys.argv[2].strip()
except:
    pass

# for each dir in the filelist, try to add a vtags.db soft link to current dir's real vtags.db
if file_list:
    if not os.path.isfile(file_list): # if file_list not exist just exit
        print("Error: filelist: %s not exist !"%(file_list))
        exit(1)
    else: # if file_list exist, try to add vtags.db's soft ln for each dir
        dir_in_filelist = []
        file_in_filelist = []
        for f in open(file_list, 'r').readlines():
            f = re.sub('//.*','', f).strip()
            # get all dir for print
            if os.path.isdir(f):
                dir_in_filelist.append(f)
            elif os.path.isfile(f):
                file_in_filelist.append(f)
        # if has filelist must has some value file or dir
        if not dir_in_filelist + file_in_filelist:
            print('Error: no valid file or dir in current filelist: %s'%(filelist))
            exit(1)
        # else generate vtags used abs filelist
        for f in dir_in_filelist + file_in_filelist:
            filelist_filehandle.write( os.path.realpath(f) + '\n')
        filelist_filehandle.close()
        # if has dir in file list need give warning to generate ln manully
        line_list = []
        line_list.append('Generated "vtags.db" put in current dir(./)                                  ')
        line_list.append('If you want active vtags in other folders in filelist, you need add soft link')
        line_list.append('manually.                                                                    ')
        line_list.append('Folders in filelist:                                                         ')
        for d in dir_in_filelist:
            line_list.append('  %s'%(d))
        line_list.append('Such as:')
        for d in dir_in_filelist:
            line_list.append('  ln -s ./vtags.db %s'%(d))
        MountPrintLines(line_list, label = 'TAKE CARE', Print = True)
else:
    print("Note: no filelist, create vtags.db for current dir !")
    filelist_filehandle.write( os.path.realpath( os.getcwd() ) + '\n')
    filelist_filehandle.close()


#-------------------------------------------------------------------------------
# get all the verilog file code inf
#-------------------------------------------------------------------------------
# get all verilog files path from file_list
design_file_path_set      = FileInfLib.get_all_design_file_path_from_filelist(vtags_file_list)

# get all code inf
file_path_to_code_inf_dic = FileInfLib.init_get_file_path_to_code_inf_dic(design_file_path_set)


#-------------------------------------------------------------------------------
# add more inf to module_inf, subcall_inf, macro_inf
#-------------------------------------------------------------------------------
module_name_to_file_path_list_dic = {}
file_path_to_last_modify_time_dic = {}
for f in file_path_to_code_inf_dic:
    file_path_to_last_modify_time_dic[f] = file_path_to_code_inf_dic[f]['last_modify_time']
    module_inf_list = file_path_to_code_inf_dic[f]['module_inf_list'  ]
    for module_inf in module_inf_list:
        module_name_to_file_path_list_dic.setdefault(module_inf['module_name'],[])
        module_name_to_file_path_list_dic[ module_inf['module_name'] ].append(f)

macro_name_to_macro_inf_list_dic = {}
for f in file_path_to_code_inf_dic:
    macro_inf_list = file_path_to_code_inf_dic[f]['macro_inf_list']
    for macro_inf in macro_inf_list:
        macro_name_to_macro_inf_list_dic.setdefault(macro_inf['macro_name'],[])
        macro_name_to_macro_inf_list_dic[macro_inf['macro_name']].append(macro_inf)

#-------------------------------------------------------------------------------
# set base module
#-------------------------------------------------------------------------------
all_basemodule_name_set_pkl_path = vtags_db_folder_path+'/pickle/all_basemodule_name_set.pkl'
all_basemodule_name_set      = set()
masked_call_me_submodule_set = set()
# if not os.path.isfile(all_basemodule_name_set_pkl_path):
add_upper_threshold     = G['CallMeSubcallInf']['AddUpperThreshold']
base_threshold          = G['BaseModuleInf']['BaseModuleThreshold']
# first get all module instance number, if instance number bigger than base_threshold
# tread corresponding module as base module
module_name_to_instance_num_dic  = {}
for f in file_path_to_code_inf_dic:
    subcall_inf_list = file_path_to_code_inf_dic[f]['subcall_inf_list']
    for subcall in subcall_inf_list:
        submodule_name = subcall['submodule_name']
        module_name_to_instance_num_dic.setdefault(submodule_name,0)
        module_name_to_instance_num_dic[submodule_name] += 1
# check if beyond the base_threshold
for module_name in module_name_to_instance_num_dic:
    if ( not os.path.isfile(all_basemodule_name_set_pkl_path) )and \
       ( module_name_to_instance_num_dic[module_name] >= base_threshold) :
        all_basemodule_name_set.add(module_name)
    if module_name_to_instance_num_dic[module_name] > add_upper_threshold:
        masked_call_me_submodule_set.add(module_name)

#-------------------------------------------------------------------------------
# generate module_name_to_call_me_subcall_inf_list_dic
#-------------------------------------------------------------------------------
module_name_to_call_me_subcall_inf_list_dic = {}
for f in file_path_to_code_inf_dic:
    subcall_inf_list = file_path_to_code_inf_dic[f]['subcall_inf_list']
    for subcall_inf in subcall_inf_list:
        submodule_name = subcall_inf['submodule_name']
        if submodule_name not in masked_call_me_submodule_set:
            module_name_to_call_me_subcall_inf_list_dic.setdefault(submodule_name, []).append( subcall_inf )

#-------------------------------------------------------------------------------
# pickle
#-------------------------------------------------------------------------------
os.system('mkdir -p %s'%(vtags_db_folder_path+'/pickle'))
# 1 pickle file_list,file_path_to_last_modify_time_dic or refresh vtags.db
vtags_db_refresh_inf = {
     'file_list'                         : vtags_file_list
    ,'file_path_to_last_modify_time_dic' : file_path_to_last_modify_time_dic
}
vtags_db_refresh_inf_pkl_path = vtags_db_folder_path+'/pickle/vtags_db_refresh_inf.pkl'
pickle_save(vtags_db_refresh_inf, vtags_db_refresh_inf_pkl_path)
# 2 pickle module_name_to_file_path_list_dic, for refresh single file subcall_inf
module_name_to_file_path_list_dic_pkl_path = vtags_db_folder_path+'/pickle/module_name_to_file_path_list_dic.pkl'
pickle_save(module_name_to_file_path_list_dic, module_name_to_file_path_list_dic_pkl_path)
# 3 pick all macro inf
macro_name_to_macro_inf_list_dic_pkl_path = vtags_db_folder_path+'/pickle/macro_name_to_macro_inf_list_dic.pkl'
pickle_save(macro_name_to_macro_inf_list_dic, macro_name_to_macro_inf_list_dic_pkl_path)
# 4 pick file_path_to_code_inf_dic
# pick save all f inf
for f in file_path_to_code_inf_dic:
    code_inf = file_path_to_code_inf_dic[f]
    del code_inf['macro_inf_list']
    code_inf_pkl_path = vtags_db_folder_path+'/pickle/design__%s.pkl'%(f.replace('/','__'))
    pickle_save(code_inf, FileInfLib.get_shortpath(code_inf_pkl_path, create = True) )
pickle_save(G["Short2RealPathMap"], vtags_db_folder_path+'/pickle/short_to_real_path_map.pkl')

# 5 used pickle save base module inf
if not os.path.isfile(all_basemodule_name_set_pkl_path):
    pickle_save(all_basemodule_name_set, all_basemodule_name_set_pkl_path)
# 6 pickle save call me subcall inf dic
call_me_subcall_inf = {
     'ModuleNameToCallMeSubcallInfListDic' : module_name_to_call_me_subcall_inf_list_dic
    ,'MaskedCallMeSubmoduleSet'            : masked_call_me_submodule_set
}
pickle_save(call_me_subcall_inf, vtags_db_folder_path+'/pickle/call_me_subcall_inf.pkl')


#-------------------------------------------------------------------------------
# copy glable config to vtags.db to generate local config if no local config
#-------------------------------------------------------------------------------
if not os.path.isfile(vtags_db_folder_path + '/vim_local_config.py'):
    os.system('cp %s/vim_glb_config.py %s/vim_local_config.py'%(vtags_install_path, vtags_db_folder_path))
