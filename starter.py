#application start

from web import flask_main
from web.flask_main import *
# import subprocess
# import os

##enable slurm sacct command
# subprocess.call("./enable_sacct.sh", shell=True)

#run web app
flask_main.app.run(host='0.0.0.0')
# flask_main.app.run(debug=True)

