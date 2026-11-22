import base64
import mimetypes
import shlex
from pathlib import Path

from agents.agents import create_all_agents
from langchain_core.messages import AIMessage

config = {"configurable": {"thread_id": "1"}}
app = create_all_agents()

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DEFAULT_IMAGE_QUESTION = "Please identify this tea."


def build_user_message(user_input):
    """Build the user message. '/image <path> [question]' attaches a photo.

    Returns (message, error). Exactly one of them is None.
    """
    if not user_input.startswith("/image"):
        return {"role": "user", "content": user_input}, None

    # posix=False keeps Windows backslashes intact; quotes allow paths with spaces
    try:
        parts = shlex.split(user_input[len("/image"):], posix=False)
    except ValueError as e:
        return None, f"Could not parse the command: {e}"
    if not parts:
        return None, "Usage: /image <path to photo> [your question]"

    path = Path(parts[0].strip('"\''))
    question = " ".join(parts[1:]) or DEFAULT_IMAGE_QUESTION

    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type not in SUPPORTED_IMAGE_TYPES:
        return None, "Unsupported image type. Use a .jpg, .png or .webp file."
    try:
        image_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError as e:
        return None, f"Could not read image: {e}"

    return {
        "role": "user",
        "content": [
            {"type": "text", "text": question},
            {"type": "image", "base64": image_b64, "mime_type": mime_type},
        ],
    }, None


print("=== Welcome to Tea Pet! Let's enjoy some tea together. ===")
print("Tip: attach a tea photo with /image <path> [your question]\n")

while True:
    #Ask for user input
    user_input = input("Ask a question:").strip()
    if not user_input:
        continue
    message, error = build_user_message(user_input)
    if error:
        print(error + "\n")
        continue

    for chunk in app.stream(
        {"messages": [message]},
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
