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
import os
import re
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
from InlineLib.ViewLib import *

def get_shortpath(real_path, create = False):
    path_split = real_path.split('/')
    file_name  = path_split[-1]
    # if file name length is ok just return
    if len(file_name) < G["MaxFileNameLength"]:
        return real_path
    # file name length is to long reduce it
    #    init map if not
    Short2RealPathMap = G["Short2RealPathMap"]
    Real2ShortPathMap = G["Real2ShortPathMap"]
    if Short2RealPathMap == None: # means not initial, try to initial it from pickle file
        Short2RealPathMap = pickle_reload(G['VTagsPath']+'/pickle/short_to_real_path_map.pkl')
        if Short2RealPathMap == None: # if still None means no pkl file, just inital it to empty
            Short2RealPathMap = {}
        # get all reduced path
        for sp in Short2RealPathMap:
            assert( Short2RealPathMap[sp] not in Real2ShortPathMap )
            Real2ShortPathMap[ Short2RealPathMap[sp] ] = sp
        G["Short2RealPathMap"] = Short2RealPathMap
        G["Real2ShortPathMap"] = Real2ShortPathMap
    #   if path already exist return sort path
    if real_path in Real2ShortPathMap:
        return Real2ShortPathMap[real_path]
    #   generate short path name
    if create == True:
        path_split[-1] = "SortPath_%s.pkl"%(len(Short2RealPathMap))
        short_path = '/'.join( path_split )
        Short2RealPathMap[ short_path ] = real_path
        Real2ShortPathMap[ real_path ] = short_path
        return short_path
    else:
        # assert(0), "not create new map, path should has match !"
        return ''

# if has file_list : get all the design file path from filelist
# else  get all design file from current folder
def get_all_design_file_path_from_filelist(file_list = ''):
    # get all the dir_path and file_path from file_list
    file_or_dir_path_set = set()
    if file_list:
        assert(os.path.isfile(file_list)),'Error: filelist: %s , not exist !'%(file_list)
        file_or_dir_path_list_raw = open(file_list, 'r').readlines()
        for l in file_or_dir_path_list_raw:
            l = (l.split('//')[0]).strip()
            if l != '':
                file_or_dir_path_set.add(l)
    else:
        cur_dir_path  = os.getcwd()
        file_or_dir_path_set.add(cur_dir_path)
    # get design file from dir_path and file path, and updata design postfix through file in filelist
    # pyhon not recognize "~" as home dir, need change "~" to abs home path
    # get the abs home path
    home_path = os.popen('echo ~').readlines()[0].rstrip('\n').rstrip('/')
    # for each line in file_or_dir_path_set, to get all the verilog files supported
    # get all the verilog files path
    # (1) add all the file path to file list and add corresponding postfix to verilog
    #     supported postfix
    # (2) add all the dir path the dir_path_set
    # (3) save all the postfix, new updated
    # (4) for each dir path , find all the verilog files
    file_path_set = set()
    dir_path_set  = set()
    add_postfix   = False
    for file_or_dir_path in file_or_dir_path_set:
        file_or_dir_path = re.sub('^~', home_path, file_or_dir_path)
        if re.match('\s*$',file_or_dir_path):
            continue
        if os.path.isdir(file_or_dir_path):    # step (2)
            # need change to abs path first
            dir_path_set.add(os.path.realpath(file_or_dir_path))
        elif os.path.isfile(file_or_dir_path): # step (1)
            file_path_set.add(os.path.realpath(file_or_dir_path))
            cur_file_postfix = get_file_path_postfix(file_or_dir_path)
            if not cur_file_postfix:
                continue
            if cur_file_postfix not in G['SupportVerilogPostfix']:
                G['SupportVerilogPostfix'].add(cur_file_postfix)
                add_postfix = True
    # step 3
    if add_postfix:
        pkl_output = open(G['VTagsPath'] + '/file_list_postfix.pkl','wb')
        pickle.dump(G['SupportVerilogPostfix'], pkl_output)
        pkl_output.close()
    # step 4
    postfix_patten = '|'.join(list(G['SupportVerilogPostfix']))
    for dir_path in dir_path_set:
        # cur_dir_all_files   = os.popen('find ' + dir_path + ' -type f 2>/dev/null').readlines()
        #cur_dir_all_files    = os.popen('find %s -type f 2>/dev/null | egrep "\.(%s)$"'%(dir_path,postfix_patten)).readlines()
        cur_dir_all_files    = os.popen('find %s -path \'*vtags.db\' -a -prune -o -type f 2>/dev/null | egrep "\.(%s)$"'%(dir_path,postfix_patten)).readlines()
        cur_dir_all_files    = [ d_l.rstrip('\n') for d_l in cur_dir_all_files ]
        for f in cur_dir_all_files:
            assert(get_file_path_postfix(f) in G['SupportVerilogPostfix']),'%s'%(f)
            file_path_set.add(f)
    return file_path_set


# this function used get all the files's verilog code_inf
# return is a dic, key is the file_path in paths, 
def init_get_file_path_to_code_inf_dic(paths):
    # step 1/2 get all module/define inf
    file_path_to_module_inf_dic   = {}
    file_path_to_macro_define_dic = {}
    all_module_name_set           = set() # a set of all the module names finded in design
    print('step 1/2:')
    for i,f in enumerate(paths):
        show_progress_bar( i, len(paths))
        PrintDebug(f)
        # gen cur module and define inf
        # cur_file_module_inf is a list of module_inf ordered by appeared line num in file
        # module_inf = { 'module_name'            : ''
        #               ,'module_line_range'      : ()
        #               ,'module_name_match_pos'  : () 
        #               -------------------------------------------
        #               ,'file_path'                   : ''        # set when add to G['ModuleNameToModuleInfListDic']
        #               ,'subcall_instance_list'       : None      # [subcall_inf,...] set when first open topo
        #               ,'instance_to_subcall_inf_dic' : None      # add one by one when used
        #              }
        cur_file_module_inf = get_single_verilog_file_module_inf(f)
        # cur_file_macro_inf is a list of macro_inf ordered by appeared line num in file
        # macro_inf = { "macro_name"              : ''
        #              ,"macro_name_match_pos"    : (line_num, colum_num)  # name first char pos
        #              ,'code_line'               : `define xxx ....}
        #               -------------------------------------------
        #              ,"file_path"               : ''  # no needed
        cur_file_macro_inf  = get_single_verilog_file_macro_define_inf(f)
        # add to result
        file_path_to_module_inf_dic[f]   = cur_file_module_inf
        file_path_to_macro_define_dic[f] = cur_file_macro_inf
        all_module_name_set              = all_module_name_set | set([ mi['module_name'] for mi in cur_file_module_inf])
    print('')
    # step 2/2 get all file sub call inf
    file_path_to_subcall_inf_dic = {}
    patten = get_submodule_match_patten(all_module_name_set)
    print('step 2/2:')
    for i,f in enumerate(paths):
        PrintDebug(f)
        show_progress_bar( i, len(paths))
        # get_single_verilog_file_subcall_inf return a list of subcall_inf ordered by appeared line num in file
        # subcall_inf = { 'submodule_name'           : ''
        #                 'instance_name'            : ''
        #                 'subcall_line_range'       : ()
        #                 'submodule_name_match_pos' : () }
        file_path_to_subcall_inf_dic[f] = get_single_verilog_file_subcall_inf(f, patten, all_module_name_set, file_path_to_module_inf_dic[f])
    print('')
    # merge to file_path_to_code_inf_dic
    # file_inf = { 'macro_inf_list'   : [] # list of macro_inf
    #             ,'module_inf_list'  : [] # list of module_inf
    #             ,'subcall_inf_list' : [] # list of subcall_inf
    #             ,'last_modify_time' : os.path.getmtime(f) }
    file_path_to_code_inf_dic = {}
    for f in paths:
        file_path_to_code_inf_dic[f] = { 
             'module_inf_list'  : file_path_to_module_inf_dic[f]   # list of module_inf
            ,'macro_inf_list'   : file_path_to_macro_define_dic[f] # list of macro_inf
            ,'subcall_inf_list' : file_path_to_subcall_inf_dic[f]  # list of subcall_inf
            ,'last_modify_time' : os.path.getmtime(f) }
    return file_path_to_code_inf_dic


# this function used to get current line inf from file_inf
# if current line in module, return module_inf
# if current line in submodule, return subcall_inf
def get_file_line_inf(line_num, path):
    updata_file_inf(path)
    if path not in G['FileInf']:
        PrintDebug('Trace: get_file_line_inf: %s has no file database !'%(path) )
        return False
    assert(G['FileInf'][path]['last_modify_time'] == os.path.getmtime(path))
    return get_line_inf_from_cur_file_inf( line_num, G['FileInf'][path] )


