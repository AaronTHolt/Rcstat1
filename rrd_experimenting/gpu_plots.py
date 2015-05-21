import time
import re
import subprocess

now = time.time()
start = now-60000000

cmd3 = """rrdtool graph gpu0.png --start {s} --end {e} \
--vertical-label "Percent (%)" \
--title "GPU Testing" \
DEF:mytemp=../rrds/GPU/gpunode0101.rc.colorado.edu/gpu0_util.rrd:sum:AVERAGE \
LINE2:mytemp#0000FF
""".format(s=int(start), e=int(now))
# print cmd3
# subprocess.call(cmd3, shell=True)
p = subprocess.Popen(cmd3, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
out, err = p.communicate()

# /home/aaron/Documents/Ganglia

cmd3 = """rrdtool graph cpu.png --start {s} --end {e} \
--vertical-label "Percent (%)" \
--title "GPU Testing" \
DEF:mytemp=../rrds/GPU/gpunode0101.rc.colorado.edu/cpu_user.rrd:sum:AVERAGE \
LINE2:mytemp#0000FF
""".format(s=int(start), e=int(now))
# print cmd3
# subprocess.call(cmd3, shell=True)
p = subprocess.Popen(cmd3, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
out, err = p.communicate()

cmd3 = """rrdtool graph gpu_num.png --start {s} --end {e} \
--vertical-label "Percent (%)" \
--title "GPU Testing" \
DEF:mytemp=../rrds/GPU/gpunode0101.rc.colorado.edu/gpu_num.rrd:sum:AVERAGE \
LINE2:mytemp#0000FF
""".format(s=int(start), e=int(now))
# print cmd3
# subprocess.call(cmd3, shell=True)
p = subprocess.Popen(cmd3, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
out, err = p.communicate()


cmd3 = """rrdtool graph gpu0_mem_util.png --start {s} --end {e} \
--vertical-label "Percent (%)" \
--title "GPU Testing" \
DEF:mytemp=../rrds/GPU/gpunode0101.rc.colorado.edu/gpu0_mem_util.rrd:sum:AVERAGE \
LINE2:mytemp#0000FF
""".format(s=int(start), e=int(now))
# print cmd3
# subprocess.call(cmd3, shell=True)
p = subprocess.Popen(cmd3, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
out, err = p.communicate()