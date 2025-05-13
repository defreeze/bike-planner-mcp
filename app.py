
import json
from fastapi import FastAPI, Request
from tools.routing import get_route_day
from tools.sleep_spots import suggest_sleep_spot
from tools.activities import find_activities
from tools.weather import get_weather_forecast
import openai
from dotenv import load_dotenv
import os
import pprint

load_dotenv()  
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Function map
tool_functions = {
    "get_route_day": get_route_day,
    "suggest_sleep_spot": suggest_sleep_spot,
    "find_activities": find_activities,
    "get_weather_forecast": get_weather_forecast
}

# Tool definitions
tool_schemas = [
    {
        "type": "function",
        "function": {
            "name": "get_route_day",
            "description": "Generate a route segment based on start and distance",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string"},
                    "distance_km": {"type": "integer"}
                },
                "required": ["start", "distance_km"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_sleep_spot",
            "description": "Suggest a place to sleep at the end of the day",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_activities",
            "description": "Find activities near a location based on user preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "preferences": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["location", "preferences"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get a 3-day weather forecast for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]


@app.post("/run")
async def run_planner(request: Request):
    body = await request.json()
    user_prompt = body.get("prompt")
    state = body.get("state", {})
    memory = body.get("memory", [])

    messages = memory + [
        {"role": "user", "content": user_prompt}
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        tools=tool_schemas,
        tool_choice="auto"
    )

    response = completion.choices[0]
    tool_call = response.get("message", {}).get("tool_calls", [None])[0]

    if tool_call:
        func_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        print(f"🔧 Tool call received: {func_name} with args {arguments}")
        result = tool_functions[func_name](**arguments)
        print("✅ Tool output:")
        pprint.pprint(result)
        return {"tool_called": func_name, "output": result}
    else:
        model_msg = response.get("message", {}).get("content", "[No content]")
        print("💬 Model response (no tool call):")
        print(model_msg)
        return {"message": model_msg}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

