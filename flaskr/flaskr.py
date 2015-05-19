# all the imports
import rrdtool
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
import os
import Image
import StringIO

# from graphing import *
from emailrrd import send_email

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create Flask instance
app = Flask(__name__)
app.config.from_object(__name__)

# app.config.from_envvar('FLASKR_SETTINGS', silent=True)


## Display blog posts (stored in sqlite db)
@app.route('/')
def show_entries():

    return render_template('show_entries.html')

## Button that goes to the graphs
@app.route('/graph_button', methods=['POST'])
def redirect_to_graphs():
    if not session.get('logged_in'):
        abort(401)
    return render_template('graph_page.html')
    # return app.send_static_file('speed4.png')

## Submit onclick
@app.route('/graph_button2', methods=['POST'])
def redirect_to_graphs2():
    if not session.get('logged_in'):
        abort(401)
    images = []
    WIDTH = 1000
    HEIGHT = 800
    error = None

    jobid = request.form['text']

    # Empty input
    if jobid == '':
        error = 'Please enter a Job ID'
        return render_template('show_entries.html', error=error)

    ## TODO: sanitize input
    ## no input, letters input, html input

    #jobid = sanitize(jobid)

    for root, dirs, files in os.walk('.'):
        for filename in [os.path.join(root, name) for name in files]:
            # if not '519035' in filename:
            #     continue
            if not jobid in filename:
                continue
            if not 'all' in filename:
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
            images.append({
                'width': int(width),
                'height': int(height),
                'src': filename
            })
    ## TODO: raise exception that a job wasn't found...
    # Input that wasn't a job
    if len(images)<2:
        error = 'No matching Job ID found'
        return render_template('show_entries.html', error=error)
    return render_template('all_graph.html', images=images, error=error)

## Button back to blog page
@app.route('/blog', methods=['POST'])
def redirect_to_blog():
    if not session.get('logged_in'):
        abort(401)
    return redirect(url_for('show_entries'))

## Emailbutton onclick
@app.route('/email', methods=['POST'])
def send_an_email():
    if not session.get('logged_in'):
        abort(401)
    addr = request.form['text']
    send_email(addr)
    return render_template('graph_page.html')

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
    app.run()