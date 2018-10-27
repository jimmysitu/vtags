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

# left sidebar window width
frame_window_width          = 20

# right bottom report window height
report_window_height        = 8

# max work window vtags auto opened, not include use self opened window and holded window
max_open_work_window_number = 1

# when use <Space><left>/<Space><right> the max number of history trace valid
max_roll_trace_depth        = 1000

# when <Space>c add check point, the max number of check point valid
max_his_check_point_num     = 10

# when gen the vtags database, in all verilog modules when some module called more then threshold times,
# set this module to be base module, then show topo will not list it's inst one by one  
base_module_threshold       = 200

# when module inst module_add_upper_threshold times, then not current module not note upper module
module_add_upper_threshold  = 10

# supported verilog postfix, we only add postfix in below to data base
support_verilog_postfix     = ['v']

# open debug module or not, open debug module will print a lot debug log at vtags.db
debug_mode                  = False

# when trace source, match bigger than TraceSourceOptimizingThreshold, open opt func, mainly for signal like clk,rst ...
trace_source_optimizing_threshold   = 20 

# frame fold level space, use to set pre space num, if current level is 3 ,
# and fold level space is ' ', then current line pre space is ' '*3 = '   ' 
frame_fold_level_space      = '    '

# weather show report or not
show_report                 = True

# will dynamic update vtags database
dynamic_update_vtags_db     = True

# max file name length in current os, used to deciside reduce pickle file name or not
max_file_name_length        = 100
