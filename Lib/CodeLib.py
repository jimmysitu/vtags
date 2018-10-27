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
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
from InlineLib.ViewLib import *
import Lib.FileInfLib as FileInfLib


# this function calculate the io number for subcall_code_line's last word 
def calculate_last_word_io_number(subcall_code_line):
    # get the code after io_connect init left bracket, include bracket
    # module_name          instance_name(b,c,d ... // case0 subcall_code_line
    # module_name #(a , b) instance_name(b,c,d ... // case1 subcall_code_line
    #                                   ^^^^^^^^^^ // code after io_connect init left bracket
    # module_name          instance_name0(a,b,c...), // case0 or 1 
    #                      instance_name1(a,b,c...), // case2
    #                      ...
    #                      instance_name2(a,b,c...); // case2
    code_after_io_connect_init_left_bracket = ''
    search_io_connect_case = re.match('^\s*\w+\s+\w+\s*(?P<after_part>\(.*)', subcall_code_line) # case0
    if not search_io_connect_case:
        search_io_connect_case = re.search('\)\s*\w+\s*(\[[^\[\]]*\])?\s*(?P<after_part>\(.*)', subcall_code_line) # case1
    if not search_io_connect_case:
        search_io_connect_case = re.match('(,)?\s*\w+\s*(\[[^\[\]]*\])?\s*(?P<after_part>\(.*)',subcall_code_line) # case2
    if search_io_connect_case:
        code_after_io_connect_init_left_bracket = search_io_connect_case.group('after_part')
    else: # not in io_connect code
        return -1
    # for the after code, change some char for count the comma in bracket level 1
    code_after_io_connect_init_left_bracket = treat_by_bracket_fmt(code_after_io_connect_init_left_bracket)
    # count the comma in bracket level 1
    comma_inf = bracket_level1_comma_index_list(code_after_io_connect_init_left_bracket, 0)
    # valid in_connect in_level1_left_bracket_y_list must be 1
    # if in_level1_left_bracket_y_list == 0 means not in io_connect
    # if in_level1_left_bracket_y_list > 1 means last pos already out of io_connect
    if len(comma_inf['in_level1_left_bracket_y_list']) != 1:
        return -1
    # the in_level1_left_bracket_y_list need add to the valid_level1_comma_y_list
    # because first ',' means has 2 io_connect
    real_io_connect_num = len( comma_inf['in_level1_left_bracket_y_list'] + comma_inf['valid_level1_comma_y_list'] )
    return real_io_connect_num - 1  # start from 0


# this function used to get the submodule io name inf
# if current subcall assign use .xxx(yyy), then return xxx as io name
# if current subcall assugn use (a,b,c), then return nubmer of io of input pos
def get_submodule_io_name_inf(subcall_lines, relative_pos):
    pos_line = subcall_lines[relative_pos[0]].strip('\n')
    # pos_line = re.sub('(^\s*`.*)|(//.*)','',pos_line)
    pos_line = get_valid_code(pos_line)
    if not( relative_pos[1] < len(pos_line) ):
        PrintDebug('Trace: get_submodule_io_name_inf: current cursor not in valid subcall line !')
        return False
    pos_word = get_full_word(pos_line, relative_pos[1])
    if not pos_word :
        PrintDebug('Trace: get_submodule_io_name_inf: current cursor not on valid word !')
        return False  
    pre_pos_part  = pos_line[ : relative_pos[1] + 1 ] # include pos char
    # case 0:
    # ... .xxx(yyy | zzz ) ...  // pos_line
    #       ^            // relative_pos[1]
    # submodule_io_name = xxx
    # pos_word          = xxx
    if re.match('\w+\.', pre_pos_part[::-1]):
        submodule_io_name = pos_word
        # post_pos_part = pos_line[ relative_pos[1] : ]     # include pos char
        # cur_line_io_connected_logic = re.sub('(^\w*)|(\.\w+\(.*)', '', post_pos_part)
        # io_connected_signals = set( re.findall('\w+' , cur_line_io_connected_logic) )
        return (submodule_io_name, pos_word)
    # case 1:
    # ... .xxx(yyy | zzz ) ...  // pos_line
    #                 ^         // relative_pos[1]
    # submodule_io_name = xxx
    # pos_word          = zzz
    case1 = re.search('\(\s*(?P<reverse_submodule_io_name>\w+)\.',pre_pos_part[::-1])
    if case1:
        submodule_io_name = (case1.group('reverse_submodule_io_name'))[::-1]
        # check match valid, valid when cursor word not out ".xxx(..." bracket pair
        match_right_bracket_left_code = ((pre_pos_part[::-1])[:case1.span()[0]+1])[::-1]
        assert(match_right_bracket_left_code[0] == '(')
        bracket_pair_index = get_bracket_pair_index(match_right_bracket_left_code, 0)
        if not bracket_pair_index['out_level1_right_bracket_y_list']:
            return (submodule_io_name, pos_word)
    # case 1.1:
    # i:   .xxx( yyy ,
    # i+1        zzz )     # pos_line
    #             ^        # pos
    # submodule_io_name = xxx
    # pos_word          = zzz
    for i in range(relative_pos[0] - 1, -1, -1): # from pre line to begining
        # cur_line = re.sub('(^\s*`.*)|(//.*)', '',subcall_lines[i].strip('\n'))
        cur_line = get_valid_code(subcall_lines[i].strip('\n'))
        pre_pos_part = cur_line + ' ' + pre_pos_part
        if pre_pos_part.find('.') == -1:
            continue
        case1 = re.search('\(\s*(?P<reverse_submodule_io_name>\w+)\.',pre_pos_part[::-1])
        if case1:
            submodule_io_name = (case1.group('reverse_submodule_io_name'))[::-1]
            # check match valid, valid when cursor word not out ".xxx(..." bracket pair
            match_right_bracket_left_code = ((pre_pos_part[::-1])[:case1.span()[0]+1])[::-1]
            assert(match_right_bracket_left_code[0] == '(')
            bracket_pair_index = get_bracket_pair_index(match_right_bracket_left_code, 0)
            if not bracket_pair_index['out_level1_right_bracket_y_list']:
                return (submodule_io_name, pos_word)
            else:
                break
    # case 2:
    # ... module_name          instance_name(a, b, c);    # maybe mul line
    # ... module_name #(parms) instance_name(a, b, c);
    #                                           ^         # pos
    # submodule_io_name = 1, the number of io's
    # pos_word          = b
    submodule_io_name = calculate_last_word_io_number(pre_pos_part)
    if submodule_io_name >= 0:
        return (submodule_io_name, pos_word)
    PrintDebug( 'Check: get_submodule_io_name_inf: current subcall line can not recognize ! %s '%(pos_line) )
    return False


