import time
import re
import os
import subprocess
import rrdtool
import hostlist

 # 666100     janus Y_svBi_d sami1065  R   15:10:47      2 node[1645,1658]


# for file in os.listdir("Crestone/cnode0101.rc.colorado.edu"):
#     if file.endswith(".rrd"):
#         print(file)



def driver(jobid):
    #Still need find job start/stop time
    ################################
    # 2015-05-13T10:21:00|2015-05-14T09:44:02
    stop = int(time.time())
    start = int(stop-9000000)  #4ish months
    # print start, stop

    #Still nees to get job cluster and node names
    cluster_names = []
    node_names = []
    ##############################

    cluster_names.append('Crestone')
    node_names.append('cnode0101')
    node_names.append('cnode0102')
    
    #Currently just plotting cpu usage and free memory
    desired_graphs = ['mem_free.rrd', 'cpu_user.rrd']

    for cluster in cluster_names:
        for root, dirs, files in os.walk(cluster):
            # print root, dirs, files
            for file in files:
                if file.endswith(".rrd"):
                    node = root.split('.')[0].split('/')[1]
                    cluster = root.split('.')[0].split('/')[0]
                    # print node, cluster, node_names
                    if any(node in s for s in node_names):
                        # print node, cluster, node_names
                        # print(os.path.join(root, file))
                        # print file
                        if str(file) in desired_graphs:
                            ## root.split('.')[0] is cluster/nodename
                            # print cluster, node, file
                            graphs(file, start, stop, node, cluster) 

def graphs(filename, start, stop, nodename, cluster):
    if filename == 'mem_free.rrd':
        rrdtool.graph('{g}_{n}.png'.format(g=filename.split('.')[0], n=nodename),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Amount Free',
              '--title', 'Free Memory in {n}'.format(n=nodename),
              'DEF:mem_free={c}/{n}.rc.colorado.edu/mem_free.rrd:sum:AVERAGE'.format(c=cluster, n=nodename),
              'LINE1:mem_free#0000FF')

    elif filename == 'cpu_user.rrd':
        rrdtool.graph('{g}_{n}.png'.format(g=filename.split('.')[0], n=nodename),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'CPU used in {n}'.format(n=nodename),
              '--lower-limit', '-1',
              'DEF:cpu_user={c}/{n}.rc.colorado.edu/cpu_user.rrd:sum:AVERAGE'.format(c=cluster, n=nodename),
              'LINE1:cpu_user#0000FF')


driver(42)





# rrdtool.graph('mem_free.png',
#               '--start', "%i" % start,
#               '--end', "%i" % now,
#               '--vertical-label', 'Amount Free',
#               '--title', 'Free Memory',
#               'DEF:mem_free=cnode0102.rc.colorado.edu/mem_free.rrd:sum:AVERAGE',
#               'LINE1:mem_free#0000FF')

# rrdtool.graph('mem_dirty.png',
#               '--start', "%i" % start,
#               '--end', "%i" % now,
#               '--vertical-label', 'Amount Dirty',
#               '--title', 'Dirty Memory',
#               '--lower-limit', '-3000',
#               'DEF:mem_dirty=cnode0102.rc.colorado.edu/mem_dirty.rrd:sum:AVERAGE',
#               'LINE1:mem_dirty#0000FF')

# rrdtool.graph('cpu_user.png',
#               '--start', "%i" % start,
#               '--end', "%i" % now,
#               '--vertical-label', 'Percent (%)',
#               '--title', 'CPU Used',
#               '--lower-limit', '-1',
#               'DEF:cpu_user=cnode0102.rc.colorado.edu/cpu_user.rrd:sum:AVERAGE',
#               'LINE1:cpu_user#0000FF')

# rrdtool.graph('cpu_idle.png',
#               '--start', "%i" % start,
#               '--end', "%i" % now,
#               '--vertical-label', 'Percent (%)',
#               '--title', 'CPU Idle',
#               '--lower-limit', '-1',
#               'DEF:cpu_idle=cnode0102.rc.colorado.edu/cpu_idle.rrd:sum:AVERAGE',
#               'LINE1:cpu_idle#0000FF')