# use this function to get the module inf from module name
def get_module_inf(module_name, report_level = 1):
    # if module in G['ModuleNameToModuleInfListDic']
    if module_name in G['ModuleNameToModuleInfListDic']:
        # del stale inf
        i = 0
        while i < len(G['ModuleNameToModuleInfListDic'][module_name]):
            t_module_inf = G['ModuleNameToModuleInfListDic'][module_name][i]
            if not check_inf_valid(t_module_inf['file_path'], t_module_inf['last_modify_time']):
                del G['ModuleNameToModuleInfListDic'][module_name][i]
                continue
            i += 1
        # if has multi valid module define print report
        if len(G['ModuleNameToModuleInfListDic'][module_name]) > 1:
            # PrintReport('Warning: module:%s has %d define ! choise first  of %s '%(module_name, len(G['ModuleNameToModuleInfListDic']), [ module_inf['file_path'] + ':' + str(module_inf['module_line_range'][0]+1) for module_inf in G['ModuleNameToModuleInfListDic'] ] ))
            PrintReport('Warning: module:%s has %d define ! choise first  of %s '%(module_name, len(G['ModuleNameToModuleInfListDic'][module_name]), [ module_inf['file_path'] + ':' + str(module_inf['module_line_range'][0]+1) for module_inf in G['ModuleNameToModuleInfListDic'][module_name] ] ))
        # return a valid module inf
        if len(G['ModuleNameToModuleInfListDic'][module_name]) > 0:
            return G['ModuleNameToModuleInfListDic'][module_name][0]
    # no valid module inf in G, updata module path one by one
    onload_G_ModuleNameToFilePathListDic()
    changed_ModuleNameToFilePathListDic = False
    i = 0
    while (module_name in G['ModuleNameToFilePathListDic']) and ( i < len(G['ModuleNameToFilePathListDic'][module_name]) ):
        t_path = G['ModuleNameToFilePathListDic'][module_name][i]
        updata_file_inf(t_path)
        if (module_name in G['ModuleNameToModuleInfListDic']) and len(G['ModuleNameToModuleInfListDic'][module_name]) > 0:
            break
        # still not get module_inf, then this path is stale, del it
        del G['ModuleNameToFilePathListDic'][module_name][i]
        changed_ModuleNameToFilePathListDic = True
    if changed_ModuleNameToFilePathListDic:
        module_name_to_file_path_list_dic_pkl_path = G['VTagsPath']+'/pickle/module_name_to_file_path_list_dic.pkl'
        pickle_save(G['ModuleNameToFilePathListDic'], module_name_to_file_path_list_dic_pkl_path)
    # if has multi valid module define print report
    if (module_name in G['ModuleNameToModuleInfListDic']) and len(G['ModuleNameToModuleInfListDic'][module_name]) > 1:
        # PrintReport('Warning: module:%s has %d define ! choise first  of %s '%(module_name, len(G['ModuleNameToModuleInfListDic']), [ module_inf['file_path'] + ':' + str(module_inf['module_line_range'][0]+1) for module_inf in G['ModuleNameToModuleInfListDic'] ] ))
        PrintReport('Warning: module:%s has %d define ! choise first  of %s '%(module_name, len(G['ModuleNameToModuleInfListDic'][module_name]), [ module_inf['file_path'] + ':' + str(module_inf['module_line_range'][0]+1) for module_inf in G['ModuleNameToModuleInfListDic'][module_name] ] ))
    # return a valid module inf
    if (module_name in G['ModuleNameToModuleInfListDic']) and len(G['ModuleNameToModuleInfListDic'][module_name]) > 0:
        return G['ModuleNameToModuleInfListDic'][module_name][0]
    # get here means not find module_inf at current vtags.db, if config allow refresh vtags.db, do it 
    if G['RefreshDBValid']:
        refresh_vtags_db()
    # if has multi valid module define print report
    if (module_name in G['ModuleNameToModuleInfListDic']) and len(G['ModuleNameToModuleInfListDic'][module_name]) > 1:
        # PrintReport('Warning: module:%s has %d define ! choise first  of %s '%(module_name, len(G['ModuleNameToModuleInfListDic']), [ module_inf['file_path'] + ':' + str(module_inf['module_line_range'][0]+1) for module_inf in G['ModuleNameToModuleInfListDic'] ] ))
        PrintReport('Warning: module:%s has %d define ! choise first  of %s '%(module_name, len(G['ModuleNameToModuleInfListDic'][module_name]), [ module_inf['file_path'] + ':' + str(module_inf['module_line_range'][0]+1) for module_inf in G['ModuleNameToModuleInfListDic'][module_name] ] ))
    # return a valid module inf
    if (module_name in G['ModuleNameToModuleInfListDic']) and len(G['ModuleNameToModuleInfListDic'][module_name]) > 0:
        return G['ModuleNameToModuleInfListDic'][module_name][0]
    PrintReport('Warning: module: %s not found in design !'%(module_name), report_level = report_level )
    return False



#############################################################################################
#-------------------------------------------------------------------------------
# note subcall upper module inf
# this function used to get the last call upper module inf
#-------------------------------------------------------------------------------


# this function used to save last call upper module inf
def set_module_last_call_inf(sub_module_name, upper_module_name, upper_instance_name):
    G['ModuleLastCallInf'][sub_module_name] = { 'upper_module_name': upper_module_name, 'upper_instance_name': upper_instance_name }
# hyperlink action add_module_last_call_action
def add_module_last_call_action(sub_module_name, upper_module_name, upper_instance_name):
    set_module_last_call_inf(sub_module_name, upper_module_name, upper_instance_name)
register_hyperlink_action( add_module_last_call_action, description = 'this link function add module last call' )

def get_module_last_call_inf(module_name):
    if module_name not in G['ModuleLastCallInf']:
        return False
    his_upper_module_name     = G['ModuleLastCallInf'][module_name]['upper_module_name']
    his_upper_instance_name   = G['ModuleLastCallInf'][module_name]['upper_instance_name']
    upper_module_inf          = get_module_inf(his_upper_module_name)
    if not upper_module_inf:
        PrintDebug('Trace: get_module_last_call_inf: history upper module %s not exist now !'%(his_upper_module_name))
        return False
    # to get upper module_to_instance subcall_inf
    if upper_module_inf.setdefault('instance_to_subcall_inf_dic',None) == None:
        assert(module_inf_add_instance_to_subcall_inf_dic(upper_module_inf))
    if his_upper_instance_name not in upper_module_inf['instance_to_subcall_inf_dic']:
        PrintDebug('Trace: get_module_last_call_inf: history instance_name %s not exist now !'%(his_upper_instance_name))
        return False
    subcall_inf = upper_module_inf['instance_to_subcall_inf_dic'][his_upper_instance_name]
    return {'upper_module_inf': upper_module_inf, 'upper_subcall_inf': subcall_inf}

# this function used line range to get current module's subcall list
def get_the_subcall_instance_list(module_line_range, module_file_subcall_order_list):
    subcall_instance_list = []
    for subcall_inf in module_file_subcall_order_list:
        subcall_line_range = subcall_inf['subcall_line_range']
        if subcall_line_range[1] < module_line_range[0]:
            continue
        if subcall_line_range[0] > module_line_range[1]:
            break
        assert( module_line_range[0] <= subcall_line_range[0] and subcall_line_range[1] <= module_line_range[1] )
        subcall_instance_list.append(subcall_inf)
    return subcall_instance_list

# this function add subcall_instance_list to module_inf
def module_inf_add_subcall_instance_list(module_inf):
    module_line_range = module_inf['module_line_range']
    module_file_path  = module_inf['file_path']
    assert(module_file_path in G['FileInf'])
    module_file_subcall_order_list = G['FileInf'][module_file_path]['subcall_inf_list']
    subcall_instance_list = get_the_subcall_instance_list(module_line_range, module_file_subcall_order_list)
    module_inf['subcall_instance_list'] = subcall_instance_list
    # check old subcall inf the same with new vtags edition 
    if G['Debug']:
        for subcall_inf in module_inf['subcall_instance_list']:
            assert( subcall_inf['cur_module_name'] == module_inf['module_name'] ),'%s'%(subcall_inf.__str__())
    return True

