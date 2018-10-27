"""
http://www.vim.org/scripts/script.php?script_id=5494
"""
#===============================================================================
# BSD 2-Clause License

# Copyright (c) 2018, Jimmy Situ
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
import os
import re
import pickle
import inspect
import Lib.GLB as GLB
G = GLB.G
# function to print debug
PrintDebug  = G['PrintDebug_F']

def MountPrintLines(line_list, label = '', link_list = None, length = 80, Print = False, end_star = True, no_end_line = False):
    final_line_list = []
    final_link_list = []
    # get real width
    max_line_length = length
    if end_star:
        for l in line_list:
            # not support change line
            # '\n' should not in MountPrintLines line list, so we use \nlable\n as lable id
            if l.find('\n') != -1:
                if re.match('\nlable\n:', l):
                    continue
                assert( False )
            if (len(l) + 4) > max_line_length:
                max_line_length = (len(l) + 4)  # +4 because need add - '| ' --- ' |'
        # start generate first two line
        final_line_list.append( '_' * max_line_length )
        final_line_list.append( '_' * ((max_line_length - len(label))>>1) + label + '_' * ((max_line_length - len(label) + 1)>>1))
        final_line_list.append( '*' + ' ' * (max_line_length - 2) + '*')
        final_link_list.append( {} )
        final_link_list.append( {} )
        final_link_list.append( {} )
        # add input line_list to frame
        for i,l in enumerate(line_list):
            # special care for sub lable
            match_sub_label = re.match('^\nlable\n:(?P<sub_label>.*)', l)
            if match_sub_label:
                sub_label = match_sub_label.group('sub_label')
                final_line_list.append( '*' + '-' * ((max_line_length -2 - len(sub_label))>>1) + sub_label + '-' * ((max_line_length -2 - len(sub_label) + 1)>>1) + '*')
            else:# normal case
                l = '* ' + l + ' ' * ( max_line_length - len(l) - 4 ) + ' *'
                final_line_list.append( l )
            # for link
            if link_list:
                final_link_list.append( link_list[i] )
            else:
                final_link_list.append( {} )
        # add end line
        final_line_list.append( '*_' + '_' * (max_line_length - 4) + '_*')
        final_link_list.append( {} )
    else:
        # start generate first two line
        final_line_list.append( '_' * max_line_length )
        final_line_list.append( '_' * ((max_line_length - len(label))>>1) + label + '_' * ((max_line_length - len(label) + 1)>>1))
        final_line_list.append( '*')
        final_link_list.append( {} )
        final_link_list.append( {} )
        final_link_list.append( {} )
        # add input line_list to frame
        for i,l in enumerate(line_list):
            # special care for sub lable
            match_sub_label = re.match('^\nlable\n:(?P<sub_label>.*)', l)
            if match_sub_label:
                sub_label = match_sub_label.group('sub_label')
                final_line_list.append( '*' + '-' * ((max_line_length -2 - len(sub_label))>>1) + sub_label + '-' * ((max_line_length -2 - len(sub_label) + 1)>>1) + '-')
            else:# normal case
                l = '* ' + l + ' ' * ( max_line_length - len(l) - 4 ) + '  '
                final_line_list.append( l )
            # for link
            if link_list:
                final_link_list.append( link_list[i] )
            else:
                final_link_list.append( {} )
        # add end line
        if not no_end_line:
            final_line_list.append( '**' + '*' * (max_line_length - 4) + '**')
            final_link_list.append( {} )
        else:
            final_line_list.append( '' )
            final_link_list.append( {} )
    assert( len(final_line_list) == len(final_link_list)  )
    if Print:
        for l in final_line_list: print(l)
    return {'line_list': final_line_list, 'link_list': final_link_list}


def PrintTime(prefix,t):
    if False:
        time_str = re.sub('\..*','',str(t*1000000))
        PrintDebug(prefix+time_str)

def get_full_word(line, y):
    pre_part  = ( re.match('^(?P<pre>\w*)',(line[:y])[::-1]).group('pre') )[::-1]
    post_part = re.match('^(?P<post>\w*)', line[y:]).group('post')
    return pre_part + post_part

def get_file_path_postfix(file_path):
    if type(file_path) != str:
        return ''
    split_by_dot = file_path.split('.')
    if len(split_by_dot) < 2 : # which means file_path has no postfix
        return ''
    # post_fix = split_by_dot[-1].lower() # postfix don't care case
    post_fix = split_by_dot[-1]           # postfix care case
    return post_fix

