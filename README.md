# Installation
## Install from Vundle
Place this in your .vimrc:
```vim
Plugin 'universal-ctags/ctags'
```
then run the following in Vim:
```bash
:source %
:PluginInstall
```

# Usage
|shortcut key|function|
|------------|--------|
|mt|print module trace from top to current cursor module.
|gi|go into submodule 
|gu|go upper module
|gs|trace source
|gd|trace destination
|gf|go forward
|gb|jjjroll back
|\<Space>\<Left> |trace source 
|\<Space>\<Right>|trace destination 
|\<Space>\<Down> |roll back 
|\<Space>\<Up>   |go forward 
|\<Space> + v   |view sidebar 
|\<Space> + c   |add checkpoint 
|\<Space> + b   |add basemodule 
|\<Space> + d   |delete 
|\<Space> + h   |hold cur window 
|\<Space>       |quick access 
|\<Space> + s   |save snapshort 
|gvim/vim       |reload snapshort 