# this function add instance_to_subcall_inf_dic to module_inf
def module_inf_add_instance_to_subcall_inf_dic(module_inf):
    if module_inf.setdefault('subcall_instance_list',None) == None :
        assert(module_inf_add_subcall_instance_list(module_inf))
    instance_to_subcall_inf_dic = {}
    for subcall_inf in module_inf['subcall_instance_list']:
        if subcall_inf['instance_name'] in instance_to_subcall_inf_dic:
            PrintDebug('Warning: instance name "%s" used multi times, in module:%s, file: %s'%(subcall_inf['instance_name'], module_inf['module_name'], module_inf['file_path'] ))
        instance_to_subcall_inf_dic[subcall_inf['instance_name']] = subcall_inf
    module_inf['instance_to_subcall_inf_dic'] = instance_to_subcall_inf_dic
    return True


def refresh_vtags_db():
    # 1. get the refresh vtags db inf
    vtags_db_refresh_inf_pkl_path = G['VTagsPath']+'/pickle/vtags_db_refresh_inf.pkl'
    vtags_db_refresh_inf = pickle_reload(vtags_db_refresh_inf_pkl_path)
    if not vtags_db_refresh_inf:
        PrintDebug('Error: no filelist found in current dir, can not refresh !')
        return False
    print(' refreshing design database ... ')
    file_list = vtags_db_refresh_inf['file_list']
    file_path_to_last_modify_time_dic = vtags_db_refresh_inf['file_path_to_last_modify_time_dic']
    # 2 get current all design file
    old_design_file_path_set = set(file_path_to_last_modify_time_dic)
    cur_design_file_path_set = get_all_design_file_path_from_filelist(file_list)
    # 3. for file current del, rm corresponding inf
    deled_file_path_set = old_design_file_path_set - cur_design_file_path_set
    changed_vtags_db_refresh_inf = False
    for file_path in deled_file_path_set:
        file_pkl_path = get_shortpath( G['VTagsPath']+'/pickle/design__%s.pkl'%(file_path.replace('/','__')), create = False )
        if os.path.isfile(file_pkl_path):
            os.system('rm -f %s'%(file_pkl_path))
        del file_path_to_last_modify_time_dic[file_path]
        changed_vtags_db_refresh_inf = True
    # 4. get stale file and new add file
    stale_and_new_file_path_set = set()
    for file_path in cur_design_file_path_set:
        if file_path in file_path_to_last_modify_time_dic:
            last_modify_time = file_path_to_last_modify_time_dic[file_path]
            if check_inf_valid(file_path, last_modify_time):
                continue
        stale_and_new_file_path_set.add(file_path)
    # 5 for each stale file and new add file
    if not stale_and_new_file_path_set:
        if changed_vtags_db_refresh_inf:
            vtags_db_refresh_inf = {
                 'file_list'                         : file_list
                ,'file_path_to_last_modify_time_dic' : file_path_to_last_modify_time_dic }
            vtags_db_refresh_inf_pkl_path = G['VTagsPath']+'/pickle/vtags_db_refresh_inf.pkl'
            pickle_save(vtags_db_refresh_inf, vtags_db_refresh_inf_pkl_path)
        return True
    changed_ModuleNameToFilePathListDic = False
    changed_MacroNameToMacroInfListDic  = False
    onload_G_ModuleNameToFilePathListDic()
    file_path_to_code_inf_dic = get_file_path_to_code_inf_dic(stale_and_new_file_path_set, set(G['ModuleNameToFilePathListDic']))
    merge_subcall_inf_list    = []
    for f in file_path_to_code_inf_dic:
        # updata path last modify time
        file_path_to_last_modify_time_dic[f] = file_path_to_code_inf_dic[f]['last_modify_time']
        # updata module_name to file path dic
        module_inf_list = file_path_to_code_inf_dic[f]['module_inf_list'  ]
        for module_inf in module_inf_list:
            add_ModuleNameToModuleInfListDic(module_inf)
            if add_ModuleNameToFilePathListDic(module_inf):
                changed_ModuleNameToFilePathListDic = True
        # updata macro
        macro_inf_list = file_path_to_code_inf_dic[f]['macro_inf_list']
        for macro_inf in macro_inf_list:
            add_MacroNameToMacroInfListDic(macro_inf)
            changed_MacroNameToMacroInfListDic = True
        # updata code_inf
        del file_path_to_code_inf_dic[f]['macro_inf_list']
        G['FileInf'][f] = file_path_to_code_inf_dic[f]
        # get all subcall inf of new files
        merge_subcall_inf_list += file_path_to_code_inf_dic[f]['subcall_inf_list']
    # 6 update call me subcall inf for all new subcall in cuurent new file
    add_ModuleNameToCallMeSubcallInfListDic( merge_subcall_inf_list )
    # 7 pickle save new inf
    os.system('mkdir -p %s'%(G['VTagsPath']+'/pickle'))
    # 1) pickle file_list,file_path_to_last_modify_time_dic or refresh vtags.db
    vtags_db_refresh_inf = {
         'file_list'                         : file_list
        ,'file_path_to_last_modify_time_dic' : file_path_to_last_modify_time_dic
    }
    vtags_db_refresh_inf_pkl_path = G['VTagsPath']+'/pickle/vtags_db_refresh_inf.pkl'
    pickle_save(vtags_db_refresh_inf, vtags_db_refresh_inf_pkl_path)
    # 2 pickle module_name_to_file_path_list_dic, for refresh single file subcall_inf
    if changed_ModuleNameToFilePathListDic:
        module_name_to_file_path_list_dic_pkl_path = G['VTagsPath']+'/pickle/module_name_to_file_path_list_dic.pkl'
        pickle_save(G['ModuleNameToFilePathListDic'], module_name_to_file_path_list_dic_pkl_path)
    # 3 pick all macro inf
    if changed_MacroNameToMacroInfListDic:
        macro_name_to_macro_inf_list_dic_pkl_path = G['VTagsPath']+'/pickle/macro_name_to_macro_inf_list_dic.pkl'
        pickle_save(G['MacroNameToMacroInfListDic'], macro_name_to_macro_inf_list_dic_pkl_path)
    # 4 pick file_path_to_code_inf_dic
    # pick save all f inf
    for f in file_path_to_code_inf_dic:
        code_inf = file_path_to_code_inf_dic[f]
        code_inf_pkl_path = G['VTagsPath']+'/pickle/design__%s.pkl'%(f.replace('/','__'))
        pickle_save(code_inf, get_shortpath( code_inf_pkl_path, creat = True) )
    pickle_save(G["Short2RealPathMap"], G['VTagsPath']+'/pickle/short_to_real_path_map.pkl')
    return True

def add_ModuleNameToModuleInfListDic( module_inf ):
    module_name = module_inf['module_name']
    G['ModuleNameToModuleInfListDic'].setdefault(module_name,[])
    # del old
    i = 0
    while i < len(G['ModuleNameToModuleInfListDic'][module_name]):
        t_module_inf = G['ModuleNameToModuleInfListDic'][module_name][i]
        if not check_inf_valid(t_module_inf['file_path'], t_module_inf['last_modify_time']):
            del G['ModuleNameToModuleInfListDic'][module_name][i]
            continue
        else: 
            # already has newest module inf, if they are same with new add, just del old
            # add module_name_match_pos incase same module has multi define of same module_name
            if (t_module_inf['file_path'], t_module_inf['module_name'], t_module_inf['module_name_match_pos']) == \
                (module_inf['file_path'], module_inf['module_name'], module_inf['module_name_match_pos']):
                del G['ModuleNameToModuleInfListDic'][module_name][i]
                continue
        i += 1
    # add new
    G['ModuleNameToModuleInfListDic'][module_name].append(module_inf) 

def add_ModuleNameToFilePathListDic(module_inf):
    real_added = False
    onload_G_ModuleNameToFilePathListDic()
    module_name = module_inf['module_name']
    module_path = module_inf['file_path']
    G['ModuleNameToFilePathListDic'].setdefault(module_name,[])
    if module_path not in G['ModuleNameToFilePathListDic'][module_name]:
        G['ModuleNameToFilePathListDic'][ module_name ].append(module_path)
        real_added = True
    return real_added

def add_MacroNameToMacroInfListDic(macro_inf):
    onload_G_MacroNameToMacroInfListDic()
    macro_name = macro_inf['macro_name']
    G['MacroNameToMacroInfListDic'].setdefault(macro_name,[])
    # del old
    i = 0
    while i < len(G['MacroNameToMacroInfListDic'][macro_name]):
        t_macro_inf = G['MacroNameToMacroInfListDic'][macro_name][i]
        if not check_inf_valid(t_macro_inf['file_path'], t_macro_inf['last_modify_time']):
            del G['MacroNameToMacroInfListDic'][macro_name][i]
            continue
        i += 1
    G['MacroNameToMacroInfListDic'][macro_name].append(macro_inf)


