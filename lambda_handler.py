import switch
import json

def handler(event, context):
    try:
        if "body" in event:
            event = json.loads(event["body"])

        plan = switch.switch(event["email"], event["password"], event["plan"])
        return "Switched to " + plan.upper() + " plan (effect tomorrow)"
    except Exception as e: 
        print(e)
        return "Switch plan failed"