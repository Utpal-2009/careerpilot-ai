
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY or GROQ_API_KEY == "chal hutt tane ni aapa":
    raise ValueError(
        "Please add a valid GROQ_API_KEY in your .env file."
    )
