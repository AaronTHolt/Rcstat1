import re
import os
import subprocess
import rrdtool
import argparse
from collections import defaultdict
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

    desired_graphs = ['mem_free.rrd', 'cpu_user.rrd', 'bytes_in.rrd',
          'bytes_out.rrd']

    # graphs_gpu = ['mem_free.rrd', 'cpu_user.rrd', 'gpu0_mem_used.rrd', 
    #       'gpu0_graphics_speed.rrd', 'bytes_in.rrd', 'bytes_out.rrd']
    # graphs_crestone = ['mem_free.rrd', 'cpu_user.rrd', 'bytes_in.rrd',
    #       'bytes_out.rrd']
    # graphs_blanca = ['mem_free.rrd', 'cpu_user.rrd', 'bytes_in.rrd',
    #       'bytes_out.rrd']
    # graphs_himem = []
    # graphs_janus = []

    graph_list = []
    for cluster in cluster_names:
        for node in node_names:
            for graph in desired_graphs:
                path = 'rrds/{c}/{n}.rc.colorado.edu/{g}'.format(c=cluster, n=node, g=graph)
                graph_list.append([path, node, cluster, jobid, graph])

            # if cluster == 'Blanca':
            #     for graph in graphs_blanca:
            #         path = 'rrds/{c}/{n}.rc.colorado.edu/{g}'.format(c=cluster, n=node, g=graph)
            #         graph_list.append([path, node, cluster, jobid, graph])
            # elif cluster == 'GPU':
            #     for graph in graphs_gpu:
            #         path = 'rrds/{c}/{n}.rc.colorado.edu/{g}'.format(c=cluster, n=node, g=graph)
            #         graph_list.append([path, node, cluster, jobid, graph])
            # elif cluster == 'Crestone':
            #     for graph in graphs_crestone:
            #         path = 'rrds/{c}/{n}.rc.colorado.edu/{g}'.format(c=cluster, n=node, g=graph)
            #         graph_list.append([path, node, cluster, jobid, graph])


    for data in graph_list:
        single_node_graphs(start, stop, data)
    # print graph_list

    all_node_graph(start, stop, jobid, node_names, cluster, graph_list)

def graph_header(start,stop,jobid,cluster,graph_type,rrd_type,index):
    # graph types are currently: average, all
    # average is all lines but only averages plotted
    # all is all lines on one plot

    header = ['plots/{j}/{r}_{g}_{i}.png'.format(j=jobid, 
                  r=rrd_type, g=graph_type, i=index),
                  '--start', "{begin}".format(begin=start),
                  '--end', "{end}".format(end=stop),
                  '--color', "CANVAS#000000[00]",
                  '--color', "MGRID#FFFFFF[00]",
                  '--color', "GRID#FF0000[00]",]
    title_modifier = ''
    if rrd_type == 'mem_free.rrd':
        header += ['--vertical-label', 'Amount Free']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}Free Memory in {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
    elif rrd_type == 'cpu_used.rrd':
        header += ['--vertical-label', 'Percent (%)']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}CPU used in {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
    elif rrd_type == 'bytes_out.rrd':
        header += ['--vertical-label', 'Bytes']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}Network Out for {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
    elif rrd_type == 'bytes_in.rrd':
        header += ['--vertical-label', 'Bytes']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}Network In for {c} Nodes'.format(
                  m=title_modifier, c=cluster)]

    # print header
    return header


def all_node_graph(start, stop, jobid, node_names, cluster, graph_list):

    # Count how many lines are on a graph
    # Split list into lists of Max_Lines
    Max_Lines = 10 # Maximum number of lines on a graph
    index = 0
    graph_dict = defaultdict(list)
    num_colors = 0
    for data in graph_list:
        graph_dict[index].append(data)
        if num_colors > Max_Lines:
            index += 1
        if data[4] == 'bytes_out.rrd':
            num_colors += 1

    # if more than 10 nodes used, generate average plot
    # and keep max 10 plots on a graph
    if num_colors > Max_Lines:
        all_average_graph(start, stop, jobid, node_names, cluster, 
                graph_list, num_colors)
        for index in graph_dict:
            graphit(start, stop, jobid, node_names, cluster,
                    graph_dict[index], index, num_colors, Max_Lines)
    else:
        ## REMOVE THIS WHEN YOU FIND JOBS>10 NODES TO TEST ON
        ##
        all_average_graph(start, stop, jobid, node_names, cluster, 
                graph_list, num_colors)
        ##
        graphit(start, stop, jobid, node_names, cluster,
                graph_dict[index], index, num_colors, Max_Lines)



