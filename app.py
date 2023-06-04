from flask import Flask, render_template, url_for

app = Flask(__name__)

#MySQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tp055241@localhost/ldpms'
@app.route('/')
def index():
    return render_template('homepage.html')

if __name__ == "__main__":
    app.run(debug=True)
