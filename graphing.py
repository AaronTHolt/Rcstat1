import re
import os
import string
from sets import Set
import subprocess
import rrdtool
import argparse
from collections import defaultdict
from Get_Data import get_data
from Utility import flat_list, get_colors, get_rackname

# debug expands the plot time window to 4 months
# helps check if the graph was supposed to be blank 
global debug
debug = False
# debug = True

def process(jobid, tab):
    ## tab is which tab to be loaded
    ## ex: aggregate, stats, cpu, etc.
    global debug

    # Get job information from slurm
    start, stop, cluster_names, node_names = get_data(jobid, debug)
    # print "Cluster Names = ", cluster_names
    # print "Node names = ", node_names

    #For jobs with no start time
    if start=='Unknown':
        return 'Unknown', 'Unknown', 'Unknown', 'Unknown'

    #For job numbers that are too large
    if start==False or stop==False:
        return False, False, False, False

    #make directory for jobid
    try:
        os.mkdir('web/static/job')
        os.chmod('web/static/job',0o777)
    except OSError:
        pass
    try:
        os.mkdir('web/static/job/{j}'.format(j=jobid))
        os.chmod('web/static/job/{j}'.format(j=jobid),0o777)
    except OSError:
        pass
    
    #Make directory for each graph type per jobid
    types = ['agg', 'avg', 'cpu', 'mem_free', 'bytes_in', 'bytes_out']
            # 'gpu0_util', 'gpu0_mem_util']
    for graph_type in types:
        try:
            # print 'web/static/job/{j}/{g}'.format(
            #             j=jobid, g=graph_type)
            os.mkdir('web/static/job/{j}/{g}'.format(
                        j=jobid, g=graph_type))
            os.chmod('web/static/job/{j}/{g}'.format(
                        j=jobid, g=graph_type),0o777)
        except OSError:
            # print "Fail Sauce"
            pass


    desired_graphs = []
    if tab == 'agg' or tab == 'avg':
        desired_graphs = ['mem_free.rrd', 'cpu_user.rrd', 'bytes_in.rrd',
                            'bytes_out.rrd']
    elif tab == 'cpu':
        desired_graphs = ['cpu_user.rrd']
    elif tab == 'mem_free':
        desired_graphs = ['mem_free.rrd']
    elif tab == 'bytes_in':
        desired_graphs = ['bytes_in.rrd']
    elif tab == 'bytes_out':
        desired_graphs = ['bytes_out.rrd']
    # elif tab == 'gpu':
    #     desired_graphs = ['gpu0_util.rrd']
    # elif tab == 'gpumem':
    #     desired_graphs = ['gpu0_mem_util.rrd']

    # #If this is a GPU job, add gpu graphs
    gpu_param = False
    # for node in node_names:
    #     if 'gpu' in node:
    #         gpu_param = True
    #         desired_graphs = ['gpu0_mem_util.rrd', 'gpu0_util.rrd'] + desired_graphs
    #         break

    graph_list = []
    for cluster in cluster_names:
        #account for jobs on multiple racks of Janus Compute
        if cluster == 'Janus':
            for node in node_names:
                rackname = get_rackname(node)
                for graph in desired_graphs:
                    path = r'/var/lib/ganglia/rrds/{c}/{n}-general.rc.colorado.edu/{g}'.format(
                                          c=rackname, n=node, g=graph)
                    graph_list.append([path, node, rackname, jobid, graph])
        else:
            for node in node_names:
                for graph in desired_graphs:
                    path = r'/var/lib/ganglia/rrds/{c}/{n}.rc.colorado.edu/{g}'.format(
                                          c=cluster, n=node, g=graph)
                    graph_list.append([path, node, cluster, jobid, graph])

    available_set = Set()
    missing_set = Set()
    for data in graph_list:
        try:    
            single_node_graphs(start, stop, data, gpu_param)
            available_set.add(data[1])
            # print "AVAIL", data[1], data[4]
        except rrdtool.error:
            # print data
            missing_set.add(data[1])
            # print "BAD", data[1], data[4]
    # print "Available =", len(available_set), available_set
    # print "Missing =", len(missing_set), missing_set
    # print "Nodes Used =", len(Set(node_names)-missing_set), Set(node_names)-missing_set    

    ## Move this after all the nodes start reporting
    ## and there are no more 'Missing'
    if tab != 'agg' and tab != 'avg':
        return gpu_param, missing_set, start, stop

    Max_Lines = 10 # Maximum number of lines on a graph
    index = 0
    graph_dict = defaultdict(list)
    num_colors = 0
    for data in graph_list:
        if data[1] in missing_set:
            pass
        else:
            graph_dict[index].append(data)
            if data[4] == 'bytes_out.rrd':
                num_colors += 1
            if num_colors >= Max_Lines + Max_Lines * index:
                index += 1

    # if more than Max_Lines nodes used, generate average plot
    # and keep Max_Lines plots per graph
    if num_colors == 0:
        pass
    else:
        if num_colors >= Max_Lines:
            if tab == 'avg':
                all_average_graph(start, stop, jobid, node_names, cluster, 
                        graph_list, num_colors, gpu_param, missing_set)
            elif tab == 'agg':
                for index in graph_dict:
                    graphit(start, stop, jobid, node_names, cluster,
                            graph_dict[index], index, num_colors, 
                            Max_Lines, gpu_param, missing_set)
        else:
            if tab == 'avg':
                all_average_graph(start, stop, jobid, node_names, cluster, 
                        graph_list, num_colors, gpu_param, missing_set)
            elif tab == 'agg':
                graphit(start, stop, jobid, node_names, cluster,
                        graph_dict[index], index, num_colors, 
                        Max_Lines, gpu_param, missing_set)

    return gpu_param, missing_set, start, stop

