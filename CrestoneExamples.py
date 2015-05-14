#Crestone Example 1
from Utility import convert_enddate_to_seconds

def CrestoneExample1():
    # Made up times
    t1 = '2015-02-13T10:21:00'
    t2 = '2015-05-14T09:44:02'
    start = convert_enddate_to_seconds(t1)
    stop = convert_enddate_to_seconds(t2)

    # Made up jobid
    jobid = 654321

    cluster_names = []
    node_names = []
    cluster_names.append('rrds/Crestone')
    node_names.append('cnode0101')
    node_names.append('cnode0102')
    node_names.append('dms5k0002')

    return start, stop, cluster_names, node_names, jobid
