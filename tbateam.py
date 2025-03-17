import os
import requests
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from datetime import datetime

import statbotics



app = Flask(__name__)

# Load Slack & TBA API keys
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
TBA_API_KEY = os.getenv("TBA_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Replace with your Slack channel ID

slack_client = WebClient(token=SLACK_BOT_TOKEN)






@app.route("/stbmatchpred",methods=["POST"])
def stbmatchpred():
    sb = statbotics.Statbotics()
    text = request.form.get('text', '')  # Get the text after /command
    args = text.split()  # Split into arguments based on spaces
    
    if len(args) < 2:
        return jsonify({"response_type": "ephemeral", "text": "Please provide at least two arguments."})

    match_num = args[0].strip()
    event_code = args[1].strip()

    data = sb.get_match(f"{event_code}_qm{match_num}")["pred"]
    message = ""


    message += f"Red win probability is {data['red_win_prob']*100}. Blue win probability is {100-data['red_win_prob']*100}\n"

    message += f"Red expected score is {data['red_score']}. Blue expected score is {data['blue_score']}"

    return jsonify({"text": message})






@app.route("/tbateamevent",methods=["POST"])
def tbateamevent():
    HEADERS = {"X-TBA-Auth-Key": TBA_API_KEY}
    def mean(val):
        return round(sum(val)/len(val))
    text = request.form.get('text', '')  # Get the text after /command
    args = text.split()  # Split into arguments based on spaces
    
    if len(args) < 2:
        return jsonify({"response_type": "ephemeral", "text": "Please provide at least two arguments."})

    team = args[0].strip()
    event_code = args[1].strip()

    team_key = f"frc{team}"
    
    print(event_code)

    url = f"https://www.thebluealliance.com/api/v3/event/{event_code}/matches"


    
    # Make the request
    response = requests.get(url, headers=HEADERS)



    if response.status_code == 200:
        data = response.json()


        #print(True)


    team_auto_scored = [] # per match
    event_auto_scored = [] #per match

    team_tele_scored = []
    event_tele_scored = []


    #print(sb.get_match(f"{event_code}_qm1")["pred"])
    message = ""


    for x in data:
        
        event_auto_scored.append(x["score_breakdown"]["blue"]["autoPoints"]+x["score_breakdown"]["red"]["autoPoints"])
        event_tele_scored.append(x["score_breakdown"]["blue"]["teleopPoints"]+x["score_breakdown"]["red"]["teleopPoints"])

        if(team_key in x["alliances"]["red"]["team_keys"]):
            team_auto_scored.append(x["score_breakdown"]["red"]["autoPoints"])
            team_tele_scored.append(x["score_breakdown"]["red"]["teleopPoints"])
        elif (team_key in x["alliances"]["blue"]["team_keys"]):
            team_auto_scored.append(x["score_breakdown"]["blue"]["autoPoints"])
            team_tele_scored.append(x["score_breakdown"]["blue"]["teleopPoints"])


    message += f"{event_code} mean auto points {mean(event_auto_scored)/2} \n"
    message += f"{event_code} mean teleop points {mean(event_tele_scored)/2} \n"
    message += f"{team} mean alliance auto points {mean(team_auto_scored)} \n"
    message += f"{team} mean alliance tele points {mean(team_tele_scored)} \n"

    message += f"{team}'s average auto score is {'above' if mean(event_auto_scored)/2-mean(team_auto_scored)<0 else 'below'} average by {abs(mean(event_auto_scored)/2-mean(team_auto_scored))} \n"
    message += f"{team}'s average tele score is {'above' if mean(event_tele_scored)/2-mean(team_tele_scored)<0 else 'below'} average by {abs(mean(event_tele_scored)/2-mean(team_tele_scored))} \n"



    return jsonify({"text": message})



@app.route("/help",methods =["POST"])
def help():
    message = ""

    message +="/tbateam ---[team #] --- gives the OPR, DPR and CCWM of any team at all events they have attended \n"
    message +="/tbateamevent ---[team # | event code] --- gives the OPR, DPR and CCWM of any team at all events they have attended \n"
    message +="/stbmatchpred ---[match # | event code] --- gives the win probabilities and expected score of a match"

    return jsonify({"text": message})



@app.route("/tbateam", methods=["POST"])
def tbateam():
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


        # Post message to a specific channel
        #slack_client.chat_postMessage(channel=CHANNEL_ID, text=message)

    return jsonify({"text": message})

if __name__ == "__main__":
    app.run(port=3000)