# this function used to return the io inf for current line
def decode_egreped_verilog_io_line(o_io_line):
    # exp: 
    #   365:output alu_frf_part_p0_w;
    #   366:output [127:0] alu_frf_data_p0_w;
    #   357:output [THR_WIDTH-1:0] alu_dst_cond_tid_w
    #   368:output reg  alu_frf_part_p0_w;
    #   369:output wire [127:0] alu_frf_data_p0_w;
    #   370:output reg  [THR_WIDTH-1:0] alu_dst_cond_tid_w
    #   388:input [width-1 : 0]  A,B;
    # split by ":" |  388:input [width-1 : 0]  A,B;
    # split0       |   0 ^      1        ^  2
    split0    = o_io_line.split(':')
    line_num  = int(split0[0]) - 1   # -1 because egrep form 1, our line from 0
    code_line = ':'.join(split0[1:])
    # valid code line is code_line del note, and change all \s+ to ' '
    # valid_code_line = re.sub('(//.*)|(^\s+)|(\s+$)','',code_line)
    # valid_code_line = (re.sub('//.*','',code_line)).strip()
    valid_code_line = get_valid_code( code_line )
    valid_code_line = re.sub('\s+',' ',valid_code_line)
    valid_code_line = re.sub('\W*$', '',valid_code_line)# del end ";" or ","
    # io type is the first word in valid_code_line
    # fix bug for "module_name ( input ..." can not reconize
    # match_io_type   = re.match('(?P<io_type>\w+)\s*(?P<other>.*)',valid_code_line)
    match_io_type   = re.search( '(^|\W)(?P<io_type>input|output|inout)\s*(?P<other>.*)' ,valid_code_line)
    if not match_io_type: # fix bug for input/output in note
        return {'io_infs':{}, 'name_list':[]}
    io_type         = match_io_type.group('io_type')
    other           = match_io_type.group('other').strip(' ')
    # other: [width-1 : 0]  A,B | wire [127:0] alu_frf_data_p0_w | alu_frf_part_p0_w
    # get name, name is the last word or words sep by ',' ; reverse it and reverse back
    # exp: A | A,B | A,B,C
    match_name = re.match('\s*(?P<r_names_str>\w+(\s*,\s*\w+)*)\s*(?P<r_other>.*)',other[::-1])
    assert(match_name),'%s | %s'%(other,code_line)
    other      = (match_name.group('r_other')[::-1]).strip(' ')
    names_str  = match_name.group('r_names_str')[::-1]
    names      = re.sub('\s+','',names_str).split(',')
    names_pos  = []
    if len(names) == 1:
        colum = re.search('\W%s(\W|$)'%(names[0]),code_line).span()[0] + 1
        names_pos = [ ( line_num, colum ) ]
    else:
        for n in names:
            colum = re.search('\W%s(\W|$)'%(n),code_line).span()[0] + 1
            names_pos.append( (line_num, colum) )
    # signal_type is the first word of other, maybe empty
    # case0 : empty
    # case1 : reg
    # case2 : reg  [THR_WIDTH-1:0]
    # case3 : [127:0]
    signal_type  =  'wire'
    if other:
        match_signal_type = re.match('\s*(?P<signal_type>\w*)\s*(?P<other>.*)',other)
        assert(match_signal_type)
        m_signal_type = match_signal_type.group('signal_type')
        if m_signal_type:
            signal_type = m_signal_type
        other = match_signal_type.group('other').strip(' ')
    # other is empty or [a : b]
    left_index   =  ''
    right_index  =  ''
    size         =  1
    if other:
        assert(other[0] == '[' and other[-1] == ']'),'%s'%(other)
        indexs = other[1:-1].split(':')
        if len(indexs) == 2:
            left_index  = indexs[0].strip(' ')
            right_index = indexs[1].strip(' ')
        try:
            left_index  = int(left_index)
            right_index = int(right_index)
            size        = right_index - left_index + 1
        except:
            size        = other
    # may a line has mulity names
    io_infs = {}
    for i, name in enumerate(names):
        io_infs[name] = {
              "name"        : name
            , "io_type"     : io_type
            , "left"        : left_index
            , "right"       : right_index
            , "size"        : size
            , 'line_num'    : line_num
            , 'name_pos'    : names_pos[i]
            , 'code_line'   : code_line
            , 'signal_type' : signal_type 
        }
    assert(len(io_infs) == len(names))
    return {'io_infs':io_infs, 'name_list':names}

# if has io_name return cur io inf
# else return all io inf of current module
#io_inf = 
    #      "name"        : name
    #    , "io_type"     : io_type
    #    , "left"        : left_index
    #    , "right"       : right_index
    #    , "size"        : size
    #    , 'line_num'    : line_num
    #    , 'name_pos'    : (line_num, colm_num)
    #    , 'code_line'   : code_line
    #    , 'signal_type' : signal_type }
def get_io_inf(module_name, io_name = ''):
    module_inf   = FileInfLib.get_module_inf(module_name)
    if not module_inf:
        PrintReport('Note: module %s database not found!'%(module_name))
        return False
    module_path  = module_inf['file_path']
    module_range = module_inf['module_line_range']
    if io_name: # get cur io inf
        io_inf       = {}
        # io_lines     =  os.popen('sed -n \'%d,%dp\' %s | egrep -n -h \'^\s*(input|output|inout)\>.*\<%s\>\''%(module_range[0]+1, module_range[1]+1, module_path, io_name)).readlines()
        io_lines     =  os.popen('sed -n \'%d,%dp\' %s | egrep -n -h \'(^|\W)(input|output|inout)\>.*\<%s\>\''%(module_range[0]+1, module_range[1]+1, module_path, io_name)).readlines()
        if len(io_lines) == 0:
            PrintReport('RTL Error: not found io: "%s" in module: "%s", path: "%s" !'%(io_name, module_name, module_path))
            return False
        if len(io_lines) > 1:
            l_i = 0
            while l_i < len(io_lines):
                if not re.search('\W%s(\W|$)'%(io_name), re.sub('//.*','',io_lines[l_i])):
                    del io_lines[l_i]
                    continue
                l_i += 1
                continue
            if len(io_lines) > 1:
                PrintReport('RTL Error: module: "%s" \'s io: "%s" define multiple times ! path: "%s" '%(module_name, io_name, module_path))
        line = io_lines[0]
        assert(line.find(io_name) != -1)
        io_inf = decode_egreped_verilog_io_line(line)['io_infs']
        if io_name in io_inf:
            # because use "sed ... | grep ..." so the line number is not the real number need add sed started line num
            # io_inf[io_name]['line_num'] = io_inf[io_name]['line_num'] + module_range[0] 1.2
            io_inf[io_name]['line_num'] = io_inf[io_name]['line_num'] + module_range[0] # decode_egreped_verilog_io_line already -1
            io_inf[io_name]['name_pos'] = ( io_inf[io_name]['line_num'], io_inf[io_name]['name_pos'][1] )
            return io_inf[io_name]
        else:
            PrintReport('Note: not found io: "%s" in module: "%s",maybe a parm name ! path: "%s" !'%(io_name, module_name, module_path))
            return False
    else: # get module all io inf list in order
        all_io_inf    = []
        cur_module_code_range = module_inf['module_line_range']
        # all_io_lines  =  os.popen('sed -n \'%d,%dp\' %s | egrep -n -h \'^\s*(input|output|inout)\>\''%(cur_module_code_range[0]+1, cur_module_code_range[1]+1, module_path)).readlines()
        all_io_lines  =  os.popen('sed -n \'%d,%dp\' %s | egrep -n -h \'(^|\W)(input|output|inout)\>\''%(cur_module_code_range[0]+1, cur_module_code_range[1]+1, module_path)).readlines()
        for line in all_io_lines:
            line      = line.rstrip('\n')
            egrep_io_infs = decode_egreped_verilog_io_line(line)
            io_inf        = egrep_io_infs['io_infs']
            name_list     = egrep_io_infs['name_list']
            if not io_inf:
                PrintDebug('Error: module: %s, line: %s, can not decode by decode_egreped_verilog_io_line() ! file: %s'%(module_name, line, module_path))
                continue
            for io_name in name_list:
                assert(io_name in io_inf)
                c_io_inf = io_inf[io_name]
                c_io_inf['line_num'] = c_io_inf['line_num'] + cur_module_code_range[0]
                c_io_inf['name_pos'] = (c_io_inf['line_num'], c_io_inf['name_pos'][1])
                all_io_inf.append( c_io_inf )
        return all_io_inf


