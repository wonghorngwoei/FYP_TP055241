from flask import Flask, render_template, url_for

app = Flask(__name__)

#MySQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:tp055241@localhost/LDPMS'
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
