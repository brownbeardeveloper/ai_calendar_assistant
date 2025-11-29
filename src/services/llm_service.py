from openai import OpenAI
from datetime import datetime
import json, os, dotenv

dotenv.load_dotenv()

class LLMService:
    """
    LLM service to parse user messages and generate responses.

    Attributes:
        client (OpenAI): The OpenAI client to use for generating responses.
        model_name (str): The name of the model to use for generating responses.
        system_prompt (str): The system prompt to use for generating responses.
    """
    def __init__(self, model_name="gpt-4o-mini") -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name
        self.system_prompt = "Extract intent and entities. Return JSON."

    def parse_intent(self, message: str, current_datetime: datetime = None, history=None) -> dict:
        
        if current_datetime is None:
            current_datetime = datetime.now()

        if history is None:
            history = []

        msgs = [{"role": "system", "content": self.system_prompt}]

        for item in history:
            msgs.append({"role": item["role"], "content": item["content"]})

        msgs.append({"role": "user", "content": message})

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=msgs,
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content
        return json.loads(content)
