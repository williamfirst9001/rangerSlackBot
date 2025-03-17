import os
import requests
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from datetime import datetime

app = Flask(__name__)

# Load Slack & TBA API keys
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
TBA_API_KEY = os.getenv("TBA_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Replace with your Slack channel ID

slack_client = WebClient(token=SLACK_BOT_TOKEN)


@app.route("/slack", methods=["POST"])

#@app.route("/")
def slack_command():
    """Handles Slack commands and posts to a channel"""
    data = request.form
    team = data.get("text")  # Get input from command
    
    if not team:
        return jsonify({"response_type": "ephemeral", "text": "Usage: `/tba event_key`"})
    
    team = int(team)

    
    HEADERS = {"X-TBA-Auth-Key": TBA_API_KEY}

    events = f"https://www.thebluealliance.com/api/v3/team/frc{team}/events/2025"



    url = f"https://www.thebluealliance.com/api/v3/team/frc{team}/matches/2025"
    # Make the request
    response = requests.get(url, headers=HEADERS)

    event_response = requests.get(events,headers=HEADERS)

    event_names = []

    if response.status_code == 200:
        event_data = event_response.json()
        data = response.json()
        #print(True)


    team_opr = []
    event_opr = []

    team_dpr = []
    team_ccwm = []





    team_auto_scored = [] # per match
    event_auto_average_scored = [] #per match

    message = ""


    #for i in data:
        #if f"frc{team}" in i["alliances"]["red"]["team_keys"]:
            #print("red",i["match_number"])
        #else:
            #print("blue",i["match_number"])
        #print(i["alliances"]["red"])

    for x in event_data:
        #print(x["end_date"])
        end_date = datetime.strptime(x["end_date"], "%Y-%m-%d")

    #print(datetime.today(),end_date)

        if datetime.today() > end_date:
            #print(f"The event {x['name']} has already happened.")
            #print(x["first_event_code"])

            opr_url = f"https://www.thebluealliance.com/api/v3/event/2025{x['first_event_code']}/oprs"

            opr_response = requests.get(opr_url,headers=HEADERS)

            opr_data = opr_response.json()
            team_opr.append(opr_data["oprs"][f"frc{team}"])

            team_dpr.append(opr_data["dprs"][f"frc{team}"])
            team_ccwm.append(opr_data["ccwms"][f"frc{team}"])
            
            message += f"At {x['name']} team {team} had an OPR of {round(opr_data['oprs'][f'frc{team}'])}"
            message += f" a DPR of {round(opr_data['dprs'][f'frc{team}'])}"
            message += f" and a CCWM of {round(opr_data['ccwms'][f'frc{team}'])} \n"



        average_opr = sum(team_opr)/len(team_opr)
        average_dpr = sum(team_dpr)/len(team_dpr)
        average_ccwm = sum(team_ccwm)/len(team_ccwm)
        message += f"Team {team} has an average OPR of {round(average_opr)} \n"
        message += f"Team {team} has an average DPR of {round(average_dpr)} \n"
        message += f"Team {team} has an average CCWM of {round(average_ccwm)} \n"

        # Post message to a specific channel
        #slack_client.chat_postMessage(channel=CHANNEL_ID, text=message)

    return jsonify({"text": message})

if __name__ == "__main__":
    app.run(port=3000)
