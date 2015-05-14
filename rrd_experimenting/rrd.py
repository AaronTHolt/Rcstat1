
import time
import re
import subprocess

cmd = """rrdtool create temptrax.rrd --start N --step 5 \
DS:Core0:GAUGE:100:0:100 \
DS:Core1:GAUGE:100:0:100 \
DS:Core2:GAUGE:100:0:100 \
DS:Core3:GAUGE:100:0:100 \
RRA:MAX:0.5:1:10000"""
# cmd = """rrdtool create temptrax.rrd --start N --step 5 \
# DS:Core0:GAUGE:100:0:100 \
# RRA:AVERAGE:0.5:1:10000"""
subprocess.call(cmd, shell=True)


cmd2 = "rrdtool update temptrax.rrd N"
# cmd2 = "rrdtool update temptrax.rrd -t Core0:Core1:Core2:Core3 N"
while True:
	output = subprocess.check_output(["sensors"])
	# print "OUTPUT = ", output
	output = output.split('\n')

	CoreTemps = {}
	key = ''
	val = ''
	for line in range(0,len(output)):
		# print line, output[line]
		if line==2 or line==3 or line==4 or line==5:
			key = output[line][0:6]
			# print key
			val = output[line].split('+')
			val = val[1].split('\xc2')
			# print key+':', float(val[0])
			CoreTemps[key]=val[0]
			# update = cmd2+str(float(val[0]))
			# subprocess.call(update, shell=True)

	update = cmd2
	for item in CoreTemps:
		update += ':' + str(CoreTemps[item])
		# print item, CoreTemps[item]
	print update
	subprocess.call(update, shell=True)
	now = time.time()
	start = now-600 
	cmd3 = """rrdtool graph ../flaskr/static/temp.png --start {s} --end {e} \
	--vertical-label "temperature (C)" \
	--title "CPU Core Temperature" \
	DEF:mytemp=temptrax.rrd:Core0:MAX \
	DEF:mytemp1=temptrax.rrd:Core1:MAX \
	DEF:mytemp2=temptrax.rrd:Core2:MAX \
	DEF:mytemp3=temptrax.rrd:Core3:MAX \
	LINE2:mytemp#0000FF:"Core1  " \
	GPRINT:mytemp:LAST:"Current\:%6.2lf %s"  \
	GPRINT:mytemp:AVERAGE:"Average\:%6.2lf %s"  \
	GPRINT:mytemp:MAX:"Maximum\:%6.2lf %s" \
	COMMENT:"\\n" \
	LINE2:mytemp1#00FF00:"Core2  " \
	GPRINT:mytemp1:LAST:"Current\:%6.2lf %s"  \
	GPRINT:mytemp1:AVERAGE:"Average\:%6.2lf %s"  \
	GPRINT:mytemp1:MAX:"Maximum\:%6.2lf %s" \
	COMMENT:"\\n" \
	LINE2:mytemp2#FF00FF:"Core3  " \
	GPRINT:mytemp2:LAST:"Current\:%6.2lf %s"  \
	GPRINT:mytemp2:AVERAGE:"Average\:%6.2lf %s"  \
	GPRINT:mytemp2:MAX:"Maximum\:%6.2lf %s" \
	COMMENT:"\\n" \
	LINE2:mytemp3#FF0000:"Core4  " \
	GPRINT:mytemp3:LAST:"Current\:%6.2lf %s"  \
	GPRINT:mytemp3:AVERAGE:"Average\:%6.2lf %s"  \
	GPRINT:mytemp3:MAX:"Maximum\:%6.2lf %s" \
	COMMENT:"\\n" \
	""".format(s=int(start), e=int(now))
	# print cmd3
	# subprocess.call(cmd3, shell=True)
	p = subprocess.Popen(cmd3, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	out, err = p.communicate()

	time.sleep(5)

	# cmd3 = """rrdtool graph ../flaskr/static/temp.png --start {s} --end {e} \
	# --vertical-label "temperature (C)" \
	# --title "CPU Core Temperature" \
	# --alt-autoscale-max \
	# DEF:mytemp=temptrax.rrd:Core0:MAX \
	# DEF:mytemp1=temptrax.rrd:Core1:MAX \
	# DEF:mytemp2=temptrax.rrd:Core2:MAX \
	# DEF:mytemp3=temptrax.rrd:Core3:MAX \
	# LINE2:mytemp#0000FF:"Core1" \
	# GPRINT:mytemp:LAST:"Current\:%8.2lf %s\n"  \
	# GPRINT:mytemp:AVERAGE:"Average\:%8.2lf %s"  \
	# GPRINT:mytemp:MAX:"Maximum\:%8.2lf %s\n" \
	# LINE2:mytemp1#00FF00:"Core2" \
	# GPRINT:mytemp1:LAST:"Current\:%8.2lf %s\n"  \
	# GPRINT:mytemp1:AVERAGE:"Average\:%8.2lf %s"  \
	# GPRINT:mytemp1:MAX:"Maximum\:%8.2lf %s\n" \
	# LINE2:mytemp2#FF00FF:"Core3" \
	# GPRINT:mytemp2:LAST:"Current\:%8.2lf %s\n"  \
	# GPRINT:mytemp2:AVERAGE:"Average\:%8.2lf %s"  \
	# GPRINT:mytemp2:MAX:"Maximum\:%8.2lf %s\n" \
	# LINE2:mytemp3#FF0000:"Core4" \
	# GPRINT:mytemp3:LAST:"Current\:%8.2lf %s\n"  \
	# GPRINT:mytemp3:AVERAGE:"Average\:%8.2lf %s"  \
	# GPRINT:mytemp3:MAX:"Maximum\:%8.2lf %s\n" \
	# """.format(s=int(start), e=int(now))