# this function used when cursor on a subcall line
# if cursor word is io_connected signal, get the 
# connect_signal (cursor word) and corresponding submodule io inf
# return ( pos_word, submodule_io_inf)
def get_subcall_connect_inf(submodule_name, subcall_lines, relative_pos):
    # get io_name and pos word
    name_inf = get_submodule_io_name_inf(subcall_lines, relative_pos)
    if name_inf == False:
        PrintDebug('Trace: get_subcall_connect_inf : pos not on valid connect !')
        return False
    submodule_io_name, pos_word = name_inf
    # get submodule io inf
    submodule_io_inf = None
    if type(submodule_io_name) == str: # is io name
        assert(submodule_io_name.strip() != '')
        submodule_io_inf = get_io_inf(submodule_name, submodule_io_name)
        if not submodule_io_inf:
            PrintDebug('Trace: get_subcall_connect_inf: no submodule_io_inf !')
            return False
    else:
        assert(type(submodule_io_name) == int and submodule_io_name >= 0)
        all_submodule_io_inf_list = get_io_inf(submodule_name)
        if not all_submodule_io_inf_list:
            PrintDebug('Trace: get_subcall_connect_inf: no submodule_io_inf !')
            return False
        assert(submodule_io_name < len(all_submodule_io_inf_list)),"%s"%([submodule_io_name, all_submodule_io_inf_list].__str__())
        submodule_io_inf = all_submodule_io_inf_list[submodule_io_name]
    return ( pos_word, submodule_io_inf)


# this function used to get cursor pos line module_inf, subcall_inf, submodule_io_inf
def get_subcall_pos_inf( module_file_path, cursor_pos, file_codes = [] ):
    # get cut line module inf and subcall inf
    subcall_line_inf = FileInfLib.get_file_line_inf(cursor_pos[0], module_file_path)
    if not subcall_line_inf:
        PrintDebug('Trace: get_subcall_pos_inf: has no subcall_line_inf !')
        return False
    module_inf  = subcall_line_inf['module_inf']
    subcall_inf = subcall_line_inf['subcall_inf']
    # if has subcall_inf means cursor no subcall line, get submodule_io_inf, else return false
    if not subcall_inf:
        PrintDebug('Trace: get_subcall_pos_inf: has no subcall_inf.')
        return False
    assert(module_inf), 'has subcall_inf must has module_inf'
    # to get submodule io inf
    if not file_codes:
        assert(os.path.isfile(module_file_path))
        file_codes = open(module_file_path,'r').readlines()
    pos_word            = ''
    submodule_io_inf    = None
    submodule_name      = subcall_inf['submodule_name']
    subcall_line_range  = subcall_inf['subcall_line_range']
    subcall_lines       = file_codes[ subcall_line_range[0] : subcall_line_range[1] + 1 ]
    assert( cursor_pos[0] >= subcall_line_range[0] and cursor_pos[0] <= subcall_line_range[1])
    relative_pos        = (cursor_pos[0] - subcall_line_range[0], cursor_pos[1] )
    subcall_connect_inf = get_subcall_connect_inf(submodule_name, subcall_lines, relative_pos)
    if subcall_connect_inf:
        PrintDebug('Trace: get_subcall_pos_inf: has subcall_connect_inf.')
        pos_word, submodule_io_inf = subcall_connect_inf
    return { 'pos_word'         : pos_word
            ,'submodule_io_inf' : submodule_io_inf
            ,'module_inf'       : module_inf
            ,'subcall_inf'      : subcall_inf }


# this function return a list of index, for level1 bracket comma
def bracket_level1_comma_index_list(code_line, start_bracket_depth):
    # split bracket and comma
    split_by_left_bracket  = code_line.split('(')
    split_by_right_bracket = code_line.split(')')
    split_by_comma         = code_line.split(',')
    # get all the comma appear colum in code_line
    last_comma_y           = -1  # colum in code_line 
    comma_appear_y = []
    for pace in split_by_comma:
        last_comma_y = last_comma_y + len(pace) + 1
        comma_appear_y.append(last_comma_y)
    assert(comma_appear_y[-1] == len(code_line))
    del comma_appear_y[-1:] # del last split pace y
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
    comma_appear_y_set         = set(comma_appear_y)
    left_bracket_appear_y_set  = set(left_bracket_appear_y)
    right_bracket_appear_y_set = set(right_bracket_appear_y)
    assert( not( comma_appear_y_set        & left_bracket_appear_y_set  ) )
    assert( not( comma_appear_y_set        & right_bracket_appear_y_set ) )
    assert( not( left_bracket_appear_y_set & right_bracket_appear_y_set ) )
    active_y = list( comma_appear_y_set | left_bracket_appear_y_set | right_bracket_appear_y_set )
    active_y.sort()
    # for each active_y do follow actions
    cur_bracket_depth               = start_bracket_depth
    valid_comma_y_list              = []
    in_level1_left_bracket_y_list   = []
    out_level1_right_bracket_y_list = []
    for y in active_y:
        if (y in comma_appear_y_set) and cur_bracket_depth == 1:
            valid_comma_y_list.append(y)
        if y in left_bracket_appear_y_set:
            cur_bracket_depth += 1
            if cur_bracket_depth == 1:
                in_level1_left_bracket_y_list.append(y)
        if y in right_bracket_appear_y_set:
            cur_bracket_depth -= 1
            if cur_bracket_depth == 0:
                out_level1_right_bracket_y_list.append(y)
    return { 'end_bracket_depth'               : cur_bracket_depth
            ,'valid_level1_comma_y_list'       : valid_comma_y_list
            ,'in_level1_left_bracket_y_list'   : in_level1_left_bracket_y_list
            ,'out_level1_right_bracket_y_list' : out_level1_right_bracket_y_list
    } 

# for count bracket deepth for comma, when find subcall io connect
# need treat below char to bracket
def treat_by_bracket_fmt( line ):
    # for not count { a, b, c} at signal connect assign
    line = line.replace('{','(')
    line = line.replace('}',')')
    return line


