import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from promptVariables import *
import httpx
import traceback
import json
from typing import List, Optional, Dict, Any, Literal, TypedDict


api_url = "https://api.groq.com/openai/v1/chat/completions"
api_key = ""
model = "llama-3.3-70b-versatile"
streaming = False
faq_intents = ""


class ChatMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str


def build_payload(
    model: str,
    prompt: str,
    user_message: str,
    small_talk_history: Optional[List[ChatMessage]],
    streaming: bool,
    system_prompt: str
) -> Dict[str, Any]:
    messages: List[ChatMessage] = [{"role": "system", "content": f"{system_prompt}\n{prompt}"}]

    if small_talk_history:
        messages.extend(small_talk_history)

    messages.append({"role": "user", "content": json.dumps(user_message)})

    return {
        "model": model,
        "temperature": 1,
        "max_completion_tokens": 1024,
        "top_p": 1,
        "stream": streaming,
        "response_format": {
            "type": "json_object"
        },
        "stop": None,
        "messages": messages
    }


async def get_completion_without_phenomes(
    model: str,
    prompt: str,
    user_message: str,
    small_talk_history: Optional[List[ChatMessage]],
) -> str:
    
    try:
        payload = build_payload(model, prompt, user_message, small_talk_history, streaming=False, system_prompt=systemPrompt)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(api_url, headers=headers, json=payload)
                print("done")

                if response.status_code != 200:
                    print(f"Unexpected response code: {response.status_code}")
                    print(f"Unexpected error response: {response.text}")
                    return f"Error: {response.reason_phrase}"

                response_data = response.json()

                content = (
                    response_data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                )

                print("response content")
                print(content)

                return content or "No valid response found"

            except Exception as e:
                print("Exception occurred:")
                traceback.print_exc()
                return f"Error: {str(e)}"
    except Exception as e:
        print(e)


async def build_faq_prompt(
    user_transcript: str,
    full_transcription: Optional[str],
    small_talk_history: Optional[List[dict]],
) -> str:
    # Build FAQ intent entries into prompt format
    intent_entries = "\n".join(
        f'- **{intent}** → "{response}"'
        for intent, response in faq_intents.items()
    )

    # Construct user input
    user_input = {
        "userTranscript": str(user_transcript),
        "fullTranscription": full_transcription or ""
    }

    # Your actual prompt (truncated or loaded from file/template)
    prompt = build_prompt(intent_entries)

    print(user_input)

    # === Non-streaming ===
    if not streaming:
        return await get_completion_without_phenomes(
            model, prompt, user_input, small_talk_history
        )


def get_faq_intents_from_file() -> Dict[str, str]:
    try:
        file_path = "scenarios.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Get list of scenarios
        scenarios_list = data.get("scenarios", [])

        # Build a map of scenarios by scenarioId
        scenarios = {
            scenario["scenarioId"]: scenario
            for scenario in scenarios_list
            if "scenarioId" in scenario
        }

        # Extract FAQ scenario
        faq_scenario = scenarios.get("FAQ")
        if faq_scenario and "steps" in faq_scenario:
            return {
                step["intent"]: step["botResponse"]
                for step in faq_scenario["steps"]
                if "intent" in step and "botResponse" in step
            }

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error in file {file_path}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return {}

def setApiKey(apiKey:str):
    global api_key
    api_key = apiKey

def setFaqIntents():
    global faq_intents
    faq_intents = get_faq_intents_from_file()
