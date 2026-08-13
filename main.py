from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from tools.google_tool import google_tool
import dotenv
import os

dotenv.load_dotenv()
model = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite')
checkpointer = InMemorySaver()
store = InMemoryStore()

# response = model.invoke('i am testing out my code. what is your model?')
# print(response)

#Create tea researcher agent
tea_researcher = create_agent(
    model = model,
    tools = [google_tool],
    system_prompt=("""You are a research agent.
    INSTRUCTIONS:
    - When provided the tea name, use the google search tool by passing in the tea's name as the search query to try to form a consensus of the optimal tea steeping time and duration
    - If unable to yield a consensus result from the google search, answer using general knowledge and say so clearly.
    - After you're done with your tasks, respond to the supervisor directly.
    - Respond only with the results of your work, do not include any other text. 
"""),
    name = 'tea_researcher'
)

#Create tea sommelier agent
tea_sommelier = create_agent(
    model = model,
    tools = [google_tool],
    system_prompt = ("""You are a creative agent that is also capable of performing research.
    INSTRUCTIONS:
    - When user asks for tea recommendations, ask them some preliminary questions about their mood, and the kind of flavour they are looking for 
    - Once the user provides their preferences, use your general knowledge to come up with 3 teas to recommend to the user and ask them to pick one
    - Once the user picks a tea, use the google search tool to search for the history and flavour profile of the chosen tea
    - Recommend 3 food that pairs well with the chosen tea
    - If you are unable to yield results from the google search, answer using your general knowledge.  
"""),
    name = 'tea_sommelier'
)

#Create tea identifier agent
tea_identifier = create_agent(
    model = model,
    tools = [google_tool],
    system_prompt = ("""You are a tea identification expert that identifies teas based on provided pictures.
    INSTRUCTIONS:
    - When user asks for assistance for tea identification, ask them to submit a photo, or if they wish to identify verbally
    - If the picture is insufficient for tea identification, ask necessary investigative questions including "do you have the packaging?", "What does the unbrewed tea look like?", "What does the brewed tea liquor and leaves look like?", "What does the tea taste like?"
    - Use your general knowledge first to try to identify the tea. If the result is uncertain, use the google tool to search the internet using textual clues you have gained so far
    - Finally answer the user the name of the tea you have identified and explain a summary of your justifications
"""),
    name = 'tea_identifier'
)

#Create supervisor agent
system = create_supervisor(
    [tea_identifier, tea_researcher, tea_sommelier],
    model = model,
    prompt = ("""You are a supervisor managing a team of agents consisting of a tea identifier, tea researcher, and a tea sommelier.
    Tea identifier identifies the name of the tea upon user request, through either images, questions, or a combination of the two. They are also able to perform google search for this purpose.
    Tea researcher is an expert at characteristics of a given tea such as tea steeping parameters.
    Tea sommelier is an expert at the different kinds of teas available that suit the user's preferences. They can guide the user through picking a tea that they like, and provide some background information for the user's enjoyment.
    Assign work to one agent at a time, do not call agents in parallel.
    Do not do any work yourself.
"""),
    add_handoff_back_messages=True,
    output_mode="full_history"
)

app = system.compile(checkpointer=checkpointer, store=store)

config = {"configurable": {"thread_id": "1", "user_id": "1"}}

# Use stream_mode="messages" to receive individual message events
for chunk, metadata in app.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "Recommend me a tea"
            }
        ]
    },
    config=config,
    stream_mode="messages"
):
    # Only print AIMessage objects that contain actual user-facing text
    if isinstance(chunk, AIMessage) and chunk.content:
        text = ""
        if isinstance(chunk.content, str):
            text = chunk.content
        elif isinstance(chunk.content, list):
            text = "".join(
                b.get("text", "") for b in chunk.content 
                if isinstance(b, dict) and b.get("type") == "text"
            )
        
        # Exclude empty content, internal tool calls, and handoff messages
        if text.strip() and not text.startswith("Transferring"):
            sender = chunk.name or metadata.get("langgraph_node", "Agent")
            print(f"\n[{sender}]:\n{text}")