# code with voice
from fastapi import FastAPI
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional
from fastapi.responses import StreamingResponse
import os, json, io
from google.cloud import texttospeech


set_tracing_disabled(True)

# ======================= 
# MongoDB Connection
# =======================
MONGO_URL = "your mango ur"
client_db = AsyncIOMotorClient(MONGO_URL)
db = client_db["chat_db"]
collection = db["conversations"]

# =======================
# API Key + Model Setup
# =======================
client = AsyncOpenAI(
    api_key="your api key",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
model = OpenAIChatCompletionsModel(openai_client=client, model="gemini-2.5-flash")

# =======================
# Pydantic Models
# =======================
class UserPrompt(BaseModel):
    conversation_id: str
    prompt: str

class UserVoice(BaseModel):
    conversation_id: str
    voice: str

# =======================
# Cardiovascular Questions Data
# =======================
Cardio_Questions = """
Cardiovascular Assessment Questions:
1. Chest Pain - Have you had any pain or pressure in your chest, neck, or arm?  
...
"""

# =======================
# FastAPI Setup
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
# Shared Agent Creator
# =======================
def get_doctor_agent(history_text: str):
    return Agent(
        name="Cardiovascular_Assessment_Questions",
        instructions=f"""
You are a **virtual doctor AI assistant**.  
Your role is to conduct a structured **cardiovascular interview**.

Conversation so far:  
{history_text}  

The only source of truth is this variable: '{Cardio_Questions}'.  
- Strictly ask questions from this variable only.  
- Do not provide answers yourself.  
- Ask **one question at a time** in a conversational doctor style.  
- Use follow-up questions if they exist.  
- When all questions finish, summarize answers and give **doctor-style suggestions**.  

Respond in English, Kannada, or Tamil (detect user language).  
For voice endpoint, keep answers short and speech-friendly.  

Format for `/chatbot`: **Markdown** with headings, bold, bullets.  
Format for `/voice`: plain speech-friendly text (no markdown).  
""",
        model=model
    )

# =======================
# Chatbot (Text)
# =======================
@app.post("/chatbot")
async def chatbot(data: UserPrompt):
    # fetch history
    history_doc = await collection.find_one({"conversation_id": data.conversation_id})
    history_text = ""
    if history_doc:
        for msg in history_doc["messages"]:
            history_text += f"{msg['sender']}: {msg['text']}\n"

    agent = get_doctor_agent(history_text)
    result = await Runner.run(agent, data.prompt)
    response = result.final_output

    # save in DB
    new_messages = [
        {"sender": "user", "text": data.prompt, "timestamp": datetime.utcnow()},
        {"sender": "bot", "text": response, "timestamp": datetime.utcnow()},
    ]
    if history_doc:
        await collection.update_one({"conversation_id": data.conversation_id}, {"$push": {"messages": {"$each": new_messages}}})
    else:
        await collection.insert_one({"conversation_id": data.conversation_id, "messages": new_messages})

    return {"response": response}


# =======================
# Voice Endpoint
# =======================

@app.post("/voice")
async def voice_chat(data: UserVoice):
    # fetch history
    history_doc = await collection.find_one({"conversation_id": data.conversation_id})
    history_text = ""
    if history_doc:
        for msg in history_doc["messages"]:
            history_text += f"{msg['sender']}: {msg['text']}\n"

    agent = get_doctor_agent(history_text)
    result = await Runner.run(agent, data.voice)

    # plain spoken style
    response = result.final_output.replace("**", "").replace("*", "")

    # save in DB
    new_messages = [
        {"sender": "user", "text": data.voice, "timestamp": datetime.utcnow()},
        {"sender": "bot", "text": response, "timestamp": datetime.utcnow()},
    ]
    if history_doc:
        await collection.update_one(
            {"conversation_id": data.conversation_id},
            {"$push": {"messages": {"$each": new_messages}}},
        )
    else:
        await collection.insert_one(
            {"conversation_id": data.conversation_id, "messages": new_messages}
        )

    # =======================
    # 🔊 Generate TTS Audio
    # =======================
    # 👇 Load credentials from local file
    d = open("GOOGLE_TTS_CREDENTIALS.json", "r")
    GOOGLE_TTS_CREDENTIALS = json.load(d) 
    client = texttospeech.TextToSpeechClient.from_service_account_info(GOOGLE_TTS_CREDENTIALS)

    synthesis_input = texttospeech.SynthesisInput(text=response)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-IN",
        name="en-IN-Wavenet-C",  # ✅ Indian English human-like voice
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    tts_response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Send audio as streaming response
    audio_bytes = io.BytesIO(tts_response.audio_content)
    return StreamingResponse(audio_bytes, media_type="audio/mpeg")
