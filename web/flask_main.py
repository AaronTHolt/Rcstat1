# all the imports
import rrdtool
import os
import string
import StringIO
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from PIL import Image

from graphing import *
from Utility import convert_seconds_to_enddate
from emailrrd import send_email


# configuration
# DEBUG = True
SECRET_KEY = 'super secret development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create Flask instance
app = Flask(__name__)
app.config.from_object(__name__)
# app.config['SERVER_NAME'] = '0.0.0.0:5000'

## Display main page
@app.route('/rcstatmain')
def show_entries():
    return render_template('show_entries.html')

## Button back to main page
@app.route('/main', methods=['GET', 'POST'])
def redirect_to_main():
    return redirect(url_for('show_entries'))

# Login page
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        return redirect(url_for('show_entries'))
    return redirect(url_for('show_entries'))

## To email graphs
@app.route('/email', methods=['GET', 'POST'])
def redirect_to_email():
    return render_template('email_page.html')

## Submit jobid button
@app.route('/graph_summary', methods=['GET', 'POST'])
def redirect_to_summary_graphs():
    return redirect_to_graphs('agg')

## Graph type selection button on-click
# @app.route('/graph_select', methods=['POST'])
@app.route('/job-<id1>', methods=['GET', 'POST'])
def graph_selection(id1):
    graph_type = request.form['action']
    # jobid = session['jobid']
    jobid = id1
    return redirect(url_for('job', jobid=jobid, graph_type=graph_type))

## After submit button or buttons on all_graph
# @app.route('/graph_button2', methods=['POST'])
def redirect_to_graphs(graph_type):
    error = None
    jobid = request.form['text']
    session['jobid'] = jobid

    # Handle: empty, non-numeric, negative, 9digit+
    if not jobid.isdigit() or len(jobid)>=9:
        error = 'Please enter a valid Job ID'
        return render_template('show_entries.html', error=error)

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
    # print jobid, graph_type
    # Generate graphs, check if gpu job

    category = ''
    if graph_type == 'agg' or graph_type == 'avg':
        category = ''
    else:
        category = 'node'

    cat_image_number = get_num_images(jobid, graph_type, category)

    if cat_image_number <= 0:
        try:
            gpu_param, missing_set, start, end = process(jobid, graph_type)
            if start == 'Unknown':
                error = '''No start time listed. 
                        Visit 'Main Page' to try a different Job ID.'''
                return render_template('all_graph.html', jobid=jobid,
                                    error=error)
            elif start == False:
                error = '''No job data found.
                        Visit 'Main Page' to try a different Job ID.'''
                return render_template('all_graph.html', jobid=jobid,
                                    error=error)
            session['start'] = convert_seconds_to_enddate(start)
            session['end'] = convert_seconds_to_enddate(end)
            session['gpu_param'] = gpu_param
        except IOError:
            error = '''No matching Job ID found.
                    Visit 'Main Page' to try a different Job ID.'''
            return render_template('all_graph.html', jobid=jobid, 
                                    error=error)

        cat_image_number = get_num_images(jobid, graph_type, category)
        # print "NUM IMAGES = ", cat_image_number

        # Input that wasn't a job
        if cat_image_number <= 0:
            error = '''No matching Job ID or no data.
                    Visit 'Main Page' to try a different Job ID.'''
            return render_template('all_graph.html', jobid=jobid,
                                    error=error)

    
    images = get_images(jobid, graph_type, category)
    session['images'] = images
    error = None
    return render_template('all_graph.html', images=images, jobid=jobid,
                            error=error, gpu_param=session['gpu_param'],
                            start=session['start'], end=session['end'])

## Emailbutton onclick
@app.route('/email_it', methods=['POST'])
def send_an_email():
    error = None
    addr = request.form['text']
    # print "ADDRESS SENT TO", addr
    sent = send_email(addr, session['jobid'])
    if sent == False:
        error = 'Unable to send email'
    return render_template('email_page.html', error=error)

def get_num_images(jobid, graph_type, category):
    images = []
    # for root, dirs, files in os.walk('web/static/'):
    for root, dirs, files in os.walk('web/static/job/{j}/{g}'.format(
                                    j=jobid, g=graph_type)):
        for filename in [os.path.join(root, name) for name in files]:
            # if not '/'+str(jobid)+'/' in filename:
            #     continue
            if not category in filename:
                continue
            # if not graph_type in filename:
            #     continue
            if not filename.endswith('.png'):
                continue
            images.append(filename)
    return len(images)

def get_images(jobid, graph_type, category):
    images = []
    WIDTH = 1000
    HEIGHT = 800
    # for root, dirs, files in os.walk('web/static/'):
    for root, dirs, files in os.walk('web/static/job/{j}/{g}'.format(
                                    j=jobid, g=graph_type)):
        for filename in [os.path.join(root, name) for name in files]:
            # if not '/'+str(jobid)+'/' in filename:
            #     continue
            if not category in filename:
                continue
            # if not graph_type in filename:
            #     continue
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

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


# if __name__ == '__main__':
#     # app.run()
#     app.run(host='10.225.160.55')