def graphit(start, stop, jobid, node_names, cluster, 
              graph_list, index, num_colors, Max_Lines):
    color_list = get_colors(num_colors)
    # print color_list
    num_colors = num_colors - index*Max_Lines
    if num_colors<4:
        thickness = 'LINE2'
    else:
        thickness = 'LINE1'

    mem_free_sources = []
    mem_free_format = []
    cpu_used_sources = []
    cpu_used_format = []
    bytes_out_sources = []
    bytes_out_format = []
    bytes_in_sources = []
    bytes_in_format = []

    counter = index
    for data in graph_list:
        # print data[6]
        if data[4] == 'mem_free.rrd':
            mem_free_sources.append('DEF:mem_free{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            mem_free_format.append('{L}:mem_free{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[1]))
        elif data[4] == 'cpu_user.rrd':
            cpu_used_sources.append('DEF:cpu_user{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            cpu_used_format.append('{L}:cpu_user{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[1]))
        elif data[4] == 'bytes_in.rrd':
            bytes_in_sources.append('DEF:bytes_in{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            bytes_in_format.append('{L}:bytes_in{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[1]))
        elif data[4] == 'bytes_out.rrd':
            bytes_out_sources.append('DEF:bytes_out{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            bytes_out_format.append('{L}:bytes_out{i}{color}:{n}'.format(
                  L=thickness, i=counter, color=color_list[counter], n=data[1]))
            counter += 1

                            # [start,stop,jobid,cluster,graph_type,rrd_type]
    mem_free_header = graph_header(start,stop,jobid,cluster,'all','mem_free',index)
    mem_free_graph = mem_free_header + mem_free_sources + mem_free_format
    cpu_used_header = graph_header(start,stop,jobid,cluster,'all','cpu_used',index)
    cpu_used_graph = cpu_used_header + cpu_used_sources + cpu_used_format
    bytes_in_header = graph_header(start,stop,jobid,cluster,'all','bytes_in',index)
    bytes_in_graph = bytes_in_header + bytes_in_sources + bytes_in_format
    bytes_out_header = graph_header(start,stop,jobid,cluster,'all','bytes_out',index)
    bytes_out_graph = bytes_out_header + bytes_out_sources + bytes_out_format
    rrdtool.graph(mem_free_graph)
    rrdtool.graph(cpu_used_graph)
    rrdtool.graph(bytes_out_graph)
    rrdtool.graph(bytes_in_graph)

