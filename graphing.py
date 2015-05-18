import re
import os
import subprocess
import rrdtool
import argparse
from Get_Data import get_data

# debug expands the plot time window to 4 months
# helps check if the graph was supposed to be blank 
global debug
debug = False
# debug = True

def process(jobid):
    global debug
    # JobID should be passed into process then using slurm:
    # Get job cluster and node names
    # Find job start/stop time
    # For now test assuming the above steps are done

    start, stop, cluster_names, node_names = get_data(jobid, debug)
    # print cluster_names, node_names

    #make directory for jobid
    try:
      os.mkdir('plots')
      os.chmod('plots',0o777)
    except OSError:
      pass
    try:
      os.mkdir('plots/{j}'.format(j=jobid))
      os.chmod('plots/{j}'.format(j=jobid),0o777)
    except OSError:
      pass

    graphs_gpu = ['mem_free.rrd', 'cpu_user.rrd', 'gpu0_mem_used.rrd', 
          'gpu0_graphics_speed.rrd', 'bytes_in.rrd', 'bytes_out.rrd']

    graphs_crestone = ['mem_free.rrd', 'cpu_user.rrd', 'bytes_in.rrd',
          'bytes_out.rrd']

    graphs_blanca = ['mem_free.rrd', 'cpu_user.rrd', 'bytes_in.rrd',
          'bytes_out.rrd']

    graphs_janus = []

  # Other possible graphs:
  # 'rx_bytes_em1.rrd',
  # 'rx_bytes_em2.rrd', 'tx_bytes_em1.rrd', 'tx_bytes_em2.rrd',
  # 'rx_bytes_eth0.rrd', 
  # 'rx_bytes_eth1.rrd', 'tx_bytes_eth0.rrd', 'tx_bytes_eth1.rrd'


    ## TODO add nodes like 10.16.8.20?
    # for cluster in cluster_names:
    #     for root, dirs, files in os.walk('rrds/{c}'.format(c=cluster)):
    #         # print root, dirs, files
    #         for file in files:
    #             if file.endswith(".rrd") and root.endswith("rc.colorado.edu"):
    #                 # print len(root.split('.')), root.split('.')
    #                 node = root.split('.')[0].split('/')[2]
    #                 # cluster = root.split('.')[0].split('/')[1]
    #                 # print node, cluster, node_names
    #                 if any(node in s for s in node_names):
    #                     # print node, cluster, node_names
    #                     # print(os.path.join(root, file))
    #                     # print file
    #                     if str(file) in desired_graphs:
    #                         ## root.split('.')[0] is cluster/nodename
    #                         # print cluster, node, file
    #                         graphs(file, start, stop, node, cluster, jobid) 

    graph_list = []
    for cluster in cluster_names:
        for node in node_names:
            if cluster == 'Blanca':
                for graph in graphs_blanca:
                    path = 'rrds/{c}/{n}.rc.colorado.edu/{g}'.format(c=cluster, n=node, g=graph)
                    graph_list.append([path, start, stop, node, cluster, jobid, graph])
            elif cluster == 'GPU':
                for graph in graphs_gpu:
                    path = 'rrds/{c}/{n}.rc.colorado.edu/{g}'.format(c=cluster, n=node, g=graph)
                    graph_list.append([path, start, stop, node, cluster, jobid, graph])
            elif cluster == 'Crestone':
                for graph in graphs_crestone:
                    path = 'rrds/{c}/{n}.rc.colorado.edu/{g}'.format(c=cluster, n=node, g=graph)
                    graph_list.append([path, start, stop, node, cluster, jobid, graph])

    ## TODO: combine netork data into two graphs per node (tx and rx)
    ## The single graph per tx/rx thing creates too many graphs
    ## Maybe do this in previous loop?
    # for data in graph_list:
    #     a = data[6].split('.')[0]
    #     if a.startswith('tx'):

    #     elif a.startswith('rx'):


    for data in graph_list:
        single_node_graphs(data)
    # print graph_list


