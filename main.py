from fastapi import FastAPI, Request
from fastapi import HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import json
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def check_text(prompt):
    reponse = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config = genai.types.GenerateContentConfig(
        temperature=0.1
    )
    )
    return reponse.text


def generate_prompt(text):
    return f"""
    You are the content moderator and you decide if the content in the input text has anything
    harmful, derogatory, or such negative sense in it which could effect people reading it negatively.This is considered toxic
    Positive criticism must not be flagged negative.

    input: {text}
        Only output a valid JSON with the **exact** following format:
    {{
    "toxic": true or false,
    "comments": "brief explanation why or why not"
    }}

    """

def parse_output(response):
    logger.info(response)
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    logger.info(json_match)
    output_parsed = json.loads(json_match.group())
    return TextResponse(**output_parsed)
    if not json_match:
            return HTTPException(status_code=500, detail="Could not extract JSON from LLM response")


class TextResponse(BaseModel):
    toxic: bool
    comments: str

class TextRequest(BaseModel):
    text: str
    userId: str



app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.post("/checkContent/text")
def check_text_content(request:TextRequest):
    text = request.text
    logger.info("hello in the py api")
    logger.info(text)

    prompt = generate_prompt(text)
    output = check_text(prompt)
    try:
        print(parse_output(output))
        logger.info(parse_output(output))
        return parse_output(output)        
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
