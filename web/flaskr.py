# all the imports
import rrdtool
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
import os
from PIL import Image
import StringIO

from graphing import *
from emailrrd import send_email


# configuration
DEBUG = True
SECRET_KEY = 'super secret development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create Flask instance
app = Flask(__name__)
app.config.from_object(__name__)
# app.config["CACHE_TYPE"] = "null"

# app.config.from_envvar('FLASKR_SETTINGS', silent=True)


## Display main page
@app.route('/')
def show_entries():
    return render_template('show_entries.html')

## To email graphs
@app.route('/email', methods=['POST'])
def redirect_to_email():
    if not session.get('logged_in'):
        abort(401)
    return render_template('email_page.html')

## Submit jobid button
@app.route('/graph_summary', methods=['POST'])
def redirect_to_summary_graphs():
    if not session.get('logged_in'):
        abort(401)
    return redirect_to_graphs('all')

## CPU button
@app.route('/graph_select', methods=['POST'])
def graph_selection():
    if not session.get('logged_in'):
        abort(401)
    # graph_type = 'cpu'
    graph_type = request.form['action']
    jobid = session['jobid']

    category = ''
    if graph_type == 'all' or graph_type == 'avg':
        category = ''
    else:
        category = 'node'

    images = get_images(jobid, graph_type, category)
    error = None
    return render_template('all_graph.html', images=images, jobid=jobid,
                             error=error, gpu_param=session['gpu_param'])


## After submit button or buttons on all_graph
# @app.route('/graph_button2', methods=['POST'])
def redirect_to_graphs(graph_type):
    if not session.get('logged_in'):
        abort(401)

    error = None
    jobid = request.form['text']
    session['jobid'] = jobid

    # Empty input
    if jobid == '':
        error = 'Please enter a Job ID'
        return render_template('show_entries.html', error=error)

    ## TODO: sanitize input
    ## no input, letters input, html input
    #jobid = sanitize(jobid)

    # Generate graphs, if gpu job returns true
    try:
        gpu_param, missing_set = process(jobid)
        session['gpu_param'] = gpu_param
    except IOError:
        error = 'No matching Job ID found'
        return render_template('show_entries.html', error=error)

    images = get_images(jobid, graph_type, 'all')
    session['images'] = images
        
    total_image_number = get_images(jobid, graph_type, 'cpu')
    # images = sorted(images)
    ## TODO: raise exception that a job wasn't found...
    # Input that wasn't a job
    if len(total_image_number)<0:
        error = 'No matching Job ID found {i}'.format(i=len(total_image_number))
        return render_template('show_entries.html', error=error)
    return render_template('all_graph.html', images=images, 
                            jobid=jobid, error=error, gpu_param=gpu_param)

#Email page back to graph page
@app.route('/graphs2', methods=['POST'])
def redirect_to_graphs2():
    if not session.get('logged_in'):
        abort(401)
    return render_template('all_graph.html', images=session['images'], 
                            jobid=session['jobid'], error=None, 
                            gpu_param=session['gpu_param'])

## Button back to main page
@app.route('/main', methods=['POST'])
def redirect_to_main():
    if not session.get('logged_in'):
        abort(401)
    return redirect(url_for('show_entries'))

## Emailbutton onclick
@app.route('/email_it', methods=['POST'])
def send_an_email():
    if not session.get('logged_in'):
        abort(401)
    addr = request.form['text']
    # print "ADDRESS SENT TO", addr
    send_email(addr, session['jobid'])
    return render_template('email_page.html')

## Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

## Logout link
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

def get_images(jobid, graph_type, category):
    images = []
    WIDTH = 1000
    HEIGHT = 800
    for root, dirs, files in os.walk('flaskr/static/'):
    # for root, dirs, files in os.walk('.'):
        # print root, dirs, files
        for filename in [os.path.join(root, name) for name in files]:
            # print filename, jobid, graph_type, category
            # if not '519035' in filename:
            #     continue
            if not '/'+str(jobid)+'/' in filename:
                continue
            if not category in filename:
                continue
            if not graph_type in filename:
                continue
            if not filename.endswith('.png'):
                continue
            im = Image.open(filename)
            w, h = im.size
            aspect = 1.0*w/h
            if aspect > 1.0*WIDTH/HEIGHT:
                width = min(w, WIDTH)
                height = width/aspect
            else:
                height = min(h, HEIGHT)
                width = height*aspect
            temp = filename.split('/')
            filename = temp[1]+'/'+temp[2]+'/'+temp[3]+'/'+temp[4]
            images.append({
                'width': int(width),
                'height': int(height),
                'src': filename
            })
    images = sorted(images)
    if graph_type == 'all' or graph_type == 'avg':
        images = sorted(images, reverse=True)
    return images

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


if __name__ == '__main__':
    # app.run()
    app.run(host='0.0.0.0')
