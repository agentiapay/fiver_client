from fastapi import FastAPI
from agents import Agent,Runner,AsyncOpenAI,OpenAIChatCompletionsModel,set_tracing_disabled
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
set_tracing_disabled(True)

# api key setup
client = AsyncOpenAI(api_key="AIzaSyCMpBWF-tOzuVQ9inIyVlPo7VFCJ6b9dd0",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                     )
model = OpenAIChatCompletionsModel(openai_client=client,model="gemini-2.5-flash")

# base model class
class UserPrompt(BaseModel):
    prompt:str

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
    return {"Status":"Done"}

@app.post("/chatbot")
async def chatbot(data:UserPrompt):
    # importing modules
# set api key

    general_purpose_agent = Agent(name="general_purpose_agent",
      instructions="""
      You are a general-purpose AI assistant. Your goal is to provide helpful, informative,
      and detailed responses to any question asked, on any topic.you can add emogies and markdown style to the response if needed.


      """, model=model
    )

    result = await Runner.run(general_purpose_agent, data.prompt)
    response = result.final_output
    print(response)
    return {"response":response}