def get_file_path_to_code_inf_dic(paths, all_module_name_set):
    # step 1/2 get all module/define inf
    file_path_to_module_inf_dic   = {}
    file_path_to_macro_define_dic = {}
    # print('step 1/2:')
    for i,f in enumerate(paths):
        # show_progress_bar( i, len(paths))
        # PrintDebug(f)
        # gen cur module and define inf
        # cur_file_module_inf is a list of module_inf ordered by appeared line num in file
        # module_inf = { 'module_name'            : ''
        #               ,'module_line_range'      : ()
        #               ,'module_name_match_pos'  : () 
        #               -------------------------------------------
        #               ,'file_path'                   : ''        # set when add to G['ModuleNameToModuleInfListDic']
        #               ,'subcall_instance_list'       : None      # [subcall_inf,...] set when first open topo
        #               ,'instance_to_subcall_inf_dic' : None      # add one by one when used
        #              }
        cur_file_module_inf = get_single_verilog_file_module_inf(f)
        # cur_file_macro_inf is a list of macro_inf ordered by appeared line num in file
        # macro_inf = { "macro_name"              : ''
        #              ,"macro_name_match_pos"    : (line_num, colum_num)  # name first char pos
        #              ,'code_line'               : `define xxx ....}
        #               -------------------------------------------
        #              ,"file_path"               : ''  # no needed
        cur_file_macro_inf  = get_single_verilog_file_macro_define_inf(f)
        # add to result
        file_path_to_module_inf_dic[f]   = cur_file_module_inf
        file_path_to_macro_define_dic[f] = cur_file_macro_inf
        all_module_name_set              = all_module_name_set | set([ mi['module_name'] for mi in cur_file_module_inf])
    # print('')
    # step 2/2 get all file sub call inf
    file_path_to_subcall_inf_dic = {}
    patten = get_submodule_match_patten(all_module_name_set)
    # print('step 2/2:')
    for i,f in enumerate(paths):
        # PrintDebug(f)
        # show_progress_bar( i, len(paths))
        # get_single_verilog_file_subcall_inf return a list of subcall_inf ordered by appeared line num in file
        # subcall_inf = { 'submodule_name'           : ''
        #                 'instance_name'            : ''
        #                 'subcall_line_range'       : ()
        #                 'submodule_name_match_pos' : () }
        file_path_to_subcall_inf_dic[f] = get_single_verilog_file_subcall_inf(f, patten, all_module_name_set, file_path_to_module_inf_dic[f])
    # print('')
    # merge to file_path_to_code_inf_dic
    # file_inf = { 'macro_inf_list'   : [] # list of macro_inf
    #             ,'module_inf_list'  : [] # list of module_inf
    #             ,'subcall_inf_list' : [] # list of subcall_inf
    #             ,'last_modify_time' : os.path.getmtime(f) }
    file_path_to_code_inf_dic = {}
    for f in paths:
        file_path_to_code_inf_dic[f] = { 
             'module_inf_list'  : file_path_to_module_inf_dic[f]   # list of module_inf
            ,'macro_inf_list'   : file_path_to_macro_define_dic[f] # list of macro_inf
            ,'subcall_inf_list' : file_path_to_subcall_inf_dic[f]  # list of subcall_inf
            ,'last_modify_time' : os.path.getmtime(f) }
    return file_path_to_code_inf_dic


# this function get the line inf from file_inf
# if line in module, return module_inf
# if line is subcall, return subcall_inf
def get_line_inf_from_cur_file_inf(line_num, file_inf):
    line_module_inf   = {}
    line_subcall_inf  = {}
    module_inf_list   = file_inf['module_inf_list' ]
    subcall_inf_list  = file_inf['subcall_inf_list']
    # first get current line module inf
    for module_inf in module_inf_list:
        cur_module_line_range = module_inf['module_line_range']
        if cur_module_line_range[1] < line_num:
            continue
        if line_num < cur_module_line_range[0]:
            break
        line_module_inf = module_inf
    # second get current line call sub inf
    for subcall_inf in subcall_inf_list:
        cur_subcall_line_range = subcall_inf['subcall_line_range']
        if cur_subcall_line_range[1] < line_num:
            continue
        if line_num < cur_subcall_line_range[0]:
            break
        line_subcall_inf = subcall_inf
    return  {
         'module_inf'   : line_module_inf
        ,'subcall_inf'  : line_subcall_inf
    }


def updata_file_inf(path):
    # not update for a no verilog file
    if get_file_path_postfix(path) not in G['SupportVerilogPostfix']:
        PrintDebug('Trace: updata_file_pickle_inf: file not verilog file ! file: %s'%(path))
        return False
    # not updata for a non exist file
    if not os.path.isfile(path):
        PrintDebug('Trace: updata_file_pickle_inf: file not exit ! file: %s'%(path))
        if path in G['FileInf']:
            del G['FileInf'][path]
        return False
    # if has not load in G['FileInf'] try get through pickle
    if path not in G['FileInf']:
        PrintDebug('Trace: updata_file_pickle_inf: reload pkl for file: %s'%(path))
        reload_pkl_file_code_inf(path)
    # if load from pickle, check modify time
    if path in G['FileInf']:
        inf_mtime  = G['FileInf'][path]['last_modify_time']
        if check_inf_valid(path, inf_mtime):
            return True
    # if mtime not match, or path no pickle inf, 
    refresh_or_add_new_single_file_code_inf(path)
    return True


# this function used to reload file_inf to G['FileInf'] through pickle
def reload_pkl_file_code_inf(path):
    pkl_path = G['VTagsPath']+'/pickle/design__%s.pkl'%(path.replace('/','__'))
    short_path = get_shortpath(pkl_path, create = False)
    code_inf   = pickle_reload(short_path)
    if code_inf != None:
        G['FileInf'][path] = code_inf
        # updata module_inf module_inf
        new_file_module_inf_list  = code_inf['module_inf_list']
        for module_inf in new_file_module_inf_list:
            add_ModuleNameToModuleInfListDic( module_inf )
        return True
    return False

# when file modified , refresh it 
def refresh_or_add_new_single_file_code_inf(path):
    PrintReport('Note: refresh file: %s !'%(path))
    # not update for a no verilog file
    assert(get_file_path_postfix(path) in G['SupportVerilogPostfix'])
    # not updata for a non exist file
    assert(os.path.isfile(path))
    # get_single_verilog_file_code_inf return
    # file_inf = { 'macro_inf_list'   : [] # list of macro_inf
    #             ,'module_inf_list'  : [] # list of module_inf
    #             ,'subcall_inf_list' : [] # list of subcall_inf
    #             ,'last_modify_time' : os.path.getmtime(f) }
    new_file_code_inf  = get_single_verilog_file_code_inf(path)
    # refresh macro inf
    new_file_macro_inf_list = new_file_code_inf['macro_inf_list']
    if new_file_macro_inf_list:
        for macro_inf in new_file_macro_inf_list:
            add_MacroNameToMacroInfListDic(macro_inf)
        macro_name_to_macro_inf_list_dic_pkl_path = G['VTagsPath']+'/pickle/macro_name_to_macro_inf_list_dic.pkl'
        pickle_save(G['MacroNameToMacroInfListDic'], macro_name_to_macro_inf_list_dic_pkl_path)
    # refresh module_inf
    new_file_module_inf_list  = new_file_code_inf['module_inf_list']
    for module_inf in new_file_module_inf_list:
        add_ModuleNameToModuleInfListDic(module_inf)
    # refresh file_inf
    del new_file_code_inf['macro_inf_list']
    G['FileInf'][path] = new_file_code_inf
    code_inf_pkl_path  = G['VTagsPath']+'/pickle/design__%s.pkl'%(path.replace('/','__'))
    pickle_save(new_file_code_inf, get_shortpath(code_inf_pkl_path, create = True))
    pickle_save(G["Short2RealPathMap"], G['VTagsPath']+'/pickle/short_to_real_path_map.pkl')
    # update call me subcall inf for all new subcall in cuurent new file
    add_ModuleNameToCallMeSubcallInfListDic(new_file_code_inf['subcall_inf_list'])


