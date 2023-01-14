from flask import Flask, request
from flask_cors import CORS
from database import Database, DatabaseException

#SERVER WILL USE SSL/NOSSL ON DIFFERENT PORTS
api = Flask(__name__)
CORS(api)
db = Database() 
    
@api.route('/webdb/api/v1.0/login', methods=['POST'])
def login():
    if not request.is_json():
        return {"error": "Invalid Request Type!"}, 400
    data = request.get_json()
    user = data['username']
    pw = data['password']
    try:
        token = db.login(user, pw)
        return {"token": token}, 200
    except DatabaseException as e:
        return {"error": str(e)}, 400

@api.route('/webdb/api/v1.0/databases', methods=['GET'])
def databases():
    #get the token from the header
    if not request.headers.get('Authorization'):
        return {"error": "No Authorization token presented!"}, 401
    token = request.headers.get('Authorization')[7:]
    if not db.verify_user_token(token):
        return {"error": "Invalid Authorization token!"}, 401
    dbs = db.list_databases()
    return {"databases": dbs}, 200

@api.route('/webdb/api/v1.0/update/<database>/<schema>/<table>', methods=['POST'])
def update(database, schema, table):
    #get the token from the header
    if not request.headers.get('Authorization'):
        return {"error": "No Authorization token presented!"}, 401
    token = request.headers.get('Authorization')[7:]
    if not db.verify_user_token(token):
        return {"error": "Invalid Authorization token!"}, 401
    user = db.get_user_from_token(token)
    if user == None:
        return {"error": "Invalid Authorization token!"}, 401
    if not request.is_json():
        return {"error": "Invalid Request Type!"}, 400
    data = request.get_json()
    condition = data["condition"]
    try:
        db.update_table(user, database, schema, table, condition)
        return {"message": f"Table {database}.{schema}.{table} updated successfully!"}, 200
    except DatabaseException as e:
        return {"error": str(e)}, 400
    
def run_api(api: Flask):
    api.run(port=5555)