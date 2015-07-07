# all the imports
import rrdtool
import os
import string
import StringIO
import time
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from flask_limiter import Limiter
from contextlib import closing
from PIL import Image

from graphing import *
from Utility import convert_seconds_to_enddate, list_previous_jobs
from email_graphs import send_email

# configuration
SECRET_KEY = 'super secret development key'

# create Flask instance
app = Flask(__name__)
limiter = Limiter(app)
app.config.from_object(__name__)

## Display main page
@app.route('/rcstatmain')
def main_page(error=None):
    error = request.args.get('error')
    try:
        data = session['joblist']
        if len(data) == 0:
            data = None
    except KeyError:
        data = None
    return render_template('main_page.html', error=error, data=data)

## Button back to main page
@app.route('/main', methods=['GET', 'POST'])
def redirect_to_main():
    return redirect(url_for('main_page', error=None))

## Start page
@app.route('/', methods=['GET', 'POST'])
def login(error=None):
    if request.method == 'POST':
        return redirect(url_for('main_page', error=error))
    return redirect(url_for('main_page', error=error))

## To email graphs
@app.route('/email', methods=['GET', 'POST'])
def redirect_to_email():
    return render_template('email_page.html')

## Submit jobid button
@app.route('/graph_summary', methods=['GET', 'POST'])
def redirect_to_summary_graphs():
    return redirect_to_graphs('agg')

## Display a table of previous jobids
@app.route('/table_previous_jobids', methods=['GET', 'POST'])
def table_of_jobids():
    username = request.form['username']
    data = list_previous_jobs(username)
    session['joblist'] = data
    return redirect(url_for('main_page', error=None))

## Graph type selection button on-click
@app.route('/job/<id1>', methods=['GET', 'POST'])
def graph_selection(id1):
    graph_type = request.form['action']
    # jobid = session['jobid']
    jobid = id1
    return redirect(url_for('job', jobid=jobid, graph_type=graph_type))

## After submit button or buttons on all_graph
def redirect_to_graphs(graph_type):
    error = None
    jobid = request.form['text']
    valid, error = check_valid_jobid(jobid)
    if valid == False:
        return redirect(url_for('main_page', error=error))
    session['jobid'] = jobid
    return redirect(url_for('job', jobid=jobid, graph_type=graph_type))

#Email page back to graph page
@app.route('/graphs2', methods=['GET'])
def redirect_to_graphs2():
    return render_template('all_graph.html', images=session['images'], 
                            jobid=session['jobid'], error=None, 
                            gpu_param=session['gpu_param'],
                            start=session['start'], end=session['end'])

@app.route('/static/job/<jobid>/<graph_type>', methods=['GET', 'POST'])
def job(jobid, graph_type):
    '''Checks for valid jobids, generates graphs, directs
    to all_graph page to display if successful'''

    # Check for valid jobid inputs
    valid, error = check_valid_jobid(jobid)
    if valid == False:
        return redirect(url_for('main_page', error=error))

    # Decide whether aggregate graphs or single node graphs
    # will be loaded
    category = ''
    if graph_type == 'agg' or graph_type == 'avg':
        category = ''
    else:
        category = 'node'

    cat_image_number = get_num_images(jobid, graph_type, category)
    total_image_number = get_num_images(jobid, '', '')

    if cat_image_number <= 0:
        #rate limit slurm calls
        if total_image_number <= 0:
            try:
                if time.time() - session['last_slurm_call'] < 2.0:
                    time.sleep(1)
            #on the first load there is no 'last_slurm_call'
            except KeyError:
                pass

        try:
            gpu_param, missing_set, start, end = process(jobid, graph_type)
            if start == 'sacct not enabled':
                error = "sacct not enabled (6)"
                return redirect(url_for('main_page', error=error))
            elif start == 'Toolong':
                error = "jobid too large (it does'nt exist) (7)"
                return redirect(url_for('main_page', error=error))
            elif start == 'no data':
                error = "No job data found for {j}. (3)".format(j=jobid)
                return redirect(url_for('main_page', error=error))
            elif start == 'Unknown':
                error = 'No start time listed for job ID {j}. (4)'.format(j=jobid)
                return redirect(url_for('main_page', error=error))
            elif end == False or end == 'Unknown':
                error = "Job {j} hasn't run yet or is still running. (5)".format(j=jobid)
                return redirect(url_for('main_page', error=error))
            
            session['start'] = convert_seconds_to_enddate(start)
            session['end'] = convert_seconds_to_enddate(end)
            session['gpu_param'] = gpu_param
        except IOError:
            error = 'No matching Job ID found for job ID {j}. (1)'.format(j=jobid)
            return redirect(url_for('main_page', error=error))
        except Exception as e:
            return redirect(url_for('main_page', 
                error='Unexpected Error: {err}'.format(err=e)))

        session['last_slurm_call'] = time.time()
        cat_image_number = get_num_images(jobid, graph_type, category)

        # Valid input that wasn't a job
        if cat_image_number <= 0:
            error = 'No matching Job ID or no data for job ID {j}. (2)'.format(j=jobid)
            return redirect(url_for('main_page', error=error))

    images = get_images(jobid, graph_type, category)
    session['images'] = images
    error = None
    # return render_template('all_graph.html', images=images, jobid=jobid,
    #                         error=error, 
    #                         start=session['start'], end=session['end'])
    return render_template('all_graph.html', images=images, jobid=jobid,
                            error=error, gpu_param=session['gpu_param'],
                            start=session['start'], end=session['end'])


