from agents.agents import create_all_agents
from langchain_core.messages import AIMessage

config = {"configurable": {"thread_id": "1"}}
app = create_all_agents()


#Print out chat output
#Ask for user reinput
#Add exit condition
print("=== Welcome to Tea Pet! Let's enjoy some tea together. === \n")

while True:
    #Ask for user input
    user_input = input("Ask a question:").strip()
    for chunk in app.stream(
        {"messages": [{'role':"user", 'content': user_input}]},
        config = config,
        stream_mode = 'messages',
        version = 'v2'
    ):
        # Catch only output containing messages
        if chunk['type'] == 'messages':
            # Unpack the data tuple of the message
            msg, meta = chunk['data']
            # Only process AIMessages with actual text (ignore ToolMessage tool outputs and tool call requests)
            if isinstance(msg, AIMessage) and not msg.tool_calls and msg.content:
                # Extract text from string or structured content blocks
                text = ""
                if isinstance(msg.content, str):
                    text = msg.content
                elif isinstance(msg.content, list):
                    text = "".join(
                        b.get("text", "") 
                        for b in msg.content 
                        if isinstance(b, dict) and b.get("type") == "text"
                    )

                # Ignore empty chunks, internal handoff/transfer messages, and tool error messages
                if (
                    text.strip() 
                    and not text.startswith("Transferring") 
                    and not text.startswith("Successfully transferred") 
                    and not text.startswith("Error:")
                ):
                    print(text, end="", flush=True)
    print("\n")

# for chunk, in app.stream(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "Recommend me a tea"
#             }
#         ]
#     },
#     config=config,
#     stream_mode="messages"
# ):
#     # Only print AIMessage objects that contain actual user-facing text
#     if isinstance(chunk, AIMessage) and chunk.content:
#         text = ""
#         if isinstance(chunk.content, str):
#             text = chunk.content
#         elif isinstance(chunk.content, list):
#             text = "".join(
#                 b.get("text", "") for b in chunk.content 
#                 if isinstance(b, dict) and b.get("type") == "text"
#             )
        
#         # Exclude empty content, internal tool calls, and handoff messages
#         if text.strip() and not text.startswith("Transferring"):
#             sender = chunk.name or metadata.get("langgraph_node", "Agent")
#             print(f"\n[{sender}]:\n{text}")
