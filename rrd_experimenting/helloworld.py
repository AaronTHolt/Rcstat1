from flask import Flask
app = Flask(__name__)



@app.route("/")
def index():
    return 'Index Page'

#New url
@app.route('/hello')
def hello():
    return 'Hello World'

#Variable in url, can use int, float, or path
@app.route('/hello/<int:myint>')    
def varurl(myint):
    return "myint = %d" %myint

if __name__ == "__main__":
    app.run(debug=True)
