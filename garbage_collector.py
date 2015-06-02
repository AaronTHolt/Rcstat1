import time
import os
import shutil

# run with:
# $nohup python garbage_collector.py </dev/null &>/dev/null &

#delete plots and text files that are over one week old
one_week_ago = time.time() - 604800
# one_minutes_ago = time.time() - 60  #for testing
directory1 = 'web/static/plots/'
directory2 = 'sacct_output/'

while True:
    os.chdir(directory1)
    for somefile in os.listdir('.'):
        st=os.stat(somefile)
        mtime=st.st_mtime
        if mtime < one_week_ago:
            # print('remove %s'%somefile)
            shutil.rmtree(somefile) 

    os.chdir('../../../')
    os.chdir(directory2)
    for somefile in os.listdir('.'):
        st=os.stat(somefile)
        mtime=st.st_mtime
        if mtime < one_week_ago:
            # print('remove %s'%somefile)
            os.unlink(somefile) 
    os.chdir('../')


    time.sleep(86400)  #run daily