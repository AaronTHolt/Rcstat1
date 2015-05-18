import re
import os
import subprocess
import rrdtool
import argparse
from Get_Data import get_data
from Utility import flat_list, get_colors

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

    graphs_himem = []

    graphs_janus = []

  # Other possible graphs:
  # 'rx_bytes_em1.rrd',
  # 'rx_bytes_em2.rrd', 'tx_bytes_em1.rrd', 'tx_bytes_em2.rrd',
  # 'rx_bytes_eth0.rrd', 
  # 'rx_bytes_eth1.rrd', 'tx_bytes_eth0.rrd', 'tx_bytes_eth1.rrd'


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


    for data in graph_list:
        single_node_graphs(data)
    # print graph_list

    all_node_graph(start, stop, jobid, node_names, cluster, graph_list)

def all_node_graph(start, stop, jobid, node_names, cluster, graph_list):
    num_colors = 0
    for data in graph_list:
        if data[6] == 'mem_free.rrd':
            num_colors += 1
    color_list = get_colors(num_colors)
    if num_colors<4:
        thickness = 'LINE2'
    else:
        thickness = 'LINE1'
    # print color_list

    mem_free_header = ['plots/{j}/{g}_Nodes.png'.format(g='mem_free.rrd', j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Amount Free',
              '--title', 'Free Memory in {c} Nodes'.format(c=cluster)]
    mem_free_sources = []
    mem_free_format = []

    cpu_used_header = ['plots/{j}/{g}_Nodes.png'.format(g='cpu_used.rrd', j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--lower-limit', '-1',
              '--title', 'CPU used in {c} Nodes'.format(c=cluster)]
    cpu_used_sources = []
    cpu_used_format = []

    bytes_out_header = ['plots/{j}/{g}_Nodes.png'.format(g='bytes_out.rrd', j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Network Out for {c} Nodes'.format(c=cluster)]
    bytes_out_sources = []
    bytes_out_format = []

    bytes_in_header = ['plots/{j}/{g}_Nodes.png'.format(g='bytes_in.rrd', j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Network In for {c} Nodes'.format(c=cluster)]
    bytes_in_sources = []
    bytes_in_format = []

    counter = 0
    for data in graph_list:
        # print data[6]
        if data[6] == 'mem_free.rrd':
            mem_free_sources.append('DEF:mem_free{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            mem_free_format.append('{L}:mem_free{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[3]))
        elif data[6] == 'cpu_user.rrd':
            cpu_used_sources.append('DEF:cpu_user{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            cpu_used_format.append('{L}:cpu_user{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[3]))
        elif data[6] == 'bytes_in.rrd':
            bytes_in_sources.append('DEF:bytes_in{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            bytes_in_format.append('{L}:bytes_in{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[3]))
        elif data[6] == 'bytes_out.rrd':
            bytes_out_sources.append('DEF:bytes_out{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            bytes_out_format.append('{L}:bytes_out{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[3]))
            counter += 1


    # mem free
    mem_free_graph = mem_free_header + mem_free_sources + mem_free_format
    cpu_used_graph = cpu_used_header + cpu_used_sources + cpu_used_format
    bytes_in_graph = bytes_in_header + bytes_in_sources + bytes_in_format
    bytes_out_graph = bytes_out_header + bytes_out_sources + bytes_out_format
    rrdtool.graph(mem_free_graph)
    rrdtool.graph(cpu_used_graph)
    rrdtool.graph(bytes_out_graph)
    rrdtool.graph(bytes_in_graph)

    # cpu used



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
              'LINE2:mem_free#0000FF')

    elif graph_type == 'cpu_user.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='cpu_used', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'CPU used in {c} - {n}'.format(c=cluster, n=nodename),
              '--lower-limit', '-1',
              'DEF:cpu_user={p}:sum:AVERAGE'.format(p=path),
              'LINE2:cpu_user#0000FF')
    
    ## GPU statistics
    elif graph_type == 'gpu0_mem_used.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='gpu0_mem_used', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'GPU memory used in {c} - {n}'.format(c=cluster, n=nodename),
              '--lower-limit', '-1',
              'DEF:gpu0_mem_used={p}:sum:AVERAGE'.format(p=path),
              'LINE2:gpu0_mem_used#0000FF')

    elif graph_type == 'gpu0_graphics_speed.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='gpu0_graphics_speed', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Graphics Speed in {c} - {n}'.format(c=cluster, n=nodename),
              '--lower-limit', '-1',
              'DEF:gpu0_graphics_speed={p}:sum:AVERAGE'.format(p=path),
              'LINE2:gpu0_graphics_speed#0000FF')

    ## Network statistics (not Blanca)
    elif graph_type == 'rx_bytes_eth0.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_eth0', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'rx bytes eth0 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_eth0={p}:sum:AVERAGE'.format(p=path),
              'LINE2:rx_bytes_eth0#0000FF')

    elif graph_type == 'rx_bytes_eth1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_eth1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'rx bytes eth1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_eth1={p}:sum:AVERAGE'.format(p=path),
              'LINE2:rx_bytes_eth1#0000FF')

    elif graph_type == 'tx_bytes_eth0.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_eth0', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'tx bytes eth0 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_eth0={p}:sum:AVERAGE'.format(p=path),
              'LINE2:tx_bytes_eth0#0000FF')

    elif graph_type == 'tx_bytes_eth1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_eth1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'tx bytes eth1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_eth1={p}:sum:AVERAGE'.format(p=path),
              'LINE2:tx_bytes_eth1#0000FF')

    ## Network statistics (Blanca)
    elif graph_type == 'rx_bytes_em1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_em1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'rx bytes em1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_em1={p}:sum:AVERAGE'.format(p=path),
              'LINE2:rx_bytes_em1#0000FF')

    elif graph_type == 'rx_bytes_em2.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_em2', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'rx bytes em2 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:rx_bytes_em2={p}:sum:AVERAGE'.format(p=path),
              'LINE2:rx_bytes_em2#0000FF')

    elif graph_type == 'tx_bytes_em1.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_em1', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'tx bytes em1 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_em1={p}:sum:AVERAGE'.format(p=path),
              'LINE2:tx_bytes_em1#0000FF')

    elif graph_type == 'tx_bytes_em2.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_em2', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'tx bytes em2 in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:tx_bytes_em2={p}:sum:AVERAGE'.format(p=path),
              'LINE2:tx_bytes_em2#0000FF')

    ## General network statistics
    elif graph_type == 'bytes_in.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='bytes_in', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Bytes In for {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:bytes_in={p}:sum:AVERAGE'.format(p=path),
              'LINE2:bytes_in#0000FF')

    elif graph_type == 'bytes_out.rrd':
        rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='bytes_out', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Bytes Out for {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:bytes_out={p}:sum:AVERAGE'.format(p=path),
              'LINE2:bytes_out#0000FF')

if __name__ == "__main__":
  # process(jobid)
  parser = argparse.ArgumentParser()
  parser.add_argument("jobid")
  args = parser.parse_args()
  # print int(float(args.jobid))
  # try:
  # if '.' in args.jobid:
  #     process(float(args.jobid))
  # else:
  process(int(float(args.jobid)))
  # except ValueError:
  #     print 'Error: Integer or float jobid only'





## Perhaps add graphs with 4ish plots per graph
## in addition to the all graph plots
#     num_graphs = 3 #max number of rrd's per graph
#     counter = 0
#     index = 0
#     multi_graph = []
#     for data in graph_list:
#         if counter == 0:
#             multi_graph.append([])
#         if counter < num_graphs:
#             multi_graph[index].append(data)
#         counter += 1

#     for data in multi_graph:
#         multi_node_graphs(data)

# def multi_node_graphs(data):