def get_single_verilog_file_code_inf(f):
    # new_file_module_inf is a list of module_inf ordered by appeared line num in file
    # module_inf = { 'module_name'            : ''
    #               ,'module_line_range'      : ()
    #               ,'sub_modules'            : None  # [] just inst_name and module_name pair set when first use
    #               ,'module_name_match_pos'  : () }
    new_file_module_inf = get_single_verilog_file_module_inf(f)
    # new_file_define_inf is a list of macro_inf ordered by appeared line num in file
    # macro_inf = { "macro_name"              : ''
    #              ,"macro_name_match_pos"    : (line_num, colum_num)  # name first char pos
    #              ,'code_line'               : `define xxx ....}
    new_file_define_inf = get_single_verilog_file_macro_define_inf(f)
    # need get current new all_module_names to generate, subcall patthen
    # gen new all_module_names, just add current file add new, can not del old incase 
    # old module may at other files, on harm for recognize more submodule
    onload_G_ModuleNameToFilePathListDic()
    old_all_module_name_set      = set(G['ModuleNameToFilePathListDic'])
    new_module_names             = set( [ mi['module_name'] for mi in new_file_module_inf ] )
    all_module_name              =  old_all_module_name_set | new_module_names
    # get file sub call inf
    patten = get_submodule_match_patten(all_module_name)
    # new_file_subcall_inf return a list of subcall_inf ordered by appeared line num in file
    # subcall_inf = { 'submodule_name'           : ''
    #                 'instance_name'            : ''
    #                 'subcall_line_range'       : ()
    #                 'submodule_name_match_pos' : () }
    new_file_subcall_inf = get_single_verilog_file_subcall_inf(f, patten, all_module_name, new_file_module_inf)
    # merge to file_inf
    new_file_inf = {
         'module_inf_list'   : new_file_module_inf
        ,'macro_inf_list'    : new_file_define_inf
        ,'subcall_inf_list'  : new_file_subcall_inf
        ,'last_modify_time'  : os.path.getmtime(f)
    }
    return new_file_inf


# current function get all the module define in current file and 
# return a module_inf list
# module_inf =  {  'module_name'            : ''
#                 ,'module_line_range'      : ()
#                 ,'subcall_instance_list'  : None  # [] subcall_inf pair
#                 ,'module_name_match_pos'  : () }
#                 ---------------------------------
#                 ,'file_path'              : ''    # added when put to ModuleNameToModuleInfListDic
def get_single_verilog_file_module_inf(f):
    # get all the module and endmodule line at current file path
    all_module_start_end_lines  = os.popen('egrep -n -h \'^\s*(module|endmodule)\>\' %s'%(f)).readlines()
    cur_file_all_module_inf     = []      # module inf in current file
    has_module_not_end          = False   # has module start and not endmodule yet
    i = 0
    while i < len(all_module_start_end_lines):
        cur_start_end_line      = all_module_start_end_lines[i]
        cur_start_end_line_num  = int(cur_start_end_line.split(':')[0]) - 1
        cur_start_end_line_code = ':'.join( cur_start_end_line.split(':')[1:] )
        match_module_start      = re.match('\s*module\s+(?P<name>(|`)\w+)', cur_start_end_line_code) # some module use macro as name so (|`)
        if match_module_start:
            module_name           = match_module_start.group('name')
            module_start_line_num = cur_start_end_line_num
            module_name_match_pos = ( module_start_line_num, cur_start_end_line_code.find(module_name) )
            # if pre module not end, see if it's used `ifdef define different module io
            # if yes skip the last module define, use the pre one
            # if not set new module start pre line as pre module end line
            if has_module_not_end:
                module_name_not_ended = cur_file_all_module_inf[-1]['module_name']
                # if pre no ended module name the same as cur module name, means use macro define module twice
                # pass current module define
                if module_name_not_ended == module_name:
                    i += 1
                    continue
                # else set new module start pre line as pre module end line
                PrintDebug('Error: module:"%s" in file:"%s", no "endmodule" !'%(cur_file_all_module_inf[-1]['module_name'],f) )
                cur_file_all_module_inf[-1]['module_line_range'][1] = module_start_line_num - 1
                # get end line number, translate to tuple
                cur_file_all_module_inf[-1]['module_line_range']    = tuple(cur_file_all_module_inf[-1]['module_line_range'])
            # add cur line match module to all module inf list
            cur_file_all_module_inf.append(
                {  'module_name'            : module_name
                  ,'module_line_range'      : [module_start_line_num, -1]
                  ,'subcall_instance_list'  : None  # [] just inst_name and module_name pair, set when first use
                  ,'module_name_match_pos'  : module_name_match_pos  
                  ,'file_path'              : f
                  ,'last_modify_time'       : os.path.getmtime(f) } )
            has_module_not_end = True
            i += 1
            continue
        match_module_end  = re.match('\s*endmodule(\W|$)', cur_start_end_line_code)
        if match_module_end:
            if not has_module_not_end:
                PrintDebug( 'Error: line: %s "endmodule" has no correlation module define ! file: %s '%(match_module_end,f) )
                i += 1
                continue
            module_end_line_num = cur_start_end_line_num
            cur_file_all_module_inf[-1]['module_line_range'][1] = module_end_line_num
            # get end line number, translate to tuple
            cur_file_all_module_inf[-1]['module_line_range']    = tuple(cur_file_all_module_inf[-1]['module_line_range'])
            has_module_not_end  = False
            i += 1
            continue
        i += 1
    # if module has no endmodule until file end, treat -1 as module end
    if has_module_not_end:
        PrintDebug( 'Error: module:"%s" in file:"%s", no "endmodule" !'%(cur_file_all_module_inf[-1]['module_name'],f) )
        # get end line number, translate to tuple
        cur_file_all_module_inf[-1]['module_line_range'] = tuple(cur_file_all_module_inf[-1]['module_line_range'])
    return cur_file_all_module_inf


# this function used get all the macro definitions
# return is a list of macro_inf
# macro_inf = {
#     "macro_name"            : ''
#    ,"macro_name_match_pos"  : (line_num, colum_num)  # name first char pos
#    ,'code_line'             : `define xxx .... }
#    ---------------------------------
#    ,"file_path"             : '' # added when in vtags run
def get_single_verilog_file_macro_define_inf(f):
    global_define_inf   = []
    global_define_lines = os.popen('egrep -n -h \'^\s*`define\W\' %s'%(f)).readlines()
    for l in global_define_lines:
        split0     = l.split(':')
        line_num   = int(split0[0]) - 1
        code_line  = ':'.join(split0[1:])
        match_name = re.match('\s*`define\s*(?P<name>\w+)',code_line)
        name       = ''
        colum_num  = -1
        if match_name:
            name      = match_name.group('name')
            colum_num = code_line.find(name)
            global_define_inf.append(
                { 'macro_name'            : name
                 ,'macro_name_match_pos'  : (line_num, colum_num)
                 ,'code_line'             : code_line
                 ,'file_path'             : f
                 ,'last_modify_time'      : os.path.getmtime(f) } )
    return global_define_inf

# this function used to generate match patten used for
# grep quict search , hear can speed up, will do it 
# latter
def get_submodule_match_patten(all_module_name):
    patten_char_set_list = []
    len_2_modules = {}
    # seplate by module_name langth
    for m_n in all_module_name:
        l = len(m_n)
        len_2_modules.setdefault(l,[])
        len_2_modules[l].append(m_n)
    l_pattens = []
    # for different length get seprate match pattens
    for l in len_2_modules:
        l_m = len_2_modules[l]
        l_patten = '(['+ (']['.join(map(''.join, map(set,zip(*l_m))))) + '])'
        l_pattens.append(l_patten)
    patten = '(' + '|'.join(l_pattens) + ')'
    return patten


