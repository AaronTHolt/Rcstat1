#Himem Test Cases
from Utility import *

def HimemExample1():
    # Data from job 660771
    with open('test_cases/jobs/660771.txt', 'r') as f:
        data = f.read()
    f.close()

    t1, t2, node_names, cluster_names = parse_job_file(data)

    #convert cluster names to match directory names in rrd
    cluster_names = convert_cluster_names(cluster_names)

    # Expand nodes if necessary and flatten nested lists
    node_names = expand_node_list(node_names)
    
    # Made up jobid (assuming a user input one)
    jobid = 660771

    # Use 3 month window for debugging
    # t1 = '2015-02-13T10:21:00'
    # t2 = '2015-05-14T09:44:02'

    start = convert_enddate_to_seconds(t1)
    stop = convert_enddate_to_seconds(t2)
    # print start, stop

    return start, stop, cluster_names, node_names