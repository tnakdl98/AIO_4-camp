
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

response = client.responses.create(
    input="한복의 유래는 어디서 ? 한국? 중국?",
    model="openai/gpt-oss-20b",
)
print(response.output_text)