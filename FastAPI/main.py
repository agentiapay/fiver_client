from fastapi import FastAPI
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime


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

    Cardiovascular_Assessment_Questions = """
Cardiovascular Assessment Questions:

1. Chest Pain  
- Have you had any pain or pressure in your chest, neck, or arm?  
Follow-Up:  
• Provocation/Palliation – What brings on the pain? What relieves it?  
• Quality/Quantity – What are the characteristics and duration?  
• Region/Radiation – Where is the pain? Does it radiate anywhere?  
• Severity – How would you rate the pain (0–10)?  
• Timing – When did it start? How long does it last? What relieves it?  
• Understanding – What do you think is causing the pain?  

2. Shortness of Breath (Dyspnea)  
- Do you ever feel short of breath with activity?  
- Do you ever feel short of breath while sleeping?  
- Do you feel short of breath when lying flat?  
Follow-Up:  
• What level of activity brings it on?  
• How long does it take you to recover?  
• Have you ever woken up suddenly short of breath (paroxysmal nocturnal dyspnea)?  
• How many pillows do you need to sleep, or do you sleep in a chair (orthopnea)? Has this recently changed?  

3. Edema  
- Have you noticed swelling of your feet or ankles?  
- Do rings, shoes, or clothing feel tight at the end of the day?  
- Any unexplained, sudden weight gain?  
- Any new abdominal fullness?  
Follow-Up:  
• Has the swelling gotten worse?  
• Does elevating your feet relieve it?  
• How much weight have you gained, and over what time?  

4. Palpitations  
- Have you ever felt your heart racing or fluttering in your chest?  
- Have you ever felt like your heart skips a beat?  
Follow-Up:  
• Are you experiencing palpitations now?  
• When did they start?  
• Have you been treated before? What treatment did you receive?  

5. Dizziness (Syncope)  
- Do you ever feel lightheaded?  
- Do you ever feel dizzy?  
- Have you ever fainted?  
Follow-Up:  
• Can you describe what happened?  
• Did you have any warning signs?  
• Did this occur with position change?  

6. Poor Peripheral Circulation  
- Do your hands or feet feel cold or look pale/blue?  
- Do you have pain in your feet or lower legs when exercising?  
Follow-Up:  
• What brings on these symptoms?  
• How much activity causes the pain?  
• Does rest relieve it?  

7. Calf Pain  
- Do you currently have constant pain in your lower legs?  
Follow-Up:  
• Can you point to the area of pain with one finger?  

    """
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
    Cardiovascular_Assessment_Questions = Agent(
        name="Cardiovascular_Assessment_Questions",
        instructions=f"""
        You are a **virtual doctor AI assistant**.  
Your role is to conduct a structured **cardiovascular and peripheral vascular interview**.  

Conversation so far:  
{history_text}  

The only source of truth is this variable: '{Cardiovascular_Assessment_Questions}'.  
- You must strictly ask questions from this variable only.  
- Do not generate questions outside of this variable.  
- Do not provide answers yourself.  
- Ask **one question at a time** in a conversational, doctor-patient manner.  
- Use follow-up questions if they exist in the variable.  
- Wait for the user’s response before moving to the next question.  
- When all questions are finished, summarize the answers and give **doctor-style suggestions**.  

## Response Style:  
- Format output in **Markdown**.  
- Use **headings (###)** where helpful.  
- Highlight key terms with **bold** and *italic*.  
- Use bullet points for clarity.  
- Add emojis 🎉🔥💡 to make responses engaging.  
- Always append *(From the provided Cardiovascular_Assessment_Questions data)* in relevant questions.  

Now begin the interview by asking the **first question from Cardiovascular_Assessment_Questions**.  

        """,
        model=model
    )

    # ---- 3. Run Agent ----
    result = await Runner.run(Cardiovascular_Assessment_Questions, data.prompt)
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