def graph_header(start,stop,jobid,cluster,graph_type,rrd_type,
                  index, gpu_param):
    # graph types are currently: avg, agg
    # avg is averages plotted with stats below
    # agg is all lines on one plot

    ## Add the following to flush rrdcached before graphing
    # --daemon unix:/var/run/rrdcached.sock [...]

    # header = ['web/static/plots/{j}/{r}_{g}_{i}.png'.format(j=jobid,
    header = ['web/static/job/{j}/{g}/{r}_{g}_{i}.png'.format(j=jobid, 
                  r=rrd_type, g=graph_type, i=index),
                  '--start', "{begin}".format(begin=start),
                  '--end', "{end}".format(end=stop),
                  '--slope-mode']
                  ## 'Black background'
                  # '--color', "CANVAS#000000[00]",
                  # '--color', "MGRID#FFFFB0[80]",
                  # '--color', "GRID#FFFFB0[A0]",
                  # '--color', "FONT#FFFFFF[00]",
                  # '--color', "SHADEA#000000[00]",
                  # '--color', "SHADEB#000000[00]",
                  # '--color', "BACK#000000[00]"


    title_modifier = ''
    if rrd_type == 'mem_free':
        header += ['--vertical-label', 'Amount Free']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}Free Memory in {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
    elif rrd_type == 'cpu_used':
        header += ['--vertical-label', 'Percent (%)']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}CPU used in {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
        header += ['-X', '0']
        header += ['--upper-limit', '10']
        header += ['--lower-limit', '0']

    elif rrd_type == 'gpu0_util':
        header += ['--vertical-label', 'Percent (%)']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}GPU used in {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
    elif rrd_type == 'gpu0_mem_util':
        header += ['--vertical-label', 'Percent (%)']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}GPU Memory used in {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
    elif rrd_type == 'bytes_out':
        header += ['--vertical-label', 'Bytes']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}Network Out for {c} Nodes'.format(
                  m=title_modifier, c=cluster)]
    elif rrd_type == 'bytes_in':
        header += ['--vertical-label', 'Bytes']
        if graph_type == 'avg':
            title_modifier = 'Average '
        header += ['--title', '{m}Network In for {c} Nodes'.format(
                  m=title_modifier, c=cluster)]

    # print "HEADER = ", header
    return header

