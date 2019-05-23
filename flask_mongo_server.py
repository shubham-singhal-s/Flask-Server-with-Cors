from flask import abort,request, json, Flask
from flask_cors import CORS, cross_origin


app = Flask(__name__)
app.config["DEBUG"] = True
app.jinja_env.cache = {}

@app.errorhandler(404)
@cross_origin()
def custom404(error):
    logger.error("Model doesn't exist",extra={'type':'error','error_code':'404'})
    response = json.dumps({'message': "Model doesn't exist."})
    return response,404,{'ContentType':'application/json'}


@app.route('/', methods = ['POST'])
@cross_origin()
def api_message():

    if request.headers['Content-Type'] == 'application/json':
        message = request.json
        result = {'message' : message}

        return json.dumps(result),200,{'ContentType':'application/json'}

    else:
        abort(415)
        
        
@app.route('/shutdown', methods = ['POST'])
@cross_origin()
def app_shutdown():
    if request.headers['Content-Type'] == 'application/json':
        message = request.json
        ret = "Auth Failed"
        try:
            key = message["key"]
        except:
            abort(422)
        #Check for Authentication
        if key == config_data['server_key']:
            ret = "Server Down"
            logger.info('Shutting down server',extra={'type':'kill'})
            func = request.environ.get('werkzeug.server.shutdown')
            
            #Kill all processes
            for r in running:
                kill_proc_tree(r.pid, True)
            
            print("-------------------------------------------------------------Server SHUTDOWN--------------------------------------------------------------------")
            # Exit Flask
            func()
        else:
            abort(422)
    else: abort(415)
    return json.dumps({"message":"Server Down"}),200,{'ContentType':'application/json'}

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8008,threaded=True)
