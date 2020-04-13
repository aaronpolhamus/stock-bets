from flask import Flask
from flask_restful import Resource, Api


app = Flask(__name__)


class HelloWorld(Resource):
    def get(self):
        return {"hello": "world"}


api = Api(app)
api.add_resource(HelloWorld, "/")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
