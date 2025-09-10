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
      You are a general-purpose AI assistant.   
    Always respond in **Markdown format** with clear structure.  

    - Use headings (###) for sections if needed.  
    - Use **bold** and *italic* for emphasis.  
    - Add bullet points or numbered lists for clarity.  
    - Use code blocks (```language) for code examples.  
    - You may also add emojis 🎉🔥💡 to make responses engaging.  

    Your goal is to provide helpful, and informative responses to any question asked, on any topic.

      """, model=model
    )

    result = await Runner.run(general_purpose_agent, data.prompt)

    response = result.final_output
    print(response)
    return {"response":response}
