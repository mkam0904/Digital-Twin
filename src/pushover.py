#### Define Pushover as an LLM Tool and add it to tools list

# Load Pushover API keys from environment 
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"
for e in ('PUSHOVER_USER','PUSHOVER_TOKEN'):
    if e is None: 
        raise Exception(f"ERROR: {e} is None")
    else:
        print(f"{e}: {globals()[e][:4]}")

# Prepare the list of tools for the LLM 
tools_l = list()

# Function to send push notification via Pushover
def send_notification(message: str):
    payload = {"user": PUSHOVER_USER, "token": PUSHOVER_TOKEN,"message":message}
    requests.post(pushover_url, data=payload)

### Define Pushover as an LLM tool 
send_notification_function_d = {
    "name":"send_notification",
    "description":"Send a message to Mamta via Pushover notification.\
        If the user asks to contact Mamta, send her a notification. \
        If you previously asked the user what message to send and the user replies with the message text, call this tool immediately.",
    "parameters":{
        "type": "object",
        "properties": {
            "message": {
                "type":"string",
                "description":"notification message to send to the users device"
            }
        },
        "required":["message"]
    }
}
# Add Pushover tool for the LLM
tools_l.append({"type":"function","function":send_notification_function_d})