# Utility Functions

import time
from calendar import timegm
from datetime import datetime
import hostlist

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


def expand_node_list(node_list):
    nodes = []
    for node in node_list:
        nodes.append(hostlist.expand_hostlist(node))

    flat_node_list = [item for sublist in nodes for item in sublist]
    # print flat_node_list
    return flat_node_list


def parse_job_file(data):
    t1 = ''
    t2 = ''
    # jobid = 0
    node_names = []
    cluster_names = []
    line_number = 0
    for line in data.split('\n'):
        if line_number == 1:
            line_split = line.split('|')
            # print line.split('|')
            t1 = line_split[0]
            t2 = line_split[1]
            node_names.append(line_split[2])
            cluster_names.append(line_split[3])
            # jobid = int(float(line_split[4]))
        # print line
        line_number += 1

    return t1, t2, node_names, cluster_names