# this function used to find the subcall io connect signal pos by submodule io index
def get_subcall_io_connect_signal_pos_from_io_index(io_index, subcall_inf, upper_module_codes):
    submodule_name  = subcall_inf['submodule_name']
    instance_name   = subcall_inf['instance_name']
    subcall_range   = subcall_inf['subcall_line_range']
    # find the io connect start left bracket pos
    # case0.0: module_name          instance_name(a,b...
    # case0.1: module_name #(x,y,z) instance_name(a,b...
    # case1: instance_name(a,bc...)
    #        module_name instance0(...),
    #                    instance1(...);
    # case2: module_name instance_name();
    io_connect_init_left_brackek_x = -1 # line number
    io_connect_init_left_brackek_y = -1 # colum number
    pre_valid_code  = ''
    post_valid_code = '' # valid code from left bracket pos
    next_line_index = subcall_range[0]
    max_line_index  = subcall_range[1] + 1
    patten_module   = '%s'%(submodule_name)
    patten_instance = '%s\s*(\[[^\[\]]*\])?'%(instance_name)
    patten_post     = '(?P<post_part>\(.*)'
    code_to_current_line = ''
    post_valid_code      = ''
    while next_line_index < max_line_index:
        cur_index_code = get_valid_code(upper_module_codes[next_line_index].strip('\n'))
        cur_line_index = next_line_index
        next_line_index += 1
        pre_line_code_length = len(code_to_current_line) + 1 # +1 because add a space between two line
        code_to_current_line = code_to_current_line + ' ' + cur_index_code
        match_case0 = re.match('(?P<pre_part>\s*%s\W(.*\W)?%s\s*)%s'%(patten_module, patten_instance, patten_post), code_to_current_line)
        if match_case0:
            post_valid_code = match_case0.group('post_part')
            io_connect_init_left_brackek_x = cur_line_index
            io_connect_init_left_brackek_y = len(match_case0.group('pre_part')) - pre_line_code_length
            break
        match_case1 = re.match('(?P<pre_part>\s*(,)?\s*%s\s*)%s'%(patten_instance, patten_post), code_to_current_line)
        if match_case1:
            post_valid_code = match_case1.group('post_part')
            io_connect_init_left_brackek_x = cur_line_index
            io_connect_init_left_brackek_y = len(match_case1.group('pre_part')) - pre_line_code_length
            break
    assert(io_connect_init_left_brackek_x != -1)
    # from io connect start left bracket pos to subcall end to get the real 
    # connect single inf
    indexed_io_connect_pre_comma_pos  = ()
    io_index_relative_to_current_line = io_index
    cur_bracket_depth     = 0
    cur_valid_code        = post_valid_code
    cur_comma_inf         = bracket_level1_comma_index_list( treat_by_bracket_fmt(cur_valid_code), cur_bracket_depth)
    # leve1 in left bracket follow a io_connect so need add it
    cur_full_comma_y_list = cur_comma_inf['in_level1_left_bracket_y_list'] + cur_comma_inf['valid_level1_comma_y_list']
    cur_full_comma_y_list.sort()
    cur_finded_io_connect_num = len( cur_full_comma_y_list )
    cur_bracket_depth = cur_comma_inf['end_bracket_depth']
    # io_index_relative_to_current_line = io_index_relative_to_current_line - cur_finded_io_connect_num
    # if still not find the last comma, looped to find it until subcall end
    # i = io_connect_init_left_brackek_x + 1
    still_in_init_line = 1
    while not (io_index_relative_to_current_line < cur_finded_io_connect_num) and (next_line_index < max_line_index):
        still_in_init_line = 0
        cur_valid_code    = get_valid_code(upper_module_codes[next_line_index].strip('\n'))
        cur_line_index    = next_line_index
        next_line_index   += 1
        io_index_relative_to_current_line = io_index_relative_to_current_line - cur_finded_io_connect_num
        cur_comma_inf     = bracket_level1_comma_index_list( treat_by_bracket_fmt(cur_valid_code) , cur_bracket_depth)
        cur_bracket_depth = cur_comma_inf['end_bracket_depth']
        cur_full_comma_y_list = cur_comma_inf['in_level1_left_bracket_y_list'] + cur_comma_inf['valid_level1_comma_y_list']
        cur_full_comma_y_list.sort()
        cur_finded_io_connect_num = len( cur_full_comma_y_list )
    # assert(io_index_relative_to_current_line < cur_finded_io_connect_num)
    if not (io_index_relative_to_current_line < cur_finded_io_connect_num):
        return () # for case 2
    indexed_io_connect_pre_comma_pos = ( next_line_index - 1, cur_full_comma_y_list[io_index_relative_to_current_line] )
    # from comma pos to get the first valid word and treat that as the subcall io connect key pos
    comma_or_init_bracket_pos = cur_full_comma_y_list[io_index_relative_to_current_line]
    post_part  = cur_valid_code[comma_or_init_bracket_pos:]
    assert(post_part[0] in [',','('] ),'%s'%(post_part)
    search_key = re.search('\w',post_part)
    match_in_first_line = 1
    while (not search_key) and (next_line_index < max_line_index):
        cur_bracket_depth = cur_comma_inf['end_bracket_depth']
        cur_valid_code    = get_valid_code(upper_module_codes[next_line_index].strip('\n'))
        cur_line_index    = next_line_index
        next_line_index += 1
        search_key = re.search('\w',cur_valid_code)
        if search_key:
            match_in_first_line = 0
    # assert(search_key)
    if not search_key: # for case2: module_name instance_name(); should no search key
        return () # for case 2
    key_x = next_line_index - 1
    key_y = (io_connect_init_left_brackek_y*still_in_init_line + comma_or_init_bracket_pos)*match_in_first_line + search_key.span()[0]
    return (key_x, key_y)


# this function used to get the upper module io inf
def get_upper_module_call_io_inf(cur_module_name , cur_io_name, report_level = 1):
    cur_module_last_call_inf = FileInfLib.get_module_last_call_inf(cur_module_name)
    if not cur_module_last_call_inf:
        PrintReport("Note: module %s not called before, no upper module !"%(cur_module_name), report_level = report_level )
        return False
    upper_module_inf   = cur_module_last_call_inf['upper_module_inf']
    assert(upper_module_inf),'upper module %s call %s before, upper should has inf in database !'%(upper_module_name, cur_module_name)
    upper_module_name  = upper_module_inf['module_name']
    upper_subcall_inf  = cur_module_last_call_inf['upper_subcall_inf']
    # for case subcall recoginize not accuracy, may because of '`ifdef, `endif ...'
    if upper_subcall_inf['inaccuracy']: 
        PrintReport('Warning: carefull the trace result, subcall module:%s, instance:%s inaccuracy !'%(upper_subcall_inf['module_name'], upper_subcall_inf['instance_name']))
    upper_module_path  = upper_module_inf['file_path']
    # get upper call, match this signal pos
    # case0: .xxx(yyy) case use egrep get thesignal pos
    subcall_range = upper_subcall_inf['subcall_line_range']
    # sed -n 'a,bp', a count from 1, so subcall_range[0]/[1] need +1
    # pos: a -> b , sed : a+1 -> b+1, egrep: 1 -> 1+b-a = k, => b = k + a -1 
    # cur_io_matched_upper_connect_lines  =  os.popen('sed -n \'%d,%dp\' %s | egrep -n -h \'\.\s*%s\s*\(\''%(subcall_range[0] + 1, subcall_range[1] + 1, upper_module_path, cur_io_name)).readlines()
    cur_io_matched_upper_connect_lines  =  os.popen('sed -n \'%d,%dp\' %s | egrep -n -h \'\.\s*%s(\W|$)\''%(subcall_range[0] + 1, subcall_range[1] + 1, upper_module_path, cur_io_name)).readlines()
    for egrep_l in cur_io_matched_upper_connect_lines:
        split_rst = (egrep_l.strip('\n')).split(':')
        line_num  = int(split_rst[0]) + subcall_range[0] - 1
        code_line = ':'.join(split_rst[1:])
        valid_code_line = re.sub('//.*','',code_line)
        # valid_match = re.match('(?P<pre_char>.*\.\s*)%s\s*\('%(cur_io_name),valid_code_line)
        valid_match = re.match('(?P<pre_char>.*\.\s*)%s(\W|$)'%(cur_io_name),valid_code_line)
        if valid_match:
            colum_num = len(valid_match.group('pre_char'))
            cur_io_upper_connect_line = code_line
            cur_io_upper_connect_pos  = (line_num, colum_num)
            return { 'upper_module_name'       : upper_module_name
                    ,'upper_module_path'       : upper_module_path
                    ,'io_upper_connect_line'   : cur_io_upper_connect_line
                    ,'io_upper_connect_signal' : cur_io_name
                    ,'io_upper_connect_pos'    : cur_io_upper_connect_pos }
    # case 1: 
    #   module_name instance_name (a,b,c)
    #   module_name #() instance_name (a,b,c)
    upper_module_codes = open(upper_module_path,'r').readlines()
    # get the current io name index in ordered all module io
    cur_io_index = -1
    submodule_name       = upper_subcall_inf['submodule_name']
    all_submodule_io_inf = get_io_inf(submodule_name)
    for i,inf in enumerate(all_submodule_io_inf):
        if inf['name'] == cur_io_name:
            cur_io_index = i
            break
    assert(cur_io_index != -1)
    # get the io_connect_line_inf
    io_connect_signal_pos = get_subcall_io_connect_signal_pos_from_io_index(cur_io_index, upper_subcall_inf, upper_module_codes)
    if not io_connect_signal_pos:
        PrintReport('Warning: not find io connect, current module:%s io :%s, upper module: %s '%(cur_module_name, cur_io_name, upper_module_name), report_level = report_level )
        return False
    match_io_upper_connect_signal = re.match('(?P<match_name>\w+)', upper_module_codes[io_connect_signal_pos[0]][io_connect_signal_pos[1]:])
    # assert(match_io_upper_connect_signal),'valid io connect signal pos:"%s", must be a valid word !'%(io_connect_signal_pos.__str__())
    if match_io_upper_connect_signal: 
        io_upper_connect_signal = match_io_upper_connect_signal.group('match_name')
    else: # for subcall like: module instance(); should not match
        io_upper_connect_signal = ''
    return { 'upper_module_name'       : upper_module_name
            ,'upper_module_path'       : upper_module_path
            ,'io_upper_connect_line'   : upper_module_codes[io_connect_signal_pos[0]]
            ,'io_upper_connect_signal' : io_upper_connect_signal
            ,'io_upper_connect_pos'    : io_connect_signal_pos }


