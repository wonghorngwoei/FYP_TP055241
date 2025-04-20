from website import create_app
from flask import Flask, session

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
    session.clear()


# .\env\Scripts\activate
# $env:FLASK_DEBUG = "1" -- Run this before do your coding


