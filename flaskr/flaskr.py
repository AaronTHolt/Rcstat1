# all the imports
import sqlite3
import rrdtool
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
import os

from emailrrd import send_email

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our Flask instance
app = Flask(__name__)
app.config.from_object(__name__)
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)

## Initialize db
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

## Display blog posts (stored in sqlite db)
@app.route('/')
def show_entries():
    cur = g.db.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)

## Add entries to blog
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

## Button that goes to the graphs
@app.route('/graph_button', methods=['POST'])
def redirect_to_graphs():
    if not session.get('logged_in'):
        abort(401)
    return render_template('graph_page.html')
    # return app.send_static_file('speed4.png')

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
## the cache is reset (so the graph updates)
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