# this function used to get all the subcall_inf in current files
# return is a list of subcall_inf 
# subcall_inf = { 'submodule_name'           : ''
#                 'instance_name'            : ''
#                 'subcall_line_range'       : ()
#                 'submodule_name_match_pos' : () }
def get_single_verilog_file_subcall_inf(f, patten, all_module_names, module_inf_list):
    # first get all match patten lines
    egrep_match_lines  = os.popen('egrep -n -h \'^\s*(%s)\>\' %s'%(patten,f)).readlines()
    # start get sub call inf
    # if no match return empty list
    if not egrep_match_lines:
        return []
    file_sub_call_infs = []
    # c0/1_cnt is counter used to monitor subcall case used to make speedup decision
    c0_cnt = 0   
    c1_cnt = 0
    # get current file lines
    f_lines = open(f,'r').readlines()
    already_pass_line_num = 0
    for egrep_l in egrep_match_lines:
        egrep_l = egrep_l.strip('\n')
        # get the first word, it maybe the subcall module name, add (|`) because some module name
        # use macro
        match_name = re.match('^(?P<line_num>\d+):(?P<pre_space>\s*)(?P<maybe_submodule_name>(`)?\w+)\s*(?P<post_part>.*)', egrep_l)
        assert(match_name),'%s should lead by a valid words !'%(egrep_l)
        maybe_submodule_name = match_name.group('maybe_submodule_name')
        # if cur name not a right match just go next
        if maybe_submodule_name not in all_module_names:
            continue
        # if is subcall get submodule inf
        cur_submodule_name            = maybe_submodule_name
        # get the submodule_name_match_pos
        cur_submodule_match_line_num  = int( match_name.group('line_num') ) - 1 # minus 1 because egrep line num start from 1
        if cur_submodule_match_line_num < already_pass_line_num:
            PrintDebug('Trace: get_single_verilog_file_subcall_inf : match passed before ! line:%d, file:%s'%(cur_submodule_match_line_num,f))
            continue
        cur_submodule_pre_space_len   = len( match_name.group('pre_space') ) 
        cur_submodule_match_colum_num = cur_submodule_pre_space_len
        submodule_name_match_pos = (cur_submodule_match_line_num,  cur_submodule_match_colum_num)
        #-----------------------
        # get the instance name
        #-----------------------
        cur_submodule_instance_name = ''
        ended_semicolon_line_num    = -1
        # cur_subcall_post_part       = re.sub('(^\s*)|(//.*)', '', match_name.group('post_part'))
        cur_subcall_post_part       = re.sub('//.*', '', match_name.group('post_part'))
        cur_subcall_post_part       = cur_subcall_post_part.strip()
        if cur_subcall_post_part.find(';') != -1: # incase it's one line instance
            ended_semicolon_line_num = cur_submodule_match_line_num
            cur_subcall_post_part = re.sub(';.*','',cur_subcall_post_part)
        # if cur_subcall_post_part is empty add new line until first char not empty
        next_line_index = cur_submodule_match_line_num + 1
        max_line_index  = len(f_lines)
        # for case "module_name #n ... instance_name(...)" for verif code
        if cur_subcall_post_part[0:1] == '#':
            cur_subcall_post_part = (re.sub('#(\d+|`\w+)','',cur_subcall_post_part)).strip()
        while (cur_subcall_post_part == '') and (next_line_index < max_line_index) and (ended_semicolon_line_num == -1):
            # next_code_line = re.sub('(^\s*)|(^\s*`.*)|(//.*)|(\s*$)','',f_lines[next_line_index].strip('\n'))
            # next_code_line = re.sub('(^\s*`.*)|(//.*)','',f_lines[next_line_index].strip('\n'))
            next_code_line = get_valid_code(f_lines[next_line_index].strip('\n'))
            cur_line_index = next_line_index
            next_line_index += 1
            # see if cur subcall ended by cur line
            if next_code_line.find(';') != -1:
                ended_semicolon_line_num = cur_line_index
                next_code_line = re.sub(';.*','',next_code_line)
            # add new line before ";" to cur_subcall_post_part if not ''
            cur_subcall_post_part = next_code_line.strip()
            # for case "module_name #n ... instance_name(...)" for verif code
            if cur_subcall_post_part[0:1] == '#':
                cur_subcall_post_part = (re.sub('#(\d+|`\w+)','',cur_subcall_post_part)).strip()
        # instance_name appear case:
        # case 1: module_name        instance_name ( ... ) ;
        # case 2: module_name #(...) instance_name (...);
        # if cur_subcall_post_part still '', means code has error, not find instance_name untill ";" or file end 
        if cur_subcall_post_part == '':
            PrintDebug('Error: subcall egrep_l : %s in file : %s can not recognized !'%(egrep_l, f))
            continue
        # if is case 2 cur_subcall_post_part[0] must be '#'
        io_connect_init_left_bracket_right_part = None
        # for case 2, first go to the end ")" pos
        # ... #(....)
        #           ^   //get this ")" pos: out_level1_right_bracket_y_list[0]
        if cur_subcall_post_part[0] == '#': # mast be case 2
            # ... #(....)
            #           ^   //get this ")" pos: out_level1_right_bracket_y_list[0]
            current_bracket_depth          = 0
            current_code_line              = cur_subcall_post_part
            bracket_pair_index = get_bracket_pair_index(current_code_line, current_bracket_depth)
            current_bracket_depth            = bracket_pair_index['end_bracket_depth']
            out_level1_right_bracket_y_list  = bracket_pair_index['out_level1_right_bracket_y_list']
            while (not out_level1_right_bracket_y_list) and (ended_semicolon_line_num == -1) and (next_line_index < max_line_index):
                # current_code_line = re.sub('(^\s*`.*)|(//.*)','',f_lines[next_line_index].strip('\n'))
                current_code_line = get_valid_code(f_lines[next_line_index].strip('\n'))
                cur_line_index = next_line_index
                next_line_index += 1
                if current_code_line.find(';') != -1:
                    ended_semicolon_line_num = cur_line_index
                    current_code_line = re.sub(';.*','',current_code_line)
                bracket_pair_index = get_bracket_pair_index(current_code_line, current_bracket_depth)
                current_bracket_depth            = bracket_pair_index['end_bracket_depth']
                out_level1_right_bracket_y_list  = bracket_pair_index['out_level1_right_bracket_y_list']
            if not out_level1_right_bracket_y_list:
                PrintDebug('Error: match_case2 subcall egrep_l : %s in file : %s can not recognized !'%(egrep_l, f))
                continue
            assert(current_code_line[out_level1_right_bracket_y_list[0]] == ')')
            cur_subcall_post_part = (current_code_line[out_level1_right_bracket_y_list[0]+1:]).strip()
        # second, match the instance name for case 0 or 1
        # case 1: module_name        instance_name ( ... ) ;
        # case 2: module_name #(...) instance_name (...);
        #                            ^                      //  cur_subcall_post_part from here
        # patten0 = '(?P<instance_name>\w+)\s*(\[[^\[\]]*\])?'
        patten0 = '(?P<instance_name>\w+(\s*\[[^\[\]]*\])?)'
        patten1 = '(?P<io_connect_init_left_bracket_right_part>\(.*)'
        full_match  = False
        match_case1 = re.match('(\s*(?P<p0>%s)\s*(?P<p1>%s)?)|(\s*$)'%(patten0,patten1), cur_subcall_post_part)
        if not match_case1:# must has some error,report a error
            PrintDebug('Error: match_case0or1 0 subcall egrep_l : %s in file : %s can not recognized !'%(egrep_l, f))
            continue
        full_match = match_case1.group('p1')
        while (not full_match) and (ended_semicolon_line_num == -1) and (next_line_index < max_line_index):
            # next_code_line = re.sub('(^\s*`.*)|(//.*)','',f_lines[next_line_index].strip('\n'))
            next_code_line = get_valid_code(f_lines[next_line_index].strip('\n'))
            cur_line_index = next_line_index
            next_line_index += 1
            if next_code_line.find(';') != -1:
                ended_semicolon_line_num = cur_line_index
                next_code_line = re.sub(';.*','',next_code_line)
            cur_subcall_post_part = cur_subcall_post_part + ' ' + next_code_line
            match_case1 = re.match('(\s*(?P<p0>%s)\s*(?P<p1>%s)?)|(\s*$)'%(patten0,patten1), cur_subcall_post_part)
            if not match_case1:
                PrintDebug('Error: match_case0or1 1 subcall egrep_l : %s in file : %s can not recognized !'%(egrep_l, f)+'***'+cur_subcall_post_part)
                break
            full_match = match_case1.group('p1')
        if full_match:
            cur_submodule_instance_name = match_case1.group('instance_name')
            io_connect_init_left_bracket_right_part = match_case1.group('io_connect_init_left_bracket_right_part')
        else:
            PrintDebug('Error: match_case1 2 subcall egrep_l : %s in file : %s can not recognized !'%(egrep_l, f))
            continue
        # finial test if instance name match
        if not cur_submodule_instance_name:
            PrintDebug('Error: instance_name not find subcall egrep_l : %s in file : %s can not recognized !'%(egrep_l, f))
            continue
        assert(io_connect_init_left_bracket_right_part[0] == '(')
        #-----------------------------
        # get the subcall_end_line_num
        #-----------------------------
        # already end
        if ended_semicolon_line_num != -1:
            assert(cur_submodule_name)
            assert(cur_submodule_instance_name)
            cur_subcall_end_line_num     = ended_semicolon_line_num
            assert(cur_submodule_match_line_num <= cur_subcall_end_line_num)
            file_sub_call_infs.append( { 'submodule_name'           : cur_submodule_name
                                        ,'cur_module_name'          : '' # module current submodule belong to
                                        ,'instance_name'            : cur_submodule_instance_name
                                        ,'subcall_line_range'       : (cur_submodule_match_line_num, cur_subcall_end_line_num)
                                        ,'submodule_name_match_pos' : submodule_name_match_pos 
                                        ,'file_path'                : f
                                        ,'inaccuracy'               : False
                                        ,'last_modify_time'         : os.path.getmtime(f) } )
            already_pass_line_num = cur_subcall_end_line_num
            continue
        # cur not end
        # ended_semicolon_line_num     = cur_subcall_end_line_num
        current_bracket_depth        = 0
        start_a_new_subcall_instance = True
        new_subcall_instance_pending = False
        while (start_a_new_subcall_instance or new_subcall_instance_pending) and next_line_index < max_line_index:
            cur_line_index = next_line_index - 1
            next_code_line  = ''
            if start_a_new_subcall_instance:
                assert(io_connect_init_left_bracket_right_part[0] == '(')
                next_code_line = io_connect_init_left_bracket_right_part
                start_a_new_subcall_instance = False
                new_subcall_instance_pending = True
                io_connect_init_left_bracket_right_part = ''
            else:
                next_code_line = get_valid_code(f_lines[next_line_index].strip('\n'))
                if next_code_line.find(';') != -1:
                    ended_semicolon_line_num = next_line_index
                    next_code_line = re.sub(';.*','',next_code_line)
                cur_line_index = next_line_index
                next_line_index += 1
            bracket_pair_index = get_bracket_pair_index(next_code_line, current_bracket_depth)
            current_bracket_depth            = bracket_pair_index['end_bracket_depth']
            out_level1_right_bracket_y_list  = bracket_pair_index['out_level1_right_bracket_y_list']
            if not out_level1_right_bracket_y_list and ended_semicolon_line_num == -1:
                continue
            # if has ";" finish current
            if ended_semicolon_line_num != -1:
                assert(new_subcall_instance_pending)
                inaccuracy = False
                if not out_level1_right_bracket_y_list: # indistinct match can not trace back
                    # may happend for used '`ifdef ... `else ...'
                    PrintDebug('RTL Error: miss ")" before ";", at line:%d, file:%s '%(cur_line_index+1, f) )
                    inaccuracy = True
                assert(cur_submodule_name)
                assert(cur_submodule_instance_name)
                cur_subcall_end_line_num     = ended_semicolon_line_num
                assert(cur_submodule_match_line_num <= cur_subcall_end_line_num)
                file_sub_call_infs.append( { 'submodule_name'           : cur_submodule_name
                                            ,'cur_module_name'          : '' # module current submodule belong to
                                            ,'instance_name'            : cur_submodule_instance_name
                                            ,'subcall_line_range'       : (cur_submodule_match_line_num, cur_subcall_end_line_num)
                                            ,'submodule_name_match_pos' : submodule_name_match_pos 
                                            ,'file_path'                : f
                                            ,'inaccuracy'               : inaccuracy
                                            ,'last_modify_time'         : os.path.getmtime(f) } )
                already_pass_line_num = cur_subcall_end_line_num
                new_subcall_instance_pending = False
                break
            # must be out_level1_right_bracket_y_list and not get ";"
            # 1 first end current subcall
            assert(out_level1_right_bracket_y_list)
            assert(new_subcall_instance_pending)
            assert(cur_submodule_name)
            assert(cur_submodule_instance_name)
            cur_subcall_end_line_num = cur_line_index
            assert(cur_submodule_match_line_num <= cur_subcall_end_line_num)
            file_sub_call_infs.append( { 'submodule_name'           : cur_submodule_name
                                        ,'cur_module_name'          : '' # module current submodule belong to
                                        ,'instance_name'            : cur_submodule_instance_name
                                        ,'subcall_line_range'       : (cur_submodule_match_line_num, cur_subcall_end_line_num)
                                        ,'submodule_name_match_pos' : submodule_name_match_pos 
                                        ,'file_path'                : f
                                        ,'inaccuracy'               : False
                                        ,'last_modify_time'         : os.path.getmtime(f) } )
            already_pass_line_num = cur_subcall_end_line_num
            new_subcall_instance_pending = False
            # 2 second find next instance start
            # deal the singal module multi instance case
            # module name ... instance0(...),
            #                 instance1(...);
            # if find the next instance name, continue. else break
            if len(out_level1_right_bracket_y_list) > 1:
                PrintDebug('Error: current not support, multi instance in one line ! line:%d, file:%s'%(cur_line_index, f))
                break
            assert(len(out_level1_right_bracket_y_list) == 1)
            code_left_part   = next_code_line[out_level1_right_bracket_y_list[0]+1:]
            assert(not (start_a_new_subcall_instance or new_subcall_instance_pending) )
            while (next_line_index < max_line_index):
                # next_code_line = re.sub('(^\s*`.*)|(//.*)','',f_lines[next_line_index].strip('\n'))
                next_code_line = get_valid_code(f_lines[next_line_index].strip('\n'))
                cur_line_index = next_line_index
                next_line_index += 1
                code_left_part = (code_left_part + ' ' + next_code_line).strip()
                if code_left_part:
                    if code_left_part[0] != ',':
                        break
                    # match: , instance_name (
                    patten0 = ','
                    # patten1 = '(?P<instance_name>\w+)\s*(\[[^\[\]]*\])?'
                    patten1 = '(?P<instance_name>\w+(\s*\[[^\[\]]*\])?)'
                    patten2 = '(?P<io_connect_init_left_bracket_right_part>\(.*)'
                    match_next = re.match('(?P<p0>%s)\s*(?P<p1>%s)?\s*(?P<p2>%s)?\s*$'%(patten0,patten1,patten2), code_left_part)
                    if not match_next:
                        break
                    if match_next.group('p2'): # full match then get new instance start
                        cur_submodule_instance_name = match_next.group('instance_name')
                        io_connect_init_left_bracket_right_part = match_next.group('io_connect_init_left_bracket_right_part')
                        cur_submodule_match_line_num = cur_line_index
                        # for signal module multi instance, match pos set to instance name(except for first one)
                        instance_y = next_code_line.find(cur_submodule_instance_name)
                        instance_x = cur_line_index
                        if instance_y == -1:
                            pre_line_code = get_valid_code(f_lines[cur_line_index-1].strip('\n'))
                            instance_y = pre_line_code.find(cur_submodule_instance_name)
                            instance_x = cur_line_index - 1
                        assert(instance_y != -1)
                        submodule_name_match_pos = (instance_x, instance_y)
                        start_a_new_subcall_instance = True
                        break
        # if has pending unfinished
        if new_subcall_instance_pending:
            PrintDebug('Error: subcall no end identify ! line:%d, file:%s'%(cur_submodule_match_line_num, f))
    # for each subcall inf in current file add cur module inf 
    add_cur_file_cur_module_name_to_subcall_inf(module_inf_list, file_sub_call_infs)
    return file_sub_call_infs