def current_appear_is_dest_or_source(key, code_lines, appear_pos):
    a_x, a_y         = appear_pos
    appear_code_line = get_valid_code( code_lines[a_x] )
    # case 0 cur pos in note return not source and dest
    if len(appear_code_line) - 1 < a_y:
        return 'unkonwn'
    # case 1 is io
    match_io = re.match('\s*(?P<io_type>(input|inout|output))\W', appear_code_line)
    if match_io:
        # incase key is not a valid signal, such as "input"
        match_io_name = re.match('\s*[;,]?\s*(?P<r_names>\w+(\s*,\s*\w+)*)',appear_code_line[::-1]) # may input a,b,c
        if match_io_name:
            io_names = match_io_name.group('r_names')[::-1]
            io_names = set(re.split('\s*,\s*',io_names))
            if key in io_names:
                if match_io.group('io_type') == 'input':
                    return 'source'
                if match_io.group('io_type') == 'output':
                    return 'dest'
                if match_io.group('io_type') == 'inout':
                    return 'source_and_dest'
        PrintDebug('Error: recognize_signal_assign_line: unrecognize io line: '+appear_code_line)
        return 'unkonwn'
    # case 2 cur pos in case/casez/for/if (...key...) then it's dest
    # this must put before assign to must case as: if(key) asas <= 
    #     key in if(...) so this is dest not source
    pre_full_line = get_verilog_pre_full_line(code_lines, appear_pos)
    case2_patten = 'case|casez|for|if|while|always'
    # find the last case2 match
    r_pre_full_line = pre_full_line[::-1]
    r_case2_patten  = case2_patten[::-1]
    r_march_case2   = re.search('(^|\W)(%s)(\W|$)'%(r_case2_patten), r_pre_full_line)
    if r_march_case2:
        r_match_y        = r_march_case2.span()[1]
        case2_match_code = (r_pre_full_line[:r_match_y+1])[::-1]
        index_inf        = get_bracket_pair_index(case2_match_code, 0)
        # just in bracket and not out means it's dest
        if (len(index_inf['in_level1_left_bracket_y_list']) == 1) and (len(index_inf['out_level1_right_bracket_y_list']) == 0):
            return 'dest'
    # case 3 check assign case
    assign_patten = '(\s|\w|^)(=|<=)(\s|\w|$)'
    # (1) check pre_full_line for dest, exp: ... <= key
    search_dest = re.search(assign_patten, pre_full_line)
    if search_dest:
        match_right_part = pre_full_line[search_dest.span()[0]+1:]
        # fix bug : for(...;xx = xx) ... key ; this not dest 
        # ... =|<= key, key must not leave =|<= scope
        # check it by assume has "(" at =|<= left, and 
        # make sure not leave this bracket 
        index_inf        = get_bracket_pair_index(match_right_part, 1)
        if len(index_inf['out_level1_right_bracket_y_list']) == 0:
            return 'dest'
    # (2) check current line for source
    # most case current line has =|<=
    if re.search(assign_patten, appear_code_line[a_y:]):
        return 'source'
    # (3) post full line sep by ";" has =|<=, it's source
    post_full_line = get_verilog_post_full_line(code_lines, appear_pos)
    if re.search(assign_patten, post_full_line):
        return 'source'
    # other case treat as false
    return 'unkonwn'


def clear_last_trace_inf( trace_type = 'both' ):
    trace_type = 'both' # i thing each time clear all is much more friendly
    if trace_type in ['source','both']:
        G['TraceInf']['LastTraceSource']['Maybe']          = []
        G['TraceInf']['LastTraceSource']['Sure']           = []
        G['TraceInf']['LastTraceSource']['ShowIndex']      = 0
        G['TraceInf']['LastTraceSource']['SignalName']     = ''
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = [-1,-1]
        G['TraceInf']['LastTraceSource']['Path']           = ''
    if trace_type in ['dest','both']:
        G['TraceInf']['LastTraceDest']['Maybe']            = []
        G['TraceInf']['LastTraceDest']['Sure']             = []
        G['TraceInf']['LastTraceDest']['ShowIndex']        = 0
        G['TraceInf']['LastTraceDest']['SignalName']       = ''
        G['TraceInf']['LastTraceDest']['ValidLineRange']   = [-1,-1]
        G['TraceInf']['LastTraceDest']['Path']             = ''


# this function trace the signal when need crose module from
# submodule io line to upper module subcall line
def real_trace_io_signal(trace_type, cursor_inf, io_signal_inf, report_level = 1):
    assert(trace_type in ['dest', 'source']),'only trace dest/source'
    # verilog
    if (trace_type is 'dest') and (io_signal_inf['io_type'] != 'output'):
        PrintDebug('Trace: real_trace_io_signal: not output signal, not dest')
        return False # not output signal, not dest
    if (trace_type is 'source') and (io_signal_inf['io_type'] != 'input'):
        PrintDebug('Trace: real_trace_io_signal: not input signal, not source')
        return False # not input signal, not source
    # trace a input signal
    clear_last_trace_inf( trace_type )  # clear pre trace dest/source result
    cur_module_inf     = None
    cur_line_inf       = FileInfLib.get_file_line_inf(cursor_inf['line_num'], cursor_inf['file_path'])
    if cur_line_inf:
        cur_module_inf = cur_line_inf['module_inf']
    if not cur_module_inf:
        if not cur_line_inf('hdl_type'):
            PrintReport('Warning: current cursor no module found, unsupport postfix "%s" !'%(get_file_path_postfix(cur_line_inf['file_path'])), report_level = report_level)
            return True
        PrintReport('Warning: current cursor no module found ! ', report_level = report_level)
        return True
    cur_module_name  = cur_module_inf['module_name']
    upper_module_call_inf = get_upper_module_call_io_inf(cur_module_name , io_signal_inf['name'], report_level = report_level)
    if not upper_module_call_inf:
        # if no upper call just get all upper module and maunlly choise one as upper
        trace_upper_inf = {  'trace_type'  :trace_type
                            ,'cursor_inf'  :cursor_inf
                            ,'report_level':report_level }
        line_and_link_list = get_upper_module_line_and_link_list( cur_module_name, trace_upper_inf = trace_upper_inf )
        if not line_and_link_list:
            return True
        # i = 0 
        link_list = []
        line_list = []
        # pre inf
        line_list.append('Knock "<Space>" to choise upper module you want trace to: ')
        line_list.append('')
        link_list.append( {} )
        link_list.append( {} )
        line_list += line_and_link_list['line_list']
        link_list += line_and_link_list['link_list']
        mounted_line_inf  = MountPrintLines(line_list, label = 'Possible Trace Upper', link_list = link_list)
        mounted_line_list = mounted_line_inf['line_list']
        mounted_link_list = mounted_line_inf['link_list']
        # add a empty line below
        mounted_line_list.append('')
        mounted_link_list.append({})
        add_trace_point()
        assert( len(mounted_line_list) == len(mounted_link_list) )
        PrintReport(mounted_line_list, mounted_link_list, MountPrint = True )
        if len(line_and_link_list['line_list']) == 1:
            for link in link_list:
                if link:
                    do_hyperlink(link, ['add_module_last_call_action', 'trace_io_signal_action']) # first valid link
                    break
        else:
            # len(mounted_line_list) + 1 is the lines relative to the last report line
            # -4 is skip first 4 unused line
            go_win( G['Report_Inf']['Report_Path'] , (-(len(mounted_line_list) + 1 -4), 57) )
        return True # this dest/source but not found upper module
    # has upper module go to upper module call location
    upper_module_name   = upper_module_call_inf['upper_module_name']
    upper_call_pos      = upper_module_call_inf['io_upper_connect_pos']
    upper_call_line     = upper_module_call_inf['io_upper_connect_line']
    upper_module_path   = upper_module_call_inf['upper_module_path']
    upper_signal_name   = upper_module_call_inf['io_upper_connect_signal']
    show_str            = '%s %d : %s'%(upper_module_name, upper_call_pos[0]+1, upper_call_line)
    file_link_parm_dic  = { 'type'             : 'trace_result'
                           ,'last_modify_time' : os.path.getmtime( upper_module_path )
                           ,'go_path'          : upper_module_path
                           ,'go_pos'           : upper_call_pos
                           ,'go_word'          : upper_signal_name }
    file_link           = gen_hyperlink('go_file_action', file_link_parm_dic)
    trace_result        = {'show': show_str, 'file_link': file_link}
    if trace_type is 'dest':
        G['TraceInf']['LastTraceDest']['Sure'].append(trace_result)
        G['TraceInf']['LastTraceDest']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceDest']['ValidLineRange'] = cur_module_inf['module_line_range']
        G['TraceInf']['LastTraceDest']['Path']           = cursor_inf['file_path']
    else :
        G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
        G['TraceInf']['LastTraceSource']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = cur_module_inf['module_line_range']
        G['TraceInf']['LastTraceSource']['Path']           = cursor_inf['file_path']
    # show dest/source to report win, and go first trace
    PrintReport(spec_case = trace_type)
    show_next_trace_result(trace_type)
    return True


