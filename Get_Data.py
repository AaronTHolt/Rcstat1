#Test Cases
#Get data from txt file assuming slurm sacct was run and piped into txt file
from Utility import *
import subprocess

def get_data(jobid, debug):

    cmd = 'sacct -P -j {j} -o Start,End,Nodelist,Partition,JobId > sacct_output/{j}.txt'.format(j=jobid)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()

    # Handle: Broken sacct
    if 'sacct: error: Problem talking to the database: Connection timed out' in err:
        return False, False, False, False

    # Handle: No data from sacct command
    file_length = sum(1 for line in open('sacct_output/{j}.txt'.format(j=jobid)))
    if file_length <= 1:
        return False, False, False, False

    with open('sacct_output/{j}.txt'.format(j=jobid), 'r') as f:
        data = f.read()
    f.close()

    t1, t2, node_names, cluster_names = parse_job_file(data)

    #convert cluster names to match directory names in rrd
    cluster_names = convert_cluster_names(cluster_names)

    # Expand nodes if necessary and flatten nested lists
    node_names = expand_node_list(node_names)
    
    ## Use long time window for debugging
    # t1 = '2015-05-25T10:00:00'
    # t2 = 'now'

    if t1 == 'Unknown':
        start = t1
        stop = t1
    else:
        start = convert_enddate_to_seconds(t1)
        start += 3600*6
        # Handle: Job not yet finished
        try:
            stop = convert_enddate_to_seconds(t2)
            stop += 3600*6
            # stop = 'now'
        except ValueError:
            return False, False, False, False
            # stop = 'now'
    # print start, stop

    return start, stop, cluster_names, node_names