def onload_G_MacroNameToMacroInfListDic():
    # if MacroNameToMacroInfListDic not updata get from pickle
    if G['MacroNameToMacroInfListDic'] == None:
        macro_name_to_macro_inf_list_dic_pkl_path = G['VTagsPath']+'/pickle/macro_name_to_macro_inf_list_dic.pkl'
        if os.path.isfile(macro_name_to_macro_inf_list_dic_pkl_path):
            print('vtags is uploading macro define information for the first time ...')
            G['MacroNameToMacroInfListDic'] = pickle_reload(macro_name_to_macro_inf_list_dic_pkl_path)
        else:
            G['MacroNameToMacroInfListDic'] = {}

def get_macro_inf_list( macro_name ):
    # if MacroNameToMacroInfListDic not updata get from pickle
    onload_G_MacroNameToMacroInfListDic()
    # if get macro inf list, refresh stale inf
    if macro_name in G['MacroNameToMacroInfListDic']:
        macro_inf_list = G['MacroNameToMacroInfListDic'][macro_name]
        # del stale
        stale_file_path_set = set()
        i = 0
        while i < len(macro_inf_list):
            t_macro_inf = macro_inf_list[i]
            if not check_inf_valid(t_macro_inf['file_path'], t_macro_inf['last_modify_time']):
                stale_file_path_set.add(t_macro_inf['file_path'])
                del macro_inf_list[i]
                continue
            i += 1
        # updata stale file
        for f in stale_file_path_set:
            updata_file_inf(t_macro_inf['file_path'])
        # if has valid inf return
        if len(G['MacroNameToMacroInfListDic'][macro_name]) > 0:
            return G['MacroNameToMacroInfListDic'][macro_name]
    # if still not find valid macro inf, refresh vtags db if valid
    if (macro_name not in G['MacroNameToMacroInfListDic']) and G['RefreshDBValid']:
        refresh_vtags_db()
    if macro_name in G['MacroNameToMacroInfListDic']:
        return G['MacroNameToMacroInfListDic'][macro_name]
    return []


def onload_G_ModuleNameToFilePathListDic():
    # if ModuleNameToFilePathListDic not updata get from pickle
    if G['ModuleNameToFilePathListDic'] == None:
        module_name_to_file_path_list_dic_pkl_path = G['VTagsPath']+'/pickle/module_name_to_file_path_list_dic.pkl'
        if os.path.isfile(module_name_to_file_path_list_dic_pkl_path):
            G['ModuleNameToFilePathListDic'] = pickle_reload(module_name_to_file_path_list_dic_pkl_path)
        else:
            G['ModuleNameToFilePathListDic'] = {}

# this function used to add which module current submodule_inf beyond to
def add_cur_file_cur_module_name_to_subcall_inf(module_inf_list, subcall_inf_list):
    cur_line_module_i       = 0
    cur_line_module_begin   = -1
    cur_line_module_end     = -1
    if module_inf_list:
        cur_line_module_begin   = module_inf_list[cur_line_module_i]['module_line_range'][0]
        cur_line_module_end     = module_inf_list[cur_line_module_i]['module_line_range'][1]
    else:
        PrintDebug("Error: file has subcall_inf but no module inf(maybe module define by macro), subcall_inf_list = %s"%(subcall_inf_list.__str__()))
        return
    cur_line_module_name    = module_inf_list[cur_line_module_i]['module_name']
    for subcall_inf in subcall_inf_list:
        submodule_name  = subcall_inf['submodule_name']
        submodule_begin = subcall_inf['subcall_line_range'][0]
        submodule_end   = subcall_inf['subcall_line_range'][1]
        # first get current subcall correspond module name
        # -----c0-------c1--------   // c0, c1 is cur module begin, end
        # ----------------s0------   // s0, s1 is subcall begin, end. need forward cur module
        # need s0 < c1
        while cur_line_module_end < submodule_begin:
            cur_line_module_i       += 1
            assert( cur_line_module_i < len(module_inf_list) )
            cur_line_module_begin   = module_inf_list[cur_line_module_i]['module_line_range'][0]
            cur_line_module_end     = module_inf_list[cur_line_module_i]['module_line_range'][1]
            cur_line_module_name    = module_inf_list[cur_line_module_i]['module_name']
        # after while only valid case is
        # -----c0-------c1--------   // c0, c1 is cur module begin, end
        # -------s0---s1----------   // s0, s1 is subcall begin, end
        if cur_line_module_begin <= submodule_begin and submodule_end <= cur_line_module_end:
            subcall_inf['cur_module_name'] = cur_line_module_name
            PrintDebug(subcall_inf.__str__())
            continue
        # other case all invalid, need report
        # already s0 < c1
        # -------c0-------c1------
        # error case
        # --s0-------s1-----------  # subcall cross module 
        # --s0-s1-----------------  # subcall not have any correspond module  
        # -----------s0------s1---- # subcall cross module 
        if submodule_begin < cur_line_module_begin and submodule_end >= cur_line_module_begin:
            PrintDebug("Error: subcall cross module, subcall_inf:%s \n module_inf:%s "%(subcall_inf.__str__(), module_inf_list[cur_line_module_i].__str__()))
        if submodule_end < cur_line_module_begin:
            PrintDebug("Error: subcall has no corresponding module, subcall_inf:%s "%(subcall_inf.__str__()))
        if submodule_begin <= cur_line_module_end and submodule_end > cur_line_module_end:
            PrintDebug("Error: subcall cross module, subcall_inf:%s \n module_inf:%s "%(subcall_inf.__str__(), module_inf_list[cur_line_module_i].__str__()))
    return

def onload_G_CallMeSubcallInf():
    # if ModuleNameToCallMeSubcallInfListDic not updata get from pickle
    if G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'] == None:
        assert( G['CallMeSubcallInf']['MaskedCallMeSubmoduleSet'] == None )
        call_me_subcall_inf_path = G['VTagsPath']+'/pickle/call_me_subcall_inf.pkl'
        if os.path.isfile(call_me_subcall_inf_path):
            call_me_subcall_inf = pickle_reload(call_me_subcall_inf_path)
            G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'] = call_me_subcall_inf['ModuleNameToCallMeSubcallInfListDic']
            G['CallMeSubcallInf']['MaskedCallMeSubmoduleSet']            = call_me_subcall_inf['MaskedCallMeSubmoduleSet']
        else:
            G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'] = {}
            G['CallMeSubcallInf']['MaskedCallMeSubmoduleSet']            = set()

def get_call_me_subcall_inf_list( module_name, create = False ):
    onload_G_CallMeSubcallInf()
    if module_name in G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic']:
        refresh_cur_call_me_subcall_inf_list( module_name )
        return G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'][module_name]
    elif create:
        G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'][module_name] = []
        return G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'][module_name]
    return None

def refresh_cur_call_me_subcall_inf_list( module_name ):    
    # refresh call me inf when add new
    assert( module_name in G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'] )
    cur_call_me_subcall_inf_list = G['CallMeSubcallInf']['ModuleNameToCallMeSubcallInfListDic'][ module_name ]
    i = 0
    while i < len( cur_call_me_subcall_inf_list ):
        cur_subcall_inf  = cur_call_me_subcall_inf_list[i]
        call_module_file = cur_subcall_inf['file_path']
        # if call module not change just continue
        if check_inf_valid( cur_subcall_inf['file_path'], cur_subcall_inf['last_modify_time'] ):
            i += 1
            continue
        # else must stale just delate, if refresh will add it when refresh
        del cur_call_me_subcall_inf_list[i] # delate stale, if still exist must add to the end before
    return

def add_ModuleNameToCallMeSubcallInfListDic( subcall_inf_list ):
    onload_G_CallMeSubcallInf()
    # touched_module_set = set()
    for new_subcall_inf in subcall_inf_list:
        # should not add a stale subcall inf
        assert( check_inf_valid(new_subcall_inf['file_path'], new_subcall_inf['last_modify_time']) )
        # if module in masked then not add
        new_submodule_name = new_subcall_inf['submodule_name']
        if new_submodule_name in G['CallMeSubcallInf']['MaskedCallMeSubmoduleSet']:
            continue
        # touched_module_set.add( new_submodule_name )
        # because get_call_me_subcall_inf_list has refreshed subcall inf
        # so it must all valid
        old_call_me_subcall_inf_list = get_call_me_subcall_inf_list( new_submodule_name, True )
        # first all new
        # if new add subcall inf(same file , same instance) already exist, replace it
        i = 0
        while i < len( old_call_me_subcall_inf_list ):
            o_subcall_inf = old_call_me_subcall_inf_list[i]
            assert( o_subcall_inf['submodule_name'] == new_subcall_inf['submodule_name'] )
            if (o_subcall_inf['file_path'], o_subcall_inf['cur_module_name'], o_subcall_inf['instance_name']) == \
               (new_subcall_inf['file_path'], new_subcall_inf['cur_module_name'], new_subcall_inf['instance_name']):
                del old_call_me_subcall_inf_list[i]
                continue
            i += 1
        old_call_me_subcall_inf_list.append( new_subcall_inf )
    # last pickle save new CallMeSubcallInf
    pickle_save(G['CallMeSubcallInf'], G['VTagsPath']+'/pickle/call_me_subcall_inf.pkl')
    return True

# need special care to loop case
def recursion_get_module_trace( module_name, cur_trace, full_traces ):
    call_me_subcall_inf_list = get_call_me_subcall_inf_list( module_name )
    if not call_me_subcall_inf_list:
        if cur_trace:
            full_traces.append( cur_trace )
        return
    for subcall_inf in call_me_subcall_inf_list:
        assert( subcall_inf['submodule_name'] == module_name),'%s,%s'%(subcall_inf.__str__(), module_name)
        new_trace = [ t for t in cur_trace]
        # need special care to loop case
        loop_back = False
        for n_subcall_inf in new_trace:
            if n_subcall_inf['submodule_name'] == subcall_inf['submodule_name']:
                loop_back = True
                break
        # normal add
        new_trace.append( subcall_inf )
        if loop_back:
            return
        # if subcall_inf has cur_module_name recursion get upper
        # if 'cur_module_name' in subcall_inf:
        if subcall_inf['cur_module_name']:
            recursion_get_module_trace( subcall_inf['cur_module_name'], new_trace, full_traces )
        else: # means current submodule has no module inf just pass, this maybe happen when module name define by macro
            PrintReport("Warning: can not find module, maybe module name define by macro. in file: %s"%(subcall_inf['file_path']))
    return