# if current is a io signal report the io_infs,
# else return false
def recognize_io_signal_line(line, line_num):
    # pre check if is not io
    if line.find('input') == -1 and line.find('output') == -1:
        return False
    line = line.strip('\n')
    line = re.sub('//.*','',line) # del notes
    # raw re match
    re_match = re.match('\s*(input|output)\W',line)
    # for module ( input ... case
    if not re_match:
        re_match = re.match('(?P<prefix>.*\(\s*)(?P<real_io>(input|output)\W.*)',line)
        if re_match:
            prefix       = re_match.group('prefix')
            real_io_line = re_match.group('real_io')
            line         = ' '*(len(prefix)) + real_io_line
        else:
            return False
    # match used egrep io line decode function
    egrep_io_line = str(line_num)+':'+line
    io_infs = decode_egreped_verilog_io_line(egrep_io_line)['io_infs']
    return io_infs
    #      "name"        : name
    #    , "io_type"     : io_type
    #    , "left"        : left_index
    #    , "right"       : right_index
    #    , "size"        : size
    #    , 'line_num'    : line_num
    #    , 'name_pos'    : (line_num, colm_num)
    #    , 'code_line'   : code_line
    #    , 'signal_type' : signal_type }


# this function trace the signal when need crose module from
# submodule io line to upper module subcall line
def trace_io_signal(trace_type, cursor_inf, report_level = 1):
    trace_signal_name  = cursor_inf['word']
    io_signal_infs     = recognize_io_signal_line(cursor_inf['line'], cursor_inf['line_num'])
    if not io_signal_infs:
        PrintDebug('Trace: trace_io_signal: not io signal')
        return False # not io signal
    # is io line but trace not a io signal, maybe 
    # macro define, such as [`EXP_MACRO:0] ...
    if trace_signal_name not in io_signal_infs:
        PrintDebug('Trace: trace_io_signal: is io signal but not traced signal')
        return False 
    if trace_type in ['source','dest']:
        return real_trace_io_signal(trace_type, cursor_inf, io_signal_infs[trace_signal_name], report_level = report_level)
    assert(0),'unkonw tarce type %s' %(trace_type)
# hyperlink action trace_io_signal_action
def trace_io_signal_action(trace_type, cursor_inf, report_level):
    trace_io_signal(trace_type, cursor_inf, report_level)
register_hyperlink_action( trace_io_signal_action, description = 'this link function use to trace input cursor io ' )


# this function used when current is really a subcall and get subcall inf
# add subcall io line to trace result and go to submodule io line
def real_trace_signal_at_subcall_lines(trace_type, subcall_cursor_inf, cursor_inf, report_level = 1):
    assert(trace_type in ['source', 'dest'])
    if trace_type == 'source' and subcall_cursor_inf['submodule_io_inf']['io_type'] != 'output':
        return False # submodule not source, just pass
    elif trace_type == 'dest' and subcall_cursor_inf['submodule_io_inf']['io_type'] != 'input':
        return False # submodule not source, just pass
    # has sub module and in submodule signal is out, then it's source
    subcall_inaccuracy        = subcall_cursor_inf['subcall_inf']['inaccuracy']
    submodule_name            = subcall_cursor_inf['subcall_inf']['submodule_name']
    if subcall_inaccuracy: # for case subcall recoginize not accuracy, may because of '`ifdef, `endif ...'
        PrintReport('Warning: carefull the trace result !  current cursor subcall module:%s, instance:%s inaccuracy !'%(submodule_name, subcall_cursor_inf['subcall_inf']['instance_name']))
    submodule_inf             = FileInfLib.get_module_inf(submodule_name)
    assert(submodule_inf)
    submodule_path            = submodule_inf['file_path']
    submodule_matched_io_pos  = subcall_cursor_inf['submodule_io_inf']['name_pos']
    submodule_matched_io_line = subcall_cursor_inf['submodule_io_inf']['code_line']
    submodule_matched_io_name = subcall_cursor_inf['submodule_io_inf']['name']
    show_str                  = '%s %d : %s'%(submodule_name, submodule_matched_io_pos[0]+1, submodule_matched_io_line)
    file_link_parm_dic        = { 'type'             : 'trace_result'
                                 ,'last_modify_time' : os.path.getmtime( submodule_path )
                                 ,'go_path'          : submodule_path
                                 ,'go_pos'           : submodule_matched_io_pos
                                 ,'go_word'          : submodule_matched_io_name }
    file_link                 = gen_hyperlink('go_file_action', file_link_parm_dic)
    trace_result              = {'show': show_str, 'file_link': file_link}
    if trace_type == 'source':
        G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
        G['TraceInf']['LastTraceSource']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = ( cursor_inf['line_num'], cursor_inf['line_num'] )
        G['TraceInf']['LastTraceSource']['Path']           = cursor_inf['file_path']
    else: # dest
        G['TraceInf']['LastTraceDest']['Sure'].append(trace_result)
        G['TraceInf']['LastTraceDest']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceDest']['ValidLineRange'] = ( cursor_inf['line_num'], cursor_inf['line_num'] )
        G['TraceInf']['LastTraceDest']['Path']           = cursor_inf['file_path']
    # go to sub module code now, so cur module is the sub module last call
    cur_module_name           = subcall_cursor_inf['module_inf']['module_name']
    subcall_instance_name     = subcall_cursor_inf['subcall_inf']['instance_name']
    FileInfLib.set_module_last_call_inf(submodule_name, cur_module_name, subcall_instance_name)
    # show source to report win, and go first trace
    PrintReport(spec_case = trace_type)
    show_next_trace_result(trace_type)
    return True


# this function used to trace signal at subcall lines 
def trace_signal_at_subcall_lines(trace_type, cursor_inf, report_level = 1):
    subcall_cursor_inf = get_subcall_pos_inf(cursor_inf['file_path'], cursor_inf['pos'], cursor_inf['codes'])
    if not subcall_cursor_inf:
        PrintDebug('Trace: trace_signal_at_subcall_lines: cursor not at subcall lines !')
        return False # not in module call io
    if not subcall_cursor_inf['submodule_io_inf']:
        PrintDebug('Trace: trace_signal_at_subcall_lines: is module call , no submodule_io_inf !')
        return False
    clear_last_trace_inf( trace_type )
    return real_trace_signal_at_subcall_lines(trace_type, subcall_cursor_inf, cursor_inf, report_level = report_level)

