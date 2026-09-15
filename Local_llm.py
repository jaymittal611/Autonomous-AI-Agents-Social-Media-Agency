import json
import time
from typing import Type, TypeVar
import requests
from pydantic import BaseModel,  ValidationError


T = TypeVar("T", bound=BaseModel)


class OllamaStructured:
    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.url = f"{base_url}/api/chat"

    def ask(
        self,
        system_prompt: str,
        user_prompt: str,
        output_model: Type[T],
        retries: int = 3,
    ) -> T:

        schema = output_model.model_json_schema()

        messages = [
            {
                "role": "system",
                "content": (
                    f"{system_prompt}\n\n"
                    "Reply with JSON only. No Markdown, explanations, or code fences.\n"
                    f"Your JSON must match this schema:\n{json.dumps(schema)}"
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": schema,  
            "options": {"temperature": 0.2},
        }

        last_error = None

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(self.url, json=payload, timeout=120)
                response.raise_for_status()

                content = response.json()["message"]["content"]

                # Validates both JSON syntax and required Pydantic fields.
                return output_model.model_validate_json(content)

            except (
                requests.RequestException,
                KeyError,
                ValidationError,
                json.JSONDecodeError,
            ) as error:
                last_error = error
                print(f"Attempt {attempt}/{retries} failed: {error}")

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous answer was invalid. "
                            "Return only valid JSON matching the schema."
                        ),
                    }
                )
                time.sleep(1)

        raise RuntimeError(
            f"Ollama could not produce valid {output_model.__name__} after "
            f"{retries} attempts."
        ) from last_error
