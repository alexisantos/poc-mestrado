from flask_restful import Resource
from flask_restful import reqparse
from flask import request
from app.models.traduzir_models import check_entity_inputs
from jsonpath_ng import jsonpath, parse


class TraduzirResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('queryResult', type=dict, required=True, help='O campo "queryResult" é obrigatório')

    def post(self):
        green_color = "\033[32m"
        reset_color = "\033[0m"

        #body_text = request.data.decode('utf-8')
        data = TraduzirResource.parser.parse_args()
        output_contexts = data["queryResult"]["outputContexts"]
        # jsonpath para: $.queryResult.outputContexts[?(@.name.endsWith('contexts/output'))].parameters
        match_contexts = [context for context in output_contexts if context["name"].endswith('contexts/output')]
        print(f"{green_color}\ndiaglogflow Data: {reset_color}{data}\n")
        if match_contexts:
            dialogflow_intent = match_contexts[0]['parameters']
            #print(dialogflow_intent)
            feedback = dialogflow_intent
            print(f"{green_color}contexts/output: {reset_color}{dialogflow_intent}")
            feedback = check_entity_inputs(dialogflow_intent)
            feedback = f'{feedback}'
        else:
            feedback = '(error): É necessário que o contexto "output" seja conduzido até o final. Não foi possível localiza-lo'
            return{
                'fulfillmentText': f'{feedback}'
            }
        
        return {
            'fulfillmentText': feedback
        }


    