import os
from openai import OpenAI
import json
import dotenv

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
        self.system_prompt = (
            "Extract intent and entities. Return JSON:\n"
            "{intent: string, entities: object}"
        )

    def parse_intent(self, message: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
