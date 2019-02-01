"""
--------------------------CHAT API---------------------------
POST requests to: http://localhost:8008
Data format: {
  "sender": "sender_id",
  "message": "user_message",
  "model": "model_name"
}
Return format: [{"recipient_id": "sender_id", "text": "Bot's reply"}]

----------------------ADD AGENTS API-----------------------
POST requests to: http://localhost:8008/agent
Data format: {
  "model": "model_name",
  "nlu": "nlu_folder_name, eg: weathernlu",
  "dialogue": "core_folder_name, eg: dialogue"
}
Return format: Model loaded with name {}

--------------------GET AGENTS LIST API----------------------
GET requests to: http://localhost:8008/agent
Return format: ["model_name_1", "model_name_2"]

----------------------DELETE AGENTS API-----------------------
POST requests to: http://localhost:8008/agent
Data format: {
  "model": "model_name"
}
Return format: Model deleted with name {}

--------------------------ERRORS----------------------------
404: When specified model name doesn't exist
409: When model name already exists while creating a new one
415: Header isn't in application/json format
422: Data is missing from request body
500: Error occured during loading model object i.e. wrong nlu/core folder name
"""

from flask import abort,request, json, Flask
from flask_cors import CORS, cross_origin
from rasa_core.agent import Agent
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_core.utils import EndpointConfig
from pymongo import MongoClient


action_endpoint = EndpointConfig(url="http://localhost:5055/webhook")
agent_lst = {}

client = MongoClient('localhost', 27017)
db = client['pymongo_test']
posts = db.posts
# post_data = {
#     'title': 'agents',
#     'model': 'default',
#     'nlu': 'weathernlu',
#     'dialogue': 'dialogue'
# }
# post_data1 = {
#     'title': 'agents',
#     'model': '1',
#     'nlu': 'weathernlu2',
#     'dialogue': 'dialogue2'
# }
# result = posts.insert_many([post_data, post_data1])

agents_mongo = posts.find({'title': 'agents'})
for item in agents_mongo:
    nlu_interpreter1 = RasaNLUInterpreter('./models/nlu/default/'+item["nlu"])
    agent1 = Agent.load('./models/'+item["dialogue"], interpreter = nlu_interpreter1, action_endpoint = action_endpoint)
    agent_lst[item["model"]] = agent1


app = Flask(__name__)
app.config["DEBUG"] = True
#app.jinja_env.cache = {}

@app.errorhandler(404)
def custom400(error):
    response = json.dumps({'message': "Model doesn't exist."})
    return response

@app.errorhandler(409)
def custom400(error):
    response = json.dumps({'message': "Model already exists."})
    return response

@app.errorhandler(415)
def custom400(error):
    response = json.dumps({'message': "Header should be in json format."})
    return response

@app.errorhandler(422)
def custom400(error):
    response = json.dumps({'message': "Incomplete data in message body."})
    return response

@app.errorhandler(500)
def custom400(error):
    response = json.dumps({'message': "Error while creating model. Please check nlu/core folder names."})
    return response


@app.route('/', methods = ['POST'])
@cross_origin()
def api_message():

    if request.headers['Content-Type'] == 'application/json':
        message = request.json
        try:
            user_query = message["message"]
            sender_id = message["sender"]
            model = message["model"]
        except:
            abort(422)
        print(model)
        x = None
        if model not in agent_lst:
            abort(404)
        agent_curr = agent_lst[model]
        x = agent_curr.handle_text(text_message=user_query,sender_id=sender_id)

        return json.dumps(x)

    else:
        abort(415)


@app.route('/agent', methods = ['POST'])
@cross_origin()
def create_agent():

    if request.headers['Content-Type'] == 'application/json':
        message = request.json
        try:
            dialogue = message["dialogue"]
            nlu = message["nlu"]
            model = message["model"]
        except:
            abort(422)

        if model in agent_lst:
            abort(409)

        post_data = {
            'title': 'agents',
            'model': model,
            'nlu': nlu,
            'dialogue': dialogue
        }

        result = posts.insert_one(post_data)

        try:
            nlu_interpreter = RasaNLUInterpreter('./models/nlu/default/'+nlu)
            agent = Agent.load('./models/'+dialogue, interpreter = nlu_interpreter, action_endpoint = action_endpoint)
        except Exception as e:
            print(e)
            abort(500)
        agent_lst[model] = agent
        print("New agent ({}) added.".format(model))

        return "Model loaded with name {}".format(model)

    else:
        abort(415)

@app.route('/agent', methods = ['GET'])
@cross_origin()
def get_agent():
    lst = [*agent_lst]
    print(lst)
    return json.dumps(lst)


@app.route('/agent', methods = ['DELETE'])
@cross_origin()
def delete_agent():

    if request.headers['Content-Type'] == 'application/json':
        message = request.json
        try:
            model = message["model"]
        except:
            abort(422)

        if model not in agent_lst:
            abort(404)

        result = posts.delete_one({'model': model})

        try:
            agent_lst.pop(model)
        except Exception as e:
            print(e)
            abort(500)
        
        print("Deleted agent ({}).".format(model))

        return "Model deleted with name {}".format(model)

    else:
        abort(415)

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8008,threaded=True)