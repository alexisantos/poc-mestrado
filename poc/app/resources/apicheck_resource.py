from flask_restful import Resource

class APIcheck_Resource(Resource):
    print(Resource)
    def get(self):
        return {"message": "API is working"}