## Emailbutton onclick
@app.route('/email_it', methods=['POST'])
# @limiter.limit("20 per hour", "1 per second")
@limiter.limit("0.5 per second")
def send_an_email():
    error = None
    success = False

    #make sure all graphs have been generater
    process(session['jobid'], 'avg')
    process(session['jobid'], 'agg')

    addr = request.form['text']
    sent = send_email(addr, session['jobid'])
    if sent == False:
        error = 'Unable to send email'
    elif sent == 'NoImages':
        error = 'No images found'
    elif sent == True:
        success = True
        flash('Email Sent!')
    return render_template('email_page.html', error=error)

def get_num_images(jobid, graph_type, category):
    images = []
    for root, dirs, files in os.walk('web/static/job/{j}/{g}'.format(
                                    j=jobid, g=graph_type)):
        for filename in [os.path.join(root, name) for name in files]:
            if not category in filename:
                continue
            if not filename.endswith('.png'):
                continue
            images.append(filename)
    return len(images)

def get_images(jobid, graph_type, category):
    images = []
    WIDTH = 1000
    HEIGHT = 800
    for root, dirs, files in os.walk('web/static/job/{j}/{g}'.format(
                                    j=jobid, g=graph_type)):
        for filename in [os.path.join(root, name) for name in files]:
            if not category in filename:
                continue
            if not filename.endswith('.png'):
                continue
            im = Image.open(filename)
            width, height = im.size
            temp = filename.split('/')
            filename = temp[2]+'/'+temp[3]+'/'+temp[4]+'/'+temp[5]
            images.append({
                'width': int(width),
                'height': int(height),
                'src': filename
            })
    images = sorted(images)
    if graph_type == 'agg' or graph_type == 'avg':
        images = sorted(images, key=lambda k: k['src'], reverse=True)
    return images

def check_valid_jobid(jobid):
    #For jobid's with an '_'
    #check both sides are digits, check length
    if '_' in jobid:
        split_id = jobid.split('_')
        if ((len(split_id)>2) or (not split_id[0].isdigit()) or
            (not split_id[1].isdigit()) or (len(jobid)>=12)):
            error = '{j} is invalid. Please enter a valid Job ID.'.format(
                        j=jobid)
            return False, error
    # Handle: empty, non-numeric, negative, 9digit+
    elif not jobid.isdigit() or len(jobid)>=9:
        error = '{j} is invalid. Please enter a valid Job ID.'.format(
                        j=jobid)
        return False, error
    return True, None

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(429)
def too_many_requests(e):
    return render_template('429.html'), 429

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

## Next 2 sections make it so any time url_for is used
## the cache is reset (so the graphs update)
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