def graphit(start, stop, jobid, node_names, cluster, graph_list, 
              index, num_colors, Max_Lines, gpu_param, missing_set):

    if num_colors == Max_Lines:
        pass
    elif num_colors - index*Max_Lines >= Max_Lines:
        num_colors = Max_Lines
    else:
        num_colors = num_colors - index*Max_Lines
    color_list = get_colors(num_colors)

    thickness = 'LINE1'

    mem_free_sources = []
    mem_free_format = []
    cpu_used_sources = []
    cpu_used_format = []
    gpu_used_sources = []
    gpu_used_format = []
    gpu_mem_used_sources = []
    gpu_mem_used_format = []
    bytes_out_sources = []
    bytes_out_format = []
    bytes_in_sources = []
    bytes_in_format = []

    # counter = index
    counter = 0
    for data in graph_list:
        
        if data[1] in missing_set:
            pass
        else:
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
            elif data[4] == 'gpu0_util.rrd':
                gpu_used_sources.append('DEF:gpu0_util{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                gpu_used_format.append('{L}:gpu0_util{i}{color}:{n}'.format(
                      L=thickness, i=counter, color=color_list[counter], n=data[1]))
            elif data[4] == 'gpu0_mem_util.rrd':
                gpu_mem_used_sources.append('DEF:gpu0_mem_util{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                gpu_mem_used_format.append('{L}:gpu0_mem_util{i}{color}:{n}'.format(
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
    mem_free_header = graph_header(start,stop,jobid,cluster,'agg',
                                  'mem_free',index,gpu_param)
    mem_free_graph = mem_free_header + mem_free_sources + mem_free_format
    cpu_used_header = graph_header(start,stop,jobid,cluster,'agg',
                                  'cpu_used',index,gpu_param)
    cpu_used_graph = cpu_used_header + cpu_used_sources + cpu_used_format
    gpu_used_header = graph_header(start,stop,jobid,cluster,'agg',
                                  'gpu0_util',index,gpu_param)
    gpu_used_graph = gpu_used_header + gpu_used_sources + gpu_used_format
    gpu_mem_used_header = graph_header(start,stop,jobid,cluster,'agg',
                                  'gpu0_mem_util',index,gpu_param)
    gpu_mem_used_graph = gpu_mem_used_header + gpu_mem_used_sources + gpu_mem_used_format
    bytes_in_header = graph_header(start,stop,jobid,cluster,'agg',
                                  'bytes_in',index,gpu_param)
    bytes_in_graph = bytes_in_header + bytes_in_sources + bytes_in_format
    bytes_out_header = graph_header(start,stop,jobid,cluster,'agg',
                                  'bytes_out',index,gpu_param)
    bytes_out_graph = bytes_out_header + bytes_out_sources + bytes_out_format

    try:
        rrdtool.graph(mem_free_graph)
        rrdtool.graph(cpu_used_graph)
        rrdtool.graph(bytes_out_graph)
        rrdtool.graph(bytes_in_graph)
        if gpu_param:
            rrdtool.graph(gpu_used_graph)
            rrdtool.graph(gpu_mem_used_graph)
    except rrdtool.error:
        pass

def all_average_graph(start, stop, jobid, node_names, cluster, 
                graph_list, num_colors, gpu_param, missing_set):
    color_list = get_colors(num_colors)
    thickness = 'LINE1'

    mem_free_sources = []
    mem_free_format = []
    cpu_used_sources = []
    cpu_used_format = []
    gpu_used_sources = []
    gpu_used_format = []
    gpu_mem_used_sources = []
    gpu_mem_used_format = []
    bytes_out_sources = []
    bytes_out_format = []
    bytes_in_sources = []
    bytes_in_format = []

    counter = 0
    for data in graph_list:
        if data[1] in missing_set:
            pass
        else:
            if data[4] == 'mem_free.rrd':
                mem_free_sources.append('DEF:mem_free{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                mem_free_sources.append('VDEF:mem_free_avg{i}=mem_free{i},AVERAGE'.format(i=counter))
                if counter == 0:
                    mem_free_format.append('COMMENT:               MAX       MIN      AVERAGE                ') 
                mem_free_format.append('{L}:mem_free_avg{i}{color}:{n}'.format(
                      L=thickness, i=counter, color=color_list[counter], n=data[1]))
                mem_free_format.append('GPRINT:mem_free{i}:MAX:%6.2lf %s'.format(i=counter))
                mem_free_format.append('GPRINT:mem_free{i}:MIN:%6.2lf %s'.format(i=counter))
                mem_free_format.append('GPRINT:mem_free{i}:AVERAGE:%6.2lf %s\l'.format(i=counter))

            elif data[4] == 'cpu_user.rrd':
                cpu_used_sources.append('DEF:cpu_user{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                cpu_used_sources.append('VDEF:cpu_user_avg{i}=cpu_user{i},AVERAGE'.format(i=counter))
                if counter == 0:
                    cpu_used_format.append('COMMENT:                MAX        MIN       AVERAGE            ')
                cpu_used_format.append('{L}:cpu_user_avg{i}{color}:{n}'.format(
                      L=thickness, i=counter, color=color_list[counter], n=data[1]))
                cpu_used_format.append('GPRINT:cpu_user{i}:MAX:%6.1lf %% '.format(i=counter))
                cpu_used_format.append('GPRINT:cpu_user{i}:MIN:%6.1lf %% '.format(i=counter))
                cpu_used_format.append('GPRINT:cpu_user{i}:AVERAGE:%6.1lf %% \l'.format(i=counter))

            elif data[4] == 'gpu0_util.rrd':
                gpu_used_sources.append('DEF:gpu0_util{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                gpu_used_sources.append('VDEF:gpu_used_avg{i}=gpu0_util{i},AVERAGE'.format(i=counter))
                if counter == 0:
                    gpu_used_format.append('COMMENT:                MAX        MIN       AVERAGE            ')
                gpu_used_format.append('{L}:gpu_used_avg{i}{color}:{n}'.format(
                      L=thickness, i=counter, color=color_list[counter], n=data[1]))
                gpu_used_format.append('GPRINT:gpu0_util{i}:MAX:%6.1lf %s%%'.format(i=counter))
                gpu_used_format.append('GPRINT:gpu0_util{i}:MIN:%6.1lf %s%%'.format(i=counter))
                gpu_used_format.append('GPRINT:gpu0_util{i}:AVERAGE:%6.1lf %s%%\l'.format(i=counter))

            elif data[4] == 'gpu0_mem_util.rrd':
                gpu_mem_used_sources.append('DEF:gpu0_mem_util{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                gpu_mem_used_sources.append('VDEF:gpu_mem_used_avg{i}=gpu0_mem_util{i},AVERAGE'.format(i=counter))
                if counter == 0:
                    gpu_mem_used_format.append('COMMENT:               MAX       MIN      AVERAGE                ')
                gpu_mem_used_format.append('{L}:gpu_mem_used_avg{i}{color}:{n}'.format(
                      L=thickness, i=counter, color=color_list[counter], n=data[1]))
                gpu_mem_used_format.append('GPRINT:gpu0_mem_util{i}:MAX:%6.2lf %s'.format(i=counter))
                gpu_mem_used_format.append('GPRINT:gpu0_mem_util{i}:MIN:%6.2lf %s'.format(i=counter))
                gpu_mem_used_format.append('GPRINT:gpu0_mem_util{i}:AVERAGE:%6.2lf %s\l'.format(i=counter))

            elif data[4] == 'bytes_in.rrd':
                bytes_in_sources.append('DEF:bytes_in{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                bytes_in_sources.append('VDEF:bytes_in_avg{i}=bytes_in{i},AVERAGE'.format(i=counter))
                if counter == 0:
                    bytes_in_format.append('COMMENT:               MAX       MIN      AVERAGE                ')
                bytes_in_format.append('{L}:bytes_in_avg{i}{color}:{n}'.format(
                      L=thickness, i=counter, color=color_list[counter], n=data[1]))
                bytes_in_format.append('GPRINT:bytes_in{i}:MAX:%6.0lf %s'.format(i=counter))
                bytes_in_format.append('GPRINT:bytes_in{i}:MIN:%6.0lf %s'.format(i=counter))
                bytes_in_format.append('GPRINT:bytes_in{i}:AVERAGE:%6.0lf %s\l'.format(i=counter))

            elif data[4] == 'bytes_out.rrd':
                bytes_out_sources.append('DEF:bytes_out{i}={p}:sum:AVERAGE'.format(
                      i=counter, p=data[0]))
                bytes_out_sources.append('VDEF:bytes_out_avg{i}=bytes_out{i},AVERAGE'.format(i=counter))
                if counter == 0:
                    bytes_out_format.append('COMMENT:               MAX       MIN      AVERAGE                ')
                bytes_out_format.append('{L}:bytes_out_avg{i}{color}:{n}'.format(
                      L=thickness, i=counter, color=color_list[counter], n=data[1]))
                bytes_out_format.append('GPRINT:bytes_out{i}:MAX:%6.0lf %s'.format(i=counter))
                bytes_out_format.append('GPRINT:bytes_out{i}:MIN:%6.0lf %s'.format(i=counter))
                bytes_out_format.append('GPRINT:bytes_out{i}:AVERAGE:%6.0lf %s\l'.format(i=counter))
                counter += 1

                            # [start,stop,jobid,cluster,graph_type,rrd_type]
    mem_free_header = graph_header(start,stop,jobid,cluster,'avg',
                                  'mem_free',0,gpu_param)
    mem_free_graph = mem_free_header + mem_free_sources + mem_free_format
    cpu_used_header = graph_header(start,stop,jobid,cluster,'avg',
                                  'cpu_used',0,gpu_param)
    cpu_used_graph = cpu_used_header + cpu_used_sources + cpu_used_format
    gpu_used_header = graph_header(start,stop,jobid,cluster,'avg',
                                  'gpu_used',0,gpu_param)
    gpu_used_graph = gpu_used_header + gpu_used_sources + gpu_used_format
    gpu_mem_used_header = graph_header(start,stop,jobid,cluster,'avg',
                                  'gpu_mem_used',0,gpu_param)
    gpu_mem_used_graph = gpu_mem_used_header + gpu_mem_used_sources + gpu_mem_used_format
    bytes_in_header = graph_header(start,stop,jobid,cluster,'avg',
                                  'bytes_in',0,gpu_param)
    bytes_in_graph = bytes_in_header + bytes_in_sources + bytes_in_format
    bytes_out_header = graph_header(start,stop,jobid,cluster,'avg',
                                  'bytes_out',0,gpu_param)
    bytes_out_graph = bytes_out_header + bytes_out_sources + bytes_out_format
    try:
        rrdtool.graph(mem_free_graph)
        rrdtool.graph(cpu_used_graph)
        rrdtool.graph(bytes_out_graph)
        rrdtool.graph(bytes_in_graph)
        if gpu_param:
            rrdtool.graph(gpu_used_graph)
            rrdtool.graph(gpu_mem_used_graph)
    except rrdtool.error:
        pass


def single_node_graphs(start, stop, data, gpu_param):
    path, nodename, cluster, jobid, graph_type = data

    # print path

    if 'himem' in nodename:
        nodename ='node' + nodename

    if graph_type == 'mem_free.rrd':
        rrdtool.graph('web/static/job/{j}/{g}/{g}_{n}.png'.format(g='mem_free', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Amount Free',
              '--title', 'Free Memory in {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:mem_free={p}:sum:AVERAGE'.format(p=path),
              'LINE2:mem_free#FF0000:{n}'.format(n=nodename))

    elif graph_type == 'cpu_user.rrd':
        rrdtool.graph('web/static/job/{j}/cpu/{g}_{n}.png'.format(g='cpu_used', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Percent (%)',
              '--title', 'CPU used in {c} - {n}'.format(c=cluster, n=nodename),
              '--lower-limit', '-1',
              'DEF:cpu_user={p}:sum:AVERAGE'.format(p=path),
              'LINE2:cpu_user#FF0000:{n}'.format(n=nodename))

    ## General network statistics
    elif graph_type == 'bytes_out.rrd':
        rrdtool.graph('web/static/job/{j}/{g}/{g}_{n}.png'.format(g='bytes_out', n=nodename, j=jobid),
              '--start', "{begin}".format(begin=start),
              '--end', "{end}".format(end=stop),
              '--vertical-label', 'Bytes',
              '--title', 'Network for {c} - {n}'.format(c=cluster, n=nodename),
              'DEF:bytes_out={p}:sum:AVERAGE'.format(p=path),
              'DEF:bytes_in={p}:sum:AVERAGE'.format(p=string.replace(
                                    path, 'bytes_out', 'bytes_in')),
              'LINE2:bytes_out#FF0000:Network Out - {n}'.format(n=nodename),
              'LINE2:bytes_in#0000FF:Network In - {n}'.format(n=nodename))

    # elif graph_type == 'bytes_out.rrd':
    #     rrdtool.graph('web/static/job/{j}/{g}/{g}_{n}.png'.format(g='bytes_out', n=nodename, j=jobid),
    #           '--start', "{begin}".format(begin=start),
    #           '--end', "{end}".format(end=stop),
    #           '--vertical-label', 'Bytes',
    #           '--title', 'Bytes Out for {c} - {n}'.format(c=cluster, n=nodename),
    #           'DEF:bytes_out={p}:sum:AVERAGE'.format(p=path),
    #           'LINE2:bytes_out#0000FF')

    # if gpu_param:
    #     if graph_type == 'gpu0_util.rrd':
    #         rrdtool.graph('web/static/job/{j}/{g}/{g}_{n}.png'.format(g='gpu0_util', n=nodename, j=jobid),
    #               '--start', "{begin}".format(begin=start),
    #               '--end', "{end}".format(end=stop),
    #               '--vertical-label', 'Percent (%)',
    #               '--title', 'GPU used in {c} - {n}'.format(c=cluster, n=nodename),
    #               'DEF:gpu0_util={p}:sum:AVERAGE'.format(p=path),
    #               'LINE2:gpu0_util#FF0000:{n}'.format(n=nodename))
    #     if graph_type == 'gpu0_mem_util.rrd':
    #         rrdtool.graph('web/static/job/{j}/{g}/{g}_{n}.png'.format(g='gpu0_mem_util', n=nodename, j=jobid),
    #               '--start', "{begin}".format(begin=start),
    #               '--end', "{end}".format(end=stop),
    #               '--vertical-label', 'Percent (%)',
    #               '--title', 'GPU Memory used in {c} - {n}'.format(c=cluster, n=nodename),
    #               'DEF:gpu0_mem_util={p}:sum:AVERAGE'.format(p=path),
    #               'LINE2:gpu0_mem_util#FF0000:{n}'.format(n=nodename))

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