def all_average_graph(start, stop, jobid, node_names, cluster, 
                graph_list, num_colors):
    color_list = get_colors(num_colors*2)
    thickness = 'LINE1'

    mem_free_sources = []
    mem_free_format = []
    cpu_used_sources = []
    cpu_used_format = []
    bytes_out_sources = []
    bytes_out_format = []
    bytes_in_sources = []
    bytes_in_format = []

      # DEF:ping_host=ping.rrd:ping_ms:AVERAGE 
      # VDEF:ping_average=ping_host,AVERAGE 

    counter = 0
    for data in graph_list:
        # print data[6]
        if data[4] == 'mem_free.rrd':
            mem_free_sources.append('DEF:mem_free{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            mem_free_sources.append('VDEF:mem_free_avg{i}=mem_free{i},AVERAGE'.format(i=counter))
            # mem_free_format.append('{L}:mem_free{i}{color}:{n}'.format(
            #       L=thickness, i=counter, color=color_list[counter], n=data[1]))
            mem_free_format.append('{L}:mem_free_avg{i}{color}:{n}AVG'.format(
                  L=thickness, i=counter, color=color_list[counter+1], n=data[1]))
        elif data[4] == 'cpu_user.rrd':
            cpu_used_sources.append('DEF:cpu_user{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            cpu_used_sources.append('VDEF:cpu_user_avg{i}=cpu_user{i},AVERAGE'.format(i=counter))
            # cpu_used_format.append('{L}:cpu_user{i}{color}:{n}'.format(
            #       L=thickness, i=counter, color=color_list[counter], n=data[1]))
            cpu_used_format.append('{L}:cpu_user_avg{i}{color}:{n}AVG'.format(
                  L=thickness, i=counter, color=color_list[counter+1], n=data[1]))
        elif data[4] == 'bytes_in.rrd':
            bytes_in_sources.append('DEF:bytes_in{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            bytes_in_sources.append('VDEF:bytes_in_avg{i}=bytes_in{i},AVERAGE'.format(i=counter))
            # bytes_in_format.append('{L}:bytes_in{i}{color}:{n}'.format(
            #       L=thickness, i=counter, color=color_list[counter], n=data[1]))
            bytes_in_format.append('{L}:bytes_in_avg{i}{color}:{n}AVG'.format(
                  L=thickness, i=counter, color=color_list[counter+1], n=data[1]))
        elif data[4] == 'bytes_out.rrd':
            bytes_out_sources.append('DEF:bytes_out{i}={p}:sum:AVERAGE'.format(
                  i=counter, p=data[0]))
            bytes_out_sources.append('VDEF:bytes_out_avg{i}=bytes_out{i},AVERAGE'.format(i=counter))
            # bytes_out_format.append('{L}:bytes_out{i}{color}:{n}'.format(
            #       L=thickness, i=counter, color=color_list[counter], n=data[1]))
            bytes_out_format.append('{L}:bytes_out_avg{i}{color}:{n}AVG'.format(
                  L=thickness, i=counter, color=color_list[counter+1], n=data[1]))
            counter += 2

                            # [start,stop,jobid,cluster,graph_type,rrd_type]
    mem_free_header = graph_header(start,stop,jobid,cluster,'avg','mem_free',0)
    mem_free_graph = mem_free_header + mem_free_sources + mem_free_format
    cpu_used_header = graph_header(start,stop,jobid,cluster,'avg','cpu_used',0)
    cpu_used_graph = cpu_used_header + cpu_used_sources + cpu_used_format
    bytes_in_header = graph_header(start,stop,jobid,cluster,'avg','bytes_in',0)
    bytes_in_graph = bytes_in_header + bytes_in_sources + bytes_in_format
    bytes_out_header = graph_header(start,stop,jobid,cluster,'avg','bytes_out',0)
    bytes_out_graph = bytes_out_header + bytes_out_sources + bytes_out_format
    # print mem_free_graph
    rrdtool.graph(mem_free_graph)
    rrdtool.graph(cpu_used_graph)
    rrdtool.graph(bytes_out_graph)
    rrdtool.graph(bytes_in_graph)


def single_node_graphs(start, stop, data):
    path, nodename, cluster, jobid, graph_type = data
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
  process(int(float(args.jobid)))



    # ## GPU statistics
    # elif graph_type == 'gpu0_mem_used.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='gpu0_mem_used', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Bytes',
    #           '--title', 'GPU memory used in {c} - {n}'.format(c=cluster, n=nodename),
    #           '--lower-limit', '-1',
    #           'DEF:gpu0_mem_used={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:gpu0_mem_used#0000FF')

    # elif graph_type == 'gpu0_graphics_speed.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='gpu0_graphics_speed', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Bytes',
    #           '--title', 'Graphics Speed in {c} - {n}'.format(c=cluster, n=nodename),
    #           '--lower-limit', '-1',
    #           'DEF:gpu0_graphics_speed={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:gpu0_graphics_speed#0000FF')

    # ## Network statistics (not Blanca)
    # elif graph_type == 'rx_bytes_eth0.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_eth0', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Percent (%)',
    #           '--title', 'rx bytes eth0 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:rx_bytes_eth0={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:rx_bytes_eth0#0000FF')

    # elif graph_type == 'rx_bytes_eth1.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_eth1', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Percent (%)',
    #           '--title', 'rx bytes eth1 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:rx_bytes_eth1={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:rx_bytes_eth1#0000FF')

    # elif graph_type == 'tx_bytes_eth0.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_eth0', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Percent (%)',
    #           '--title', 'tx bytes eth0 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:tx_bytes_eth0={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:tx_bytes_eth0#0000FF')

    # elif graph_type == 'tx_bytes_eth1.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_eth1', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Percent (%)',
    #           '--title', 'tx bytes eth1 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:tx_bytes_eth1={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:tx_bytes_eth1#0000FF')

    # ## Network statistics (Blanca)
    # elif graph_type == 'rx_bytes_em1.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_em1', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Bytes',
    #           '--title', 'rx bytes em1 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:rx_bytes_em1={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:rx_bytes_em1#0000FF')

    # elif graph_type == 'rx_bytes_em2.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='rx_bytes_em2', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Bytes',
    #           '--title', 'rx bytes em2 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:rx_bytes_em2={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:rx_bytes_em2#0000FF')

    # elif graph_type == 'tx_bytes_em1.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_em1', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Bytes',
    #           '--title', 'tx bytes em1 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:tx_bytes_em1={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:tx_bytes_em1#0000FF')

    # elif graph_type == 'tx_bytes_em2.rrd':
    #     rrdtool.graph('plots/{j}/{g}_{n}.png'.format(g='tx_bytes_em2', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Bytes',
    #           '--title', 'tx bytes em2 in {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:tx_bytes_em2={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:tx_bytes_em2#0000FF')