# this function used to trace signal for normal case
def real_trace_normal_signal(trace_type, signal_appear_pos_line, cursor_inf):
    assert(trace_type in ['source', 'dest'])
    trace_signal_name  = cursor_inf['word']
    cur_module_inf     = None
    cur_line_inf       = FileInfLib.get_file_line_inf(cursor_inf['line_num'], cursor_inf['file_path'])
    if cur_line_inf:
        cur_module_inf = cur_line_inf['module_inf'] 
    assert(cur_module_inf) # already qualify
    cur_module_name    = cur_module_inf['module_name']
    cur_module_path    = cur_module_inf['file_path']
    # initial the trace inf
    clear_last_trace_inf(trace_type)
    if trace_type == 'source':
        G['TraceInf']['LastTraceSource']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = cur_module_inf['module_line_range']
        G['TraceInf']['LastTraceSource']['Path']           = cursor_inf['file_path']
    else: 
        G['TraceInf']['LastTraceDest']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceDest']['ValidLineRange'] = cur_module_inf['module_line_range']
        G['TraceInf']['LastTraceDest']['Path']           = cursor_inf['file_path']
    # add optimizing for signal such like clk, used by many times, but only io, or sub call is source
    input_is_only_source = False
    if trace_type == 'source' and len(signal_appear_pos_line) > G['TraceInf']['TraceSourceOptimizingThreshold']:
        for appear_pos, appear_line in signal_appear_pos_line:
            signal_appear_line = cursor_inf['codes'][appear_pos[0]]
            if signal_appear_line.find('input') == -1:
                continue
            dest_or_source = current_appear_is_dest_or_source( trace_signal_name, [signal_appear_line], (0,appear_pos[1]) )
            if dest_or_source in ['source', 'source_and_dest']:
                input_is_only_source = True
                show_str = '%s %d : %s'%(cur_module_name, appear_pos[0]+1, appear_line)
                file_link_parm_dic = {   'type'             : 'trace_result'
                                        ,'last_modify_time' : os.path.getmtime( cur_module_path )
                                        ,'go_path'          : cur_module_path
                                        ,'go_pos'           : appear_pos
                                        ,'go_word'          : trace_signal_name }
                file_link    = gen_hyperlink('go_file_action', file_link_parm_dic)
                trace_result = {'show': show_str, 'file_link': file_link}
                G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
                break
    # if found a input as source, should be the only source, clear appear pos to jump, normal search
    if input_is_only_source:
        signal_appear_pos_line = []
    # appear_pos (line number, column), deal each match to find source
    for appear_pos, appear_line in signal_appear_pos_line:
        appear_dest_or_source     = False
        appear_is_dest            = False
        appear_is_source          = False
        # check if a io or assign signal
        dest_or_source = current_appear_is_dest_or_source( trace_signal_name, cursor_inf['codes'], appear_pos )
        if dest_or_source in ['source', 'source_and_dest']:
            appear_is_source = True
        if dest_or_source in ['dest', 'source_and_dest']:
            appear_is_dest   = True
        # not assign signal check module call
        submodule_and_subinstance = ''
        if not (appear_is_dest or appear_is_source):
            subcall_cursor_inf = get_subcall_pos_inf(cur_module_path, appear_pos, cursor_inf['codes'])
            if subcall_cursor_inf:
                # cur is subcall but not io name not match trace name go next
                if not subcall_cursor_inf['submodule_io_inf']:
                    appear_dest_or_source = True
                elif subcall_cursor_inf['submodule_io_inf']['io_type'] in ['output', 'inout']:
                    assert(trace_signal_name == subcall_cursor_inf['pos_word']),'%s != %s'%(trace_signal_name, subcall_cursor_inf['pos_word'])
                    appear_is_source      = True
                    submodule_and_subinstance = ':%s(%s)'%(subcall_cursor_inf['subcall_inf']['instance_name'],subcall_cursor_inf['subcall_inf']['submodule_name'])
                    # for case subcall recoginize not accuracy, may because of '`ifdef, `endif ...'
                    if subcall_cursor_inf['subcall_inf']['inaccuracy']: 
                        PrintReport('Warning: carefull the trace result, subcall module:%s, instance:%s inaccuracy !'%(subcall_cursor_inf['subcall_inf']['module_name'], subcall_cursor_inf['subcall_inf']['instance_name']))
                elif subcall_cursor_inf['submodule_io_inf']['io_type'] in ['input','inout']:
                    assert(trace_signal_name == subcall_cursor_inf['pos_word']),'%s != %s'%(trace_signal_name, subcall_cursor_inf['pos_word'])
                    appear_is_dest        = True
                    submodule_and_subinstance = ':%s(%s)'%(subcall_cursor_inf['subcall_inf']['instance_name'],subcall_cursor_inf['subcall_inf']['submodule_name'])
                    # for case subcall recoginize not accuracy, may because of '`ifdef, `endif ...'
                    if subcall_cursor_inf['subcall_inf']['inaccuracy']: 
                        PrintReport('Warning: carefull the trace result, subcall module:%s, instance:%s inaccuracy !'%(subcall_cursor_inf['subcall_inf']['module_name'], subcall_cursor_inf['subcall_inf']['instance_name']))
                else:
                    appear_dest_or_source = True
            else:
                appear_dest_or_source = True
        assert(appear_is_source or appear_is_dest or appear_dest_or_source),'appear: "%s" must be some case !'%(appear_line)
        assert( not ((appear_is_source or appear_is_dest) and appear_dest_or_source) ),'appear: "%s" if is dest or source , should not be maybe'%(appear_line)
        # finial add to source/dest
        show_str = '%s %d : %s'%(cur_module_name+submodule_and_subinstance, appear_pos[0]+1, appear_line)
        file_link_parm_dic = {  'type'             : 'trace_result'
                                ,'last_modify_time' : os.path.getmtime( cur_module_path )
                                ,'go_path'          : cur_module_path
                                ,'go_pos'           : appear_pos
                                ,'go_word'          : trace_signal_name }
        file_link    = gen_hyperlink('go_file_action', file_link_parm_dic)
        trace_result = {'show': show_str, 'file_link': file_link}
        if trace_type == 'source':
            if appear_dest_or_source:
                G['TraceInf']['LastTraceSource']['Maybe'].append(trace_result)
            elif appear_is_source:
                G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
        else: # trace dest
            if appear_dest_or_source:
                G['TraceInf']['LastTraceDest']['Maybe'].append(trace_result)
            elif appear_is_dest:
                G['TraceInf']['LastTraceDest']['Sure'].append(trace_result)
        continue
    # finish get all dest/source
    if trace_type == 'source':
        finded_source_num       = len(G['TraceInf']['LastTraceSource']['Sure'])
        finded_maybe_source_num = len(G['TraceInf']['LastTraceSource']['Maybe'])
        # not find signal source
        if not (finded_source_num + finded_maybe_source_num):
            PrintReport("Note: Not find signal source !")
            return True
    else: # dest
        finded_dest_num       = len(G['TraceInf']['LastTraceDest']['Sure'])
        finded_maybe_dest_num = len(G['TraceInf']['LastTraceDest']['Maybe'])
        # not find signal dest
        if not (finded_dest_num + finded_maybe_dest_num):
            PrintReport("Note: Not find signal dest !")
            return True
    # show source to report win, and go first trace
    PrintReport(spec_case = trace_type)
    show_next_trace_result(trace_type)
    return True


def trace_normal_signal(trace_type, cursor_inf):
    cur_module_inf   = None
    cur_line_inf     = FileInfLib.get_file_line_inf(cursor_inf['line_num'], cursor_inf['file_path'])
    if cur_line_inf:
        cur_module_inf = cur_line_inf['module_inf']  
    if not cur_module_inf:
        PrintDebug('Trace: cur file has no module inf, may be no database or cur line not in module, file: %s '%(cursor_inf['file_path']))
        return False
    # just use grep get all signal appear in current file to speed up signal search
    signal_appear_pos_line = search_verilog_code_use_grep( cursor_inf['word'], cursor_inf['file_path'], cur_module_inf['module_line_range'] )
    return real_trace_normal_signal(trace_type, signal_appear_pos_line, cursor_inf)


# this function used to trace macro
def trace_glb_define_signal(trace_type, cursor_inf):
    assert(trace_type in ['dest', 'source'])
    cur_word  = cursor_inf['word']
    cur_line  = cursor_inf['line']
    if cur_line.find('`') == -1: # bucause most case not trace macro, so it's worth pre check
        PrintDebug('Trace: trace_glb_define_signal: %s not macro_name !'%(cur_word))
        return False
    # ...`XXX...
    #      ^        cursor pos
    #     XXX       cur word
    # ...`XX        pre_pos_part
    pre_pos_part = cur_line[:cursor_inf['pos'][1] + 1]
    match_macro  = re.match('\w+`' , pre_pos_part[::-1])
    if not match_macro:
        PrintDebug('Trace: trace_glb_define_signal: %s not macro_name !'%(cur_word))
        return False
    # no matter get trace result or not trace done, need clear old trace result
    clear_last_trace_inf(trace_type)
    # cur_word is macro get macro inf list
    cur_macro_inf_list = FileInfLib.get_macro_inf_list( cur_word )
    if not cur_macro_inf_list:
        PrintReport('Warning: not find macro: %s define in design !'%(cur_word))
        return True
    # if trace_type == 'dest': for macro no dest just source
    if trace_type == 'dest':
        PrintReport('None: macro: %s can not trace dest, only support trace source !'%(cur_word))
        return True
    # valid trace macro source
    for macro_inf in cur_macro_inf_list: # {name path pos code_line}
        file_name    = re.sub('.*/','',macro_inf['file_path'])
        show_str     = '%s %d : %s'%(file_name, macro_inf['macro_name_match_pos'][0]+1, macro_inf['code_line'])
        file_link_parm_dic  = { 'type'             : 'trace_result'
                               ,'last_modify_time' : os.path.getmtime( macro_inf['file_path'] )
                               ,'go_path'          : macro_inf['file_path']
                               ,'go_pos'           : macro_inf['macro_name_match_pos']
                               ,'go_word'          : cur_word }
        file_link           = gen_hyperlink('go_file_action', file_link_parm_dic)
        trace_result = {'show': show_str, 'file_link': file_link}
        G['TraceInf']['LastTraceSource']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = (cursor_inf['line_num'], cursor_inf['line_num'])
        G['TraceInf']['LastTraceSource']['Path']           = cursor_inf['file_path']
        G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
    # show source to report win, and go first trace
    PrintReport(spec_case = trace_type)
    show_next_trace_result(trace_type)
    return True

def get_upper_module_line_and_link_list( cur_module_name, trace_upper_inf = {} ):
    # even has upper, also should list all the poss upper
    call_me_subcall_inf_list = FileInfLib.get_call_me_subcall_inf_list( cur_module_name )
    if call_me_subcall_inf_list:
        # i = 0 
        link_list = []
        line_list = []
        stale_call_me_subcall_inf_list = []
        for i, subcall_inf in enumerate(call_me_subcall_inf_list):
            if check_inf_valid( subcall_inf['file_path'], subcall_inf['last_modify_time']):
                c_file_link = None
                c_print_str = None
                if not trace_upper_inf: # must go upper
                    c_file_link_parm_dic    = {  'type'                : 'possible_upper'
                                                # for go_file_action
                                                ,'last_modify_time'    : os.path.getmtime( subcall_inf['file_path'] )
                                                ,'go_path'             : subcall_inf['file_path']
                                                ,'go_pos'              : subcall_inf['submodule_name_match_pos']
                                                ,'go_word'             : subcall_inf['submodule_name'] 
                                                # for add_module_last_call_action
                                                ,'sub_module_name'     : subcall_inf['submodule_name']
                                                ,'upper_module_name'   : subcall_inf['cur_module_name']
                                                ,'upper_instance_name' : subcall_inf['instance_name']  }
                    c_file_link = gen_hyperlink(['go_file_action', 'add_module_last_call_action'], c_file_link_parm_dic, 'possible_upper')
                    c_print_str = '%d : %s -> %s (%s)'%(i, subcall_inf['cur_module_name'], subcall_inf['instance_name'], subcall_inf['submodule_name'])
                else:
                    c_file_link_parm_dic    = {  'type'                : 'possible_trace_upper'
                                                # for trace_io_signal_action
                                                ,'trace_type'          : trace_upper_inf['trace_type']
                                                ,'cursor_inf'          : trace_upper_inf['cursor_inf']
                                                ,'report_level'        : trace_upper_inf['report_level']
                                                # for add_module_last_call_action
                                                ,'sub_module_name'     : subcall_inf['submodule_name']
                                                ,'upper_module_name'   : subcall_inf['cur_module_name']
                                                ,'upper_instance_name' : subcall_inf['instance_name']  }
                    c_file_link_parm_dic['cursor_inf']['codes'] = None # fix bug for vim.buffer cannot pickle when <Space>+s
                    c_file_link = gen_hyperlink(['trace_io_signal_action', 'add_module_last_call_action'], c_file_link_parm_dic, 'possible_trace_upper')
                    c_print_str = '%d : %s -> %s (%s)'%(i, subcall_inf['cur_module_name'], subcall_inf['instance_name'], subcall_inf['submodule_name'])
                link_list.append( c_file_link )
                line_list.append( c_print_str )
            else:
                stale_call_me_subcall_inf_list.append( subcall_inf )
        if stale_call_me_subcall_inf_list:
            line_list.append( 'Stale:' )
            line_list.append( '( stale means upper module file has been modified )' )
            link_list.append( {} )
            link_list.append( {} )
            for subcall_inf in stale_call_me_subcall_inf_list:
                # current is for stale possible call
                c_file_link = None
                c_print_str = None
                if not trace_upper_inf: # must go upper
                    c_file_link_parm_dic    = {  'type'                : 'possible_upper'
                                                # for go_file_action
                                                ,'last_modify_time'    : os.path.getmtime( subcall_inf['file_path'] )
                                                ,'go_path'             : subcall_inf['file_path']
                                                ,'go_pos'              : subcall_inf['submodule_name_match_pos']
                                                ,'go_word'             : subcall_inf['submodule_name'] 
                                                # for add_module_last_call_action
                                                ,'sub_module_name'     : subcall_inf['submodule_name']
                                                ,'upper_module_name'   : subcall_inf['cur_module_name']
                                                ,'upper_instance_name' : subcall_inf['instance_name']  }
                    c_file_link = gen_hyperlink(['go_file_action', 'add_module_last_call_action'], c_file_link_parm_dic, 'possible_upper')
                    c_print_str = '%d : %s -> %s (%s)'%(i, subcall_inf['cur_module_name'], subcall_inf['instance_name'], subcall_inf['submodule_name'])
                else:
                    c_file_link_parm_dic    = {  'type'                : 'possible_trace_upper'
                                                # for trace_io_signal_action
                                                ,'trace_type'          : trace_upper_inf['trace_type']
                                                ,'cursor_inf'          : trace_upper_inf['cursor_inf']
                                                ,'report_level'        : trace_upper_inf['report_level']
                                                # for add_module_last_call_action
                                                ,'sub_module_name'     : subcall_inf['submodule_name']
                                                ,'upper_module_name'   : subcall_inf['cur_module_name']
                                                ,'upper_instance_name' : subcall_inf['instance_name']  }
                    c_file_link_parm_dic['cursor_inf']['codes'] = None # fix bug for vim.buffer cannot pickle when <Space>+s
                    c_file_link = gen_hyperlink(['trace_io_signal_action', 'add_module_last_call_action'], c_file_link_parm_dic, 'possible_trace_upper')
                    c_print_str = '%d : %s -> %s (%s)'%(i, subcall_inf['cur_module_name'], subcall_inf['instance_name'], subcall_inf['submodule_name'])
                link_list.append( c_file_link )
                line_list.append( c_print_str )
        return {"line_list":line_list, 'link_list':link_list}
    return {}

