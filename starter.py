#application start

from web import flask_main
from web.flask_main import *
import os
import shutil

##change working dir to work with systemd startup
os.chdir('/root/rcstat/rcstat1')

##remove old files
directory1 = 'web/static/job/'
directory2 = 'sacct_output/'
try:
    os.chdir(directory1)
    for somefile in os.listdir('.'):
        shutil.rmtree(somefile) 

    os.chdir('../../../')
    os.chdir(directory2)
    for somefile in os.listdir('.'):
        os.unlink(somefile) 
    os.chdir('../')
except OSError:
    pass

##enable slurm sacct command
os.environ['PATH'] = '/curc/slurm/slurm/current/bin:${PATH}'
os.environ['LD_LIBRARY_PATH'] = '/curc/slurm/slurm/current/lib:${LD_LIBRARY_PATH}'
os.environ['MANPATH'] = 'curc/slurm/slurm/current/share/man${MANPATH}' 
os.environ['SLURM_ROOT'] = '/curc/slurm/slurm/current'
os.environ['I_MPI_PMI_LIBRARY'] = '/curc/slurm/slurm/current/lib/libmpi.so'

##run web app
flask_main.app.run(host='0.0.0.0')
# flask_main.app.run(debug=True)

