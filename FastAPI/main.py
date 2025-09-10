from fastapi import FastAPI
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
# import uuid
set_tracing_disabled(True)

# =======================
# MongoDB Connection
# =======================
MONGO_URL = "mongodb+srv://freeskills:NajafAli5$@cluster0.8mlufak.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client_db = AsyncIOMotorClient(MONGO_URL)
db = client_db["chat_db"]                 # Database name 
collection = db["conversations"]          # Collection name

# =======================
# API Key + Model Setup
# =======================
client = AsyncOpenAI(
    api_key="AIzaSyCMpBWF-tOzuVQ9inIyVlPo7VFCJ6b9dd0",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
model = OpenAIChatCompletionsModel(openai_client=client, model="gemini-2.5-flash")

# =======================
# Pydantic Base Model
# =======================
class UserPrompt(BaseModel):
    conversation_id: str
    prompt: str

# =======================
# FastAPI App Setup
# =======================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"Status": "Done"}

# =======================
# Chatbot Endpoint
# =======================
@app.post("/chatbot")
async def chatbot(data: UserPrompt):
    # ---- 1. Fetch old conversation history ----
    # conversation_id = str(uuid.uuid4())
    history_doc = await collection.find_one({"conversation_id": data.conversation_id})
    history_text = ""
    if history_doc:
        for msg in history_doc["messages"]:
            role = msg["sender"]
            text = msg["text"]
            history_text += f"{role}: {text}\n"

    # ---- 2. Prepare Agent with history ----
    general_purpose_agent = Agent(
        name="general_purpose_agent",
        instructions=f"""
        You are a general-purpose AI assistant.
        Always respond in **Markdown format** with clear structure.

        Conversation so far:
        {history_text}

        Now continue the conversation. 
        - Use headings (###) for sections if needed.
        - Use **bold** and *italic* for emphasis.
        - Add bullet points or numbered lists for clarity.
        - Use code blocks (```language) for code examples.
        - You may also add emojis 🎉🔥💡 to make responses engaging.
        """,
        model=model
    )

    # ---- 3. Run Agent ----
    result = await Runner.run(general_purpose_agent, data.prompt)
    response = result.final_output

    # ---- 4. Save user + bot message into MongoDB ----
    new_messages = [
        {"sender": "user", "text": data.prompt, "timestamp": datetime.utcnow()},
        {"sender": "bot", "text": response, "timestamp": datetime.utcnow()}
    ]

    if history_doc:
        await collection.update_one(
            {"conversation_id": data.conversation_id},
            {"$push": {"messages": {"$each": new_messages}}}
        )
    else:
        new_convo = {
            "conversation_id": data.conversation_id,
            "messages": new_messages
        }
        await collection.insert_one(new_convo)
    print(history_text)

    return {"response": response}