def single_node_graphs(data):
    path, start, stop, nodename, cluster, jobid, graph_type = data
    # print data, filename
    if graph_type == 'mem_free.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='mem_free.rrd', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Amount Free',
              '--title', 'Free Memory in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:mem_free={p}:sum:AVERAGE'.format(p=path),
              'LINE1:mem_free#0000FF')

    elif graph_type == 'cpu_user.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='cpu_used', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'CPU used in {c} - {n}'.format(c=cluster, n=nodename),
              '--lower-limit', '-1',
              'DEF:cpu_user={p}:sum:AVERAGE'.format(p=path),
              'LINE1:cpu_user#0000FF')
    
    ## GPU statistics
    elif graph_type == 'gpu0_mem_used.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='gpu0_mem_used', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'GPU memory used in {c} - {n}'.format(c=cluster, n=nodename),
              '--lower-limit', '-1',
              'DEF:gpu0_mem_used={p}:sum:AVERAGE'.format(p=path),
              'LINE1:gpu0_mem_used#0000FF')

    elif graph_type == 'gpu0_graphics_speed.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='gpu0_graphics_speed', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Graphics Speed in {c} - {n}'.format(c=cluster, n=nodename),
              '--lower-limit', '-1',
              'DEF:gpu0_graphics_speed={p}:sum:AVERAGE'.format(p=path),
              'LINE1:gpu0_graphics_speed#0000FF')

    ## Network statistics (not Blanca)
    elif graph_type == 'rx_bytes_eth0.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_eth0', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'rx bytes eth0 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_eth0={p}:sum:AVERAGE'.format(p=path),
              'LINE1:rx_bytes_eth0#0000FF')

    elif graph_type == 'rx_bytes_eth1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_eth1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'rx bytes eth1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_eth1={p}:sum:AVERAGE'.format(p=path),
              'LINE1:rx_bytes_eth1#0000FF')

    elif graph_type == 'tx_bytes_eth0.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_eth0', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'tx bytes eth0 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_eth0={p}:sum:AVERAGE'.format(p=path),
              'LINE1:tx_bytes_eth0#0000FF')

    elif graph_type == 'tx_bytes_eth1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_eth1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'tx bytes eth1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_eth1={p}:sum:AVERAGE'.format(p=path),
              'LINE1:tx_bytes_eth1#0000FF')

    ## Network statistics (Blanca)
    elif graph_type == 'rx_bytes_em1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_em1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'rx bytes em1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_em1={p}:sum:AVERAGE'.format(p=path),
              'LINE1:rx_bytes_em1#0000FF')

    elif graph_type == 'rx_bytes_em2.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_em2', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'rx bytes em2 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_em2={p}:sum:AVERAGE'.format(p=path),
              'LINE1:rx_bytes_em2#0000FF')

    elif graph_type == 'tx_bytes_em1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_em1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'tx bytes em1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_em1={p}:sum:AVERAGE'.format(p=path),
              'LINE1:tx_bytes_em1#0000FF')

    elif graph_type == 'tx_bytes_em2.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_em2', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'tx bytes em2 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_em2={p}:sum:AVERAGE'.format(p=path),
              'LINE1:tx_bytes_em2#0000FF')

    ## General network statistics
    elif graph_type == 'bytes_in.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='bytes_in', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Bytes In for {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:bytes_in={p}:sum:AVERAGE'.format(p=path),
              'LINE1:bytes_in#0000FF')

    elif graph_type == 'bytes_out.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='bytes_out', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Bytes Out for {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:bytes_out={p}:sum:AVERAGE'.format(p=path),
              'LINE1:bytes_out#0000FF')

if __name__ == "__main__":
  # process(jobid)
  parser = argparse.ArgumentParser()
  parser.add_argument("jobid")
  args = parser.parse_args()
  # print int(float(args.jobid))
  try:
      if '.' in args.jobid:
          process(float(args.jobid))
      else:
          process(int(float(args.jobid)))
  except ValueError:
      print 'Error: Integer or float jobid only'
