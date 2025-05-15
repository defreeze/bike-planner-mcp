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
import uvicorn
from typing import Any
import re
from fastapi.responses import JSONResponse

# test change 

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

def resolve_placeholders(args: dict, context: dict) -> dict:
    """Replace placeholders in args with values from context."""
    def replace(val):
        if isinstance(val, str):
            matches = re.findall(r"<([\w\.]+)>", val)
            for m in matches:
                keys = m.split('.')
                v = context
                for k in keys:
                    v = v.get(k, None)
                    if v is None:
                        break
                if v is not None:
                    val = val.replace(f"<{m}>", str(v))
            return val
        elif isinstance(val, list):
            return [replace(x) for x in val]
        elif isinstance(val, dict):
            return {k: replace(v) for k, v in val.items()}
        return val
    return {k: replace(v) for k, v in args.items()}

@app.post("/run")
async def run_planner(request: Request):
    body = await request.json()
    user_prompt = body.get("prompt")
    state = body.get("state", {})
    memory = body.get("memory", [])

    # Step 1: Ask LLM for a plan (improved prompt with explicit example)
    planning_prompt = f"""
    You are a trip planner. Based on the following user request, output a JSON plan of tool calls to achieve the goal.
    Each step must include all required arguments for the tool.
    Available tools:
    - get_route_day(start: string, distance_km: integer)
    - get_weather_forecast(location: string)
    - suggest_sleep_spot(location: string)
    - find_activities(location: string, preferences: list of strings)

    Example plan:
    {{
      "steps": [
        {{"tool": "get_route_day", "args": {{"start": "Groningen", "distance_km": 70}}}},
        {{"tool": "get_weather_forecast", "args": {{"location": "<get_route_day.end>"}}}},
        {{"tool": "suggest_sleep_spot", "args": {{"location": "<get_route_day.end>"}}}},
        {{"tool": "find_activities", "args": {{"location": "<get_route_day.end>", "preferences": ["nature"]}}}}
      ]
    }}

    User request: {user_prompt}
    Output only valid JSON with a 'steps' list.
    """
    planning_messages = memory + [
        {"role": "user", "content": planning_prompt}
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=planning_messages,
        temperature=0.2,
        max_tokens=512
    )
    plan_text = response.choices[0].message.content
    print("\n--- LLM PLAN ---\n", plan_text)
    try:
        plan = json.loads(plan_text)
        steps = plan.get("steps", [])
    except Exception as e:
        print("\n--- PLAN PARSE ERROR ---\n", plan_text)
        return {"error": "Failed to parse plan", "plan_text": plan_text, "exception": str(e)}

    # Step 2: Execute the plan
    context = {}
    results = []
    for i, step in enumerate(steps):
        tool = step["tool"]
        args = resolve_placeholders(step.get("args", {}), context)
        required_args = tool_functions[tool].__code__.co_varnames[:tool_functions[tool].__code__.co_argcount]
        missing_args = [arg for arg in required_args if arg not in args]
        if tool not in tool_functions:
            results.append({"error": f"Unknown tool: {tool}"})
            continue
        if missing_args:
            results.append({
                "tool": tool,
                "input": args,
                "error": f"Missing required arguments: {missing_args}"
            })
            continue
        try:
            output = tool_functions[tool](**args)
        except Exception as e:
            results.append({
                "tool": tool,
                "input": args,
                "error": f"Exception: {str(e)}"
            })
            continue
        # Store output in context for placeholder resolution
        context[tool] = output
        context[f"step{i}"] = output
        results.append({"tool": tool, "input": args, "output": output})
    print("\n--- TOOL RESULTS ---\n", json.dumps(results, indent=2))
    return {"plan": steps, "results": results}

@app.get("/tools")
def list_tools():
    return JSONResponse([schema["function"] for schema in tool_schemas])

@app.get("/mcp.json")
def mcp_manifest():
    return {
        "name": "bike-planner-mcp",
        "description": "A modular trip planning MCP for Smithery.",
        "tools": [schema["function"] for schema in tool_schemas],
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

