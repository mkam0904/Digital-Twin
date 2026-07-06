# respond_ai: gradio interface function: Run the LLM and handle tool calls
def respond_ai(message, history):

    # variable declaration
    debug_rag = 0 
    max_toolcalls_allowed = 3
    count = 0
    system_enhanced_msg = system_message

    add_dynamic_context = 0
    if add_dynamic_context:
        for k_set, v in Topic_Context.items():
            for k in k_set:
                if k in message.lower():
                    system_enhanced_msg +=  '\n' + v

    msgs = [{"role": "system","content": system_enhanced_msg}] \
            + history \
            + [{"role": "user","content": message}]

    add_rag = 1 
    if add_rag:
        
        # Generate embedding for a message
        test_query = message

        #####
        # RAG: Embed the query (using the same model we used for the chunks to ensure compatibility)
        # note: response.data = [{"embedding":[0.012,...],"index":0,"object":"embedding"
        response = client.embeddings.create( 
            model = "text-embedding-3-small",
            input = [test_query]
        )
        query_embeddings = [item.embedding for item in response.data]
        
        if debug_rag: 
            print(type(query_embeddings),len(query_embeddings))
            print(response.model_dump().keys())
            # note: dict_keys(['data', 'model', 'object', 'usage'])

        # RAG: Search ChromaDB
            # summary:
            # query() = semantic/vector search = [query][match]
            # get()   = exact fetch/metadata filter = [row]
            # query()["documents"][q][k]
            # get()["documents"][i]
        
        # note: query results: {"ids":[[...]],"documents":[[...]],"metadatas":[[{"source":<>,"chunk_index":<>}]],"distances":[[...]]
        n_results = 3 
        results = collection.query(
            query_embeddings = query_embeddings, # OR query_texts=[...]
            n_results = n_results,
            include=["documents","metadatas","distances"]
        )
        all_rows = collection.get(
                        include=["documents","metadatas"]
                    )
        context_blocks = []
        for i in range(n_results):
            ix = results["metadatas"][0][i]["chunk_index"]
            wanted = {ix-1, ix, ix+1}
            pairs = [
                (meta["chunk_index"], doc)
                for meta, doc in zip(all_rows["metadatas"], all_rows["documents"])
                if meta["chunk_index"] in wanted
            ]
            pairs = sorted(pairs, key=lambda x: x[0])
            context_blocks.append("\n\n".join(d for _, d in pairs)) 
        system_enhanced_msg += "\n\nContext:\n" + "\n\n---\n\n".join(context_blocks)

        if debug_rag: 
            print(f"Retrived Chunks: ")
            # metadatas: source, chunk_index
            for a,b,c in zip(results["documents"][0],results["metadatas"][0],results["distances"][0]):
                print(f"Chunk {b['chunk_index']}: distance:{round(c,2)}\n\t{a}")
                print()      
            print("system_enhanced_msg: ", system_enhanced_msg)

    # Build messages for this turn 
    msgs = [{"role": "system","content": system_enhanced_msg}] + \
           history + \
           [{"role": "user","content": message}]

    # Call the llm 
    response = call_llm(msgs)
    assistant_msg = response.choices[0].message

    # Check if model wants to call a tool 
    while assistant_msg.tool_calls:
        print('tool_calling')
        # protection from infinite consecutive tool calling 
        if count >= max_toolcalls_allowed:
            break
        count += 1  
        # handle tool calls 
        msgs_fromtool_l = handle_tool_calls(assistant_msg.tool_calls)
        msgs.append(assistant_msg)
        msgs.extend(msgs_fromtool_l)
        response = call_llm(msgs)
        assistant_msg = response.choices[0].message
    print('all done')

    if assistant_msg.content:
        return(assistant_msg.content)
    else:
        return "No text response returned."