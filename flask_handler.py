from flask import Flask, request
import switch
import json

app = Flask("app")

@app.route('/', methods=['POST'])
def handler():
    try:
        event = request.get_json()
        plan = switch.switch(event["email"], event["password"], event["plan"])
        return "Switched to " + plan.upper() + " plan (effect tomorrow)"
    except Exception as e: 
        print(e)
        return "Switch plan failed"

