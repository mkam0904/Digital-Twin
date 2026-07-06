# Function to simulate a single six sided dice 
def roll_dice():
    return(random.randint(1,6))

# Define dice rolling as an LLM tool 
dice_roll_function_d = {
    "name":"roll_dice",
    "description":"Simulates rolling a single six-sided dice. Use this when the user wants to roll a dice for games, decision or random number generation.",
    "parameters":{
        "type": "object",
        "properties": {},
        "required":[]
    }
}
# Add dice roll tool for the LLM
tools_l.append({"type":"function","function":dice_roll_function_d})


# Function to handle LLM Tool calls 
def handle_tool_calls(tool_calls):
    ### 
    debug_handle_tool_calls = 0 
    msg = ''
    tool_call_results_l = list()
    ###
    for i, tool_call in enumerate(tool_calls):
        ###
        function_name = tool_call.function.name
        # print()
        # print(f"{function_name}")
        if function_name == "send_notification":
            args = json.loads(tool_call.function.arguments)
            send_notification(args["message"])
            content = f"Notification sent: {args['message']}"
        elif function_name == "roll_dice":
            content = f"roll_dice_result: {roll_dice()}"
        else:
            content = f"Unknown function: {function_name}"
        ###        
        tool_call_result_d = {
            "role":"tool",
            "tool_call_id": tool_call.id,
            "content": content
        }
        tool_call_results_l.append(tool_call_result_d)
        if debug_handle_tool_calls: 
            pprint(tool_call_results_l)
    return(tool_call_results_l)