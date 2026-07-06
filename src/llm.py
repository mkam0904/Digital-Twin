


# Call the large language model
def call_llm(msgs):
    print("call_llm")
    debug_call_llm = 0
    response = client.chat.completions.create(
        model = "gpt-4.1-mini",
        messages = msgs,
        tools = tools_l
    )
    if debug_call_llm:
        pprint(response.model_dump())
    return(response)

