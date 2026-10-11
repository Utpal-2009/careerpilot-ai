
from groq import Groq
from src.utils.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def ask_groq(prompt: str, json_mode: bool = False) -> str:
    options = {}

    if json_mode:
        options["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        **options,
    )

    return response.choices[0].message.content or ""
