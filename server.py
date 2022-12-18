from flask import Flask
from flask import request, make_response, jsonify
from flask_cors import CORS
# from DD import get_df
import DD

app = Flask(__name__, static_folder="./build/static", template_folder="./build")
CORS(app) #Cross Origin Resource Sharing

@app.route("/", methods=['GET'])
def index():
    return "text parser:)"

@app.route("/get_df", methods=['GET','POST'])
def parse():
    data = request.get_json()
    id = data['id']

    res = DD.DD.get_df(id, 10, 10)
    response = {'result': res}
    #print(response)
    return make_response(jsonify(response))

if __name__ == "__main__":
    app.debug = True
    app.run(host='127.0.0.1', port=5000)