def get_file_hdl_type(file_path):
    postfix = get_file_path_postfix(file_path)
    if postfix in G['SupportVHDLPostfix']:
        return 'vhdl'
    elif postfix in G['SupportVerilogPostfix']:
        return 'verilog'
    else:
        return ''

def get_valid_code(code_line, mode = ['note','macro_code']):
    if 'note' in mode:
        pos = code_line.find('//')
        if pos != -1:
            code_line = code_line[:pos]
        pos = code_line.find('/*')
        if pos != -1:
            code_line = re.sub('/\*.*?\*/', '', code_line)
    if 'macro_code' in mode:
        if re.match('\s*(`define|`ifdef|`ifndef|`else|`endif)',code_line):
            code_line = ''
    return code_line




# this use egrep to find all the signal appear pos,code_line
def search_verilog_code_use_grep(key, path, row_range = ()):
    search_result = []
    match_lines    = os.popen('egrep -n -h \'(^|\W)%s(\W|$)\' %s'%(key, path)).readlines()
    for l in match_lines:
        l = l.strip('\n')
        split0 = l.split(':')
        line_num   = int(split0[0]) - 1
        code_line  = ':'.join(split0[1:])
        if row_range and ( line_num not in range(row_range[0], row_range[1]+1 ) ):
            continue
        # del note see if has key
        s0 = re.search('(?P<pre>^|\W)%s(\W|$)'%(key), re.sub('//.*','',code_line) )
        if s0:
            colum_num  = s0.span()[0] + len(s0.group('pre'))
            match_pos  = (line_num, colum_num)
            line       = code_line
            search_result.append( (match_pos, line) )
    return search_result


def show_progress_bar( i, i_max, show_char = '#', show_width = 20):
    i += 1 # count from 1
    i_max_len = len(str(i_max))
    i_len     = len(str(i))
    i_str     = ' '*(i_max_len-i_len)+str(i)
    i_max_str = str(i_max)
    prefix    = '%s/%s: '%(i_str,i_max_str)
    pass_str  = show_char * int(((i*show_width)/i_max))
    empty_str = ' '*(show_width - len(pass_str))
    progress_bar = '[%s%s]'%(pass_str,empty_str)
    tool_len  = len(prefix) + show_width
    sys.stdout.write(' '*tool_len + '\r')
    sys.stdout.flush()
    sys.stdout.write(prefix + progress_bar)

def get_vhdl_full_line(codes, start_pos, direction):
    pass

def get_verilog_pre_full_line(codes, start_pos):
    pre_full_line = ''
    start_x, start_y = start_pos
    start_line = codes[start_x][:start_y+1]
    start_line = start_line.strip('\n')
    start_line = re.sub('//.*','',start_line)
    colon_y    = start_line.rfind(';')
    if colon_y != -1:
        pre_full_line = start_line[colon_y+1:]
    else:
        pre_full_line = start_line
        for i in range(start_x-1,-1,-1):
            t_line = codes[i].strip('\n')
            t_line = re.sub('//.*', '', t_line)
            t_colon_y = t_line.rfind(';')
            if t_colon_y != -1:
                pre_full_line = t_line[t_colon_y+1:] + ' ' + pre_full_line
                break
            else:
                pre_full_line = t_line + ' ' +pre_full_line
    return pre_full_line

def get_verilog_post_full_line(codes, start_pos):
    post_full_line = ''
    start_x, start_y = start_pos
    start_line = codes[start_x][start_y:]
    start_line = start_line.strip('\n')
    start_line = re.sub('//.*','',start_line)
    colon_y    = start_line.find(';')
    if colon_y != -1:
        pre_full_line = start_line[:colon_y+1]
    else:
        pre_full_line = start_line
        for i in range(start_x+1,len(codes)):
            t_line = codes[i].strip('\n')
            t_line = re.sub('//.*', '', t_line)
            t_colon_y = t_line.find(';')
            if t_colon_y != -1:
                pre_full_line = pre_full_line + ' ' + t_line[: t_colon_y+1]
                break
            else:
                pre_full_line = pre_full_line + ' ' + t_line
    return pre_full_line

def get_verilog_full_line(codes, start_pos, direction):
    if direction == -1:  # 0 <- x
        return get_verilog_pre_full_line(codes, start_pos)
    elif direction == 1: #      x -> n
        return get_verilog_post_full_line(codes, start_pos)
    elif direction == 0: # 0 <- x -> n
        return get_verilog_pre_full_line(codes, start_pos) + get_verilog_post_full_line(codes, start_pos)[1:] # [1:] because start char at both part
    else:
        return ''

def get_full_line( codes, hdl_type, start_pos, direction = 0):
    if hdl_type == 'vhdl':
        return get_vhdl_full_line(codes, start_pos, direction)
    elif hdl_type == 'verilog':
        return get_verilog_full_line(codes, start_pos, direction)
    else:
        return ''

# this function used to save/reload inf used pickle
def pickle_save(data, path):
    output = open(path, 'wb')
    pickle.dump(data, output)
    output.close()

def pickle_reload(path):
    data      = None
    if os.path.isfile(path):
        pkl_input = open(path,'rb')
        data      = pickle.load(pkl_input)
        pkl_input.close()
    return data

def check_inf_valid(path, last_modify_time = None):
    if not os.path.isfile(path):
        return False
    if last_modify_time != None:
        if os.path.getmtime(path) != last_modify_time:
            return False
    return True

# this function return a list of index, for level1 bracket comma
def get_bracket_pair_index(code_line, start_bracket_depth):
    # split bracket and comma
    split_by_left_bracket  = code_line.split('(')
    split_by_right_bracket = code_line.split(')')
    # get all the left_bracket appear colum in code_line
    last_left_bracket_y   = -1  # left_bracket in code_line
    left_bracket_appear_y = []
    for pace in split_by_left_bracket:
        last_left_bracket_y = last_left_bracket_y + len(pace) + 1
        left_bracket_appear_y.append(last_left_bracket_y)
    assert(left_bracket_appear_y[-1] == len(code_line))
    del left_bracket_appear_y[-1:] # del last split pace y
    # get all the left_bracket appear colum in code_line
    last_right_bracket_y   = -1  # right_bracket in code_line
    right_bracket_appear_y = []
    for pace in split_by_right_bracket:
        last_right_bracket_y = last_right_bracket_y + len(pace) + 1
        right_bracket_appear_y.append(last_right_bracket_y)
    assert(right_bracket_appear_y[-1] == len(code_line))
    del right_bracket_appear_y[-1:] # del last split pace y
    # get all the y need care
    left_bracket_appear_y_set  = set(left_bracket_appear_y)
    right_bracket_appear_y_set = set(right_bracket_appear_y)
    assert( not( left_bracket_appear_y_set & right_bracket_appear_y_set ) )
    active_y = list( left_bracket_appear_y_set | right_bracket_appear_y_set )
    active_y.sort()
    # for each active_y do follow actions
    cur_bracket_depth               = start_bracket_depth
    in_level1_left_bracket_y_list   = []
    out_level1_right_bracket_y_list = []
    for y in active_y:
        if y in left_bracket_appear_y_set:
            cur_bracket_depth += 1
            if cur_bracket_depth == 1:
                in_level1_left_bracket_y_list.append(y)
        if y in right_bracket_appear_y_set:
            cur_bracket_depth -= 1
            if cur_bracket_depth == 0:
                out_level1_right_bracket_y_list.append(y)
    return { 'end_bracket_depth'               : cur_bracket_depth
            ,'in_level1_left_bracket_y_list'   : in_level1_left_bracket_y_list
            ,'out_level1_right_bracket_y_list' : out_level1_right_bracket_y_list }

#------------------------------------------------------------------------------
# hyperlink function
#------------------------------------------------------------------------------
hyperlink_action_dic = {}

def register_hyperlink_action( action_func, description = '' ):
    assert(inspect.isfunction(action_func) and type(description) == str)
    action = action_func.__name__
    assert(action not in hyperlink_action_dic)
    action_func.description     = description
    hyperlink_action_dic[action] = action_func
    return True

def check_hyperlink_legal(action_list, action_parm_dic):
    def check_action_valid(action, action_parm_dic):
        if action not in hyperlink_action_dic:
            return False
        action_func = hyperlink_action_dic[action]
        arg_spec = inspect.getargspec(action_func)
        # mast need arg has no default value
        must_need_arg_list = []
        arg_to_default_value_map = {}
        if arg_spec.defaults == None:
            must_need_arg_list = arg_spec.args
        else:
            must_need_arg_list         = [ arg for arg in arg_spec.args[:-(len(arg_spec.defaults))] ]
            for i,v in enumerate(arg_spec.defaults[::-1]):
                arg_to_default_value_map[ arg_spec.args[-(i+1)] ] = v
        for arg in must_need_arg_list:
            if arg not in action_parm_dic:
                return False
        # arg has default value type must same
        for arg in arg_to_default_value_map:
            if arg in action_parm_dic:
                if type( action_parm_dic[arg] ) != type(arg_to_default_value_map[arg]):
                    return False
        return True
    # if only one action, you can use action name as trigger
    if type(action_list) == str:
        return check_action_valid(action_list, action_parm_dic)
    #if multi action, need check each action func parameter valid
    for action in action_list:
        if not check_action_valid(action, action_parm_dic):
            return False
    return True

def gen_hyperlink(action_list, action_parm_dic, Type = 'single_action_link'):
    # if only one action, you can use action name as trigger
    if type(action_list) == str:
        action_list = [ action_list ]
    # if G['Debug']: assert( check_hyperlink_legal(action_list, action_parm_dic) )
    hyperlink = {
         'type'               : Type
        ,'action_list'        : action_list
        ,'action_parm_dic'    : action_parm_dic
        ,'intime_parms_dic'   : None
        ,'payload_dic'        : {}
    }
    return hyperlink

def do_action_function( action_func, parm_dic ):
    arg_spec           = inspect.getargspec(action_func)
    func_parm_str_list = []
    for arg in arg_spec.args:
        if arg in parm_dic:
            func_parm_str_list.append( '%s = parm_dic["%s"]'%(arg, arg) )
    func_parm = ', '.join( func_parm_str_list )
    PrintDebug('Trace: do_action_function: "return_result = %s(%s)'%(action_func.__name__, func_parm))
    return_result = None
    exec( "return_result = action_func(%s)"%(func_parm) )
    return return_result

def do_hyperlink( hyperlink, trigger_list = []):
    action_list        = hyperlink['action_list']
    action_parm_dic    = hyperlink['action_parm_dic']
    intime_parms_dic   = hyperlink['intime_parms_dic']
    assert('intime_parms_dic' not in action_parm_dic)
    action_parm_dic['intime_parms_dic'] = intime_parms_dic
    # if no trigger must only one action for this link
    if not trigger_list:
        if len(action_list) != 1:
            PrintDebug( "do_hyperlink 0: action_parm_dic = %s"%(action_parm_dic.__str__()) )
            PrintDebug( "do_hyperlink 0: hyperlink = %s"%(hyperlink.__str__()) )
            hyperlink['intime_parms_dic'] = None
            del action_parm_dic['intime_parms_dic']
            return False
        if not check_hyperlink_legal(action_list, action_parm_dic):
            PrintDebug( "do_hyperlink 1: action_parm_dic = %s"%(action_parm_dic.__str__()) )
            hyperlink['intime_parms_dic'] = None
            del action_parm_dic['intime_parms_dic']
            return False
        do_action_function( hyperlink_action_dic[action_list[0]], action_parm_dic )
        hyperlink['intime_parms_dic'] = None
        del action_parm_dic['intime_parms_dic']
        return True
    # if just do one action, trigger_list can be action string
    if type(trigger_list) == str:
        if not check_hyperlink_legal(trigger_list, action_parm_dic):
            PrintDebug( "do_hyperlink 1: action_parm_dic = %s"%(action_parm_dic.__str__()) )
            hyperlink['intime_parms_dic'] = None
            del action_parm_dic['intime_parms_dic']
            return False
        do_action_function( hyperlink_action_dic[ trigger_list ], action_parm_dic )
        hyperlink['intime_parms_dic'] = None
        del action_parm_dic['intime_parms_dic']
        return True
    # if has trigger_list, trigger action one by one
    # first check all action can work
    for trigger in trigger_list:
        if trigger not in action_list:
            PrintDebug( "do_hyperlink: trigger not in action_list" )
            hyperlink['intime_parms_dic'] = None
            del action_parm_dic['intime_parms_dic']
            return False
        if not check_hyperlink_legal( trigger, action_parm_dic):
            PrintDebug( "do_hyperlink: not check_hyperlink_legal(action_list[trigger], action_parm_dic)" )
            hyperlink['intime_parms_dic'] = None
            del action_parm_dic['intime_parms_dic']
            return False
    for trigger in trigger_list:
        do_action_function( hyperlink_action_dic[ trigger ], action_parm_dic )
    hyperlink['intime_parms_dic'] = None
    del action_parm_dic['intime_parms_dic']
    return True
