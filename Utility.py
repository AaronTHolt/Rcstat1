# Utility Functions

import time
from calendar import timegm
import datetime
from datetime import datetime
import hostlist
import numpy as np
import colorsys
import subprocess

def convert_seconds_to_enddate(seconds):
    if seconds == 'now':
        return "Unknown / Still Running"
    return datetime.fromtimestamp(int(seconds)).strftime(
                                                '%Y-%m-%d %H:%M:%S')

#used to get a sacct usable date (to get users previous jobids)
def convert_seconds_to_enddate_2(seconds):
    return datetime.fromtimestamp(int(seconds)).strftime(
                                                '%Y-%m-%d')

def convert_enddate_to_seconds(ts):
    # Takes ISO 8601 format(string) and converts into epoch time.
    # Adding timezones will break this function!
    timestamp = timegm(time.strptime(ts,'%Y-%m-%dT%H:%M:%S'))
    return timestamp

def convert_cluster_names(cluster_list):
    #Make Slurm cluster names match directory names in rrd
    cluster_names = []
    for cluster in cluster_list:
        if cluster == 'blanca':
            cluster_names.append('Blanca')
        elif cluster == 'crc-serial':
            cluster_names.append('Crestone')
        elif cluster == 'crc-gpu':
            cluster_names.append('GPU')
        elif cluster == 'crc-himem':
            cluster_names.append('Himem')
        elif cluster == 'janus':
            cluster_names.append('Janus')
        else:
            cluster_names.append(cluster)

    return cluster_names

# Expands node lists such as 'node[0001-0010,0015]'
# into individual nodes
def expand_node_list(node_list):
    nodes = []
    for node in node_list:
        nodes.append(hostlist.expand_hostlist(node))
    flat_node_list = [item for sublist in nodes for item in sublist]
    return flat_node_list

# Flattens a list of lists
def flat_list(a_list):
    a_flat_list = [item for sublist in a_list for item in sublist]
    return a_flat_list

#get information about previous
def list_previous_jobs(username):
    info = []
    sorted_info = []

    now = time.time()
    some_time_ago = now - 2678400*2 #n months ago
    some_time_ago = convert_seconds_to_enddate_2(some_time_ago)

    cmd = 'sacct -P -u {u} -S {t} --format JobID,Start,End,State,Partition > sacct_output/{u}.txt'.format(u=username, t=some_time_ago)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()

    max_lines = 0
    #read in file backwards to get most recent jobs
    for line in reversed(open('sacct_output/{u}.txt'.format(u=username)).readlines()):
        line_split = line.split('|')
        if len(line_split) == 5:
            if ('batch' in line_split[0] or '.' in line_split[0] or 
                'Job' in line_split[0]):
                pass
            elif max_lines <= 25:
                line_split[1] = line_split[1].replace('T', ' ')
                line_split[2] = line_split[2].replace('T', ' ')
                info.append([line_split[0], line_split[1], line_split[2],
                                        line_split[3], line_split[4]])
                max_lines += 1
    return info


#parses a slurm sacct ouput file (for job information)
def parse_job_file(data):
    t1 = ''
    t2 = ''
    node_names = []
    cluster_names = []
    line_number = 0
    for line in data.split('\n'):
        if line_number == 1:
            line_split = line.split('|')
            t1 = line_split[0]
            t2 = line_split[1]
            node_names.append(line_split[2])
            cluster_names.append(line_split[3])
        line_number += 1

    return t1, t2, node_names, cluster_names

# Returns unique 8bit colors
def get_colors(num_colors):
    colors=[]
    for i in np.arange(0., 360., 360. / num_colors):
        hue = i/360.
        lightness = (50 + np.random.rand() * 10)/100.
        saturation = (90 + np.random.rand() * 10)/100.
        colors.append(colorsys.hls_to_rgb(hue, lightness, saturation))

    hex_colors = []
    for color in colors:
        hex_colors.append("#{0:02x}{1:02x}{2:02x}".format(
            clamp(int(color[0]*255)),  #r
            clamp(int(color[1]*255)),  #g
            clamp(int(color[2]*255)))) #b
        # print int(color[0]*255), int(color[1]*255), int(color[2]*255)
    return hex_colors

# Keep colors in 8bit range
def clamp(x): 
    return max(0, min(x, 255))

def get_rackname(node_number):
    rackname = 'Rack ' + node_number[4:6]
    return rackname
