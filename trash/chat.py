# src/chat.py
from config import client
from prompts import system_message
from llm import call_llm
from tools import handle_tool_calls

def respond_ai(message, history, collection):
    max_toolcalls_allowed = 3
    count = 0

    response = client.embeddings.create(model="text-embedding-3-small", input=[message])
    query_embeddings = [item.embedding for item in response.data]

    n_results = 3
    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    all_rows = collection.get(include=["documents", "metadatas"])

    context_blocks = []
    for i in range(n_results):
        ix = results["metadatas"][0][i]["chunk_index"]
        wanted = {ix - 1, ix, ix + 1}
        pairs = [
            (meta["chunk_index"], doc)
            for meta, doc in zip(all_rows["metadatas"], all_rows["documents"])
            if meta["chunk_index"] in wanted
        ]
        pairs = sorted(pairs, key=lambda x: x[0])
        context_blocks.append("\n\n".join(d for _, d in pairs))

    system_enhanced_msg = system_message + "\n\nContext:\n" + "\n\n---\n\n".join(context_blocks)

    msgs = [{"role": "system", "content": system_enhanced_msg}] + history + [{"role": "user", "content": message}]

    response = call_llm(msgs)
    assistant_msg = response.choices[0].message

    while assistant_msg.tool_calls:
        if count >= max_toolcalls_allowed:
            break
        count += 1
        msgs_from_tools = handle_tool_calls(assistant_msg.tool_calls)
        msgs.append(assistant_msg)
        msgs.extend(msgs_from_tools)
        response = call_llm(msgs)
        assistant_msg = response.choices[0].message

    return assistant_msg.content or "No text response returned."