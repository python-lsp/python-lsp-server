# Autoimport for pylsp
Requirements:
1. rope
2. ``pylsp.plugins.rope_autoimport.enabled`` is enabled
## Startup
Autoimport will generate an autoimport sqllite3 database in .ropefolder/autoimport.db on startup.  
This will take a few seconds but should be much quicker on future runs.
## Usage 
Autoimport will provide suggestions to import names from everything in ``sys.path``. It will suggest modules, submodules, keywords, functions, and classes.  

Since autoimport inserts everything towards the end of the import group, its recommended you use the isort [plugin](https://github.com/paradoxxxzero/pyls-isort).

## Credits
 - Most of the code was written by me, @bageljrkhanofemus
 - [lyz-code](https://github.com/lyz-code/autoimport) for inspiration and some ideas
 - [rope](https://github.com/python-rope/rope)
 - [pyright](https://github.com/Microsoft/pyright) for details on language server implementation
