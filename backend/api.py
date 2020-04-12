from app import app


@app.route('/')
def get():
    return "<h1>Hello world</h1>"
