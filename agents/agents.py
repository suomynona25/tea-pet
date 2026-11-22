import sys
from pathlib import Path

# Ensure root project directory is in sys.path when running agents.py directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import HumanMessage, AIMessage
from tools.google_tool import google_tool
import dotenv

dotenv.load_dotenv()
model = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite')
checkpointer = InMemorySaver()
store = InMemoryStore()


def supervisor_pre_model_hook(state):
    messages = list(state.get("messages", []))
    if messages and isinstance(messages[-1], AIMessage) and not messages[-1].tool_calls:
        # If the last message is an AIMessage from a subagent, append a prompt so Gemini doesn't complain about model prefilling
        llm_msgs = messages + [
            HumanMessage(
                content="The previous agent has provided a response to the user. Respond with no tool calls if finished."
            )
        ]
        return {"llm_input_messages": llm_msgs}
    return {"llm_input_messages": messages}


def create_all_agents():
    #Create tea researcher agent
    tea_researcher = create_agent(
        model = model,
        tools = [google_tool],
        system_prompt=("""You are a research agent.
        INSTRUCTIONS:
        - When provided the tea name, use the google search tool by passing in the tea's name as the search query to try to form a consensus of the optimal tea steeping time and duration
        - If unable to yield a consensus result from the google search, answer using general knowledge and say so clearly.
        - After you're done with your tasks, output your research findings directly in text. Do not attempt to call any transfer tools. 
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
        model=model,
        tools=[],
        system_prompt= ("""
        You are a Chinese tea identification expert. When the user's message includes 
        a photo, examine the leaf shape, color, compression (loose leaf vs. cake/brick), 
        liquor color if visible, and any packaging text (including Chinese characters) 
        to identify the most likely tea name and category (green, oolong, black/red, 
        white, dark/pu-erh, or scented). State your best guess clearly, mention what 
        visual evidence supports it, and flag your confidence level. If there is no
        photo in the conversation, tell the user they can attach one by typing
        "/image <path to photo> [optional question]", or they can describe the tea
        instead. If the photo or description is insufficient, ask investigative
        questions such as "Do you have the packaging?", "What does the unbrewed tea
        look like?", "What do the brewed liquor and leaves look like?", and "What
        does the tea taste like?"
    """),
        name="tea_identifier",
    )

    #Create supervisor agent
    system = create_supervisor(
        [tea_identifier, tea_researcher, tea_sommelier],
        model = model,
        prompt = ("""You are a supervisor managing a team of agents consisting of a tea identifier, tea researcher, and a tea sommelier.
        Tea identifier identifies the name of the tea upon user request, through either images, questions, or a combination of the two.
        Tea researcher is an expert at characteristics of a given tea such as tea steeping parameters.
        Tea sommelier is an expert at the different kinds of teas available that suit the user's preferences. They can guide the user through picking a tea that they like, and provide some background information for the user's enjoyment.
        Assign work to one agent at a time, do not call agents in parallel.
        Do not do any work yourself.
    """),
        add_handoff_back_messages=True,
        output_mode="full_history",
        pre_model_hook=supervisor_pre_model_hook
    )

    app = system.compile(checkpointer=checkpointer, store=store)
    return app


if __name__ == "__main__":
    app = create_all_agents()
    print("Tea Pet agents compiled successfully!")
