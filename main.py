import sys
import json
import os
import re
from tools.routing import get_route_day
from tools.sleep_spots import suggest_sleep_spot
from tools.activities import find_activities
from tools.weather import get_weather_forecast
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

tool_functions = {
    "get_route_day": get_route_day,
    "suggest_sleep_spot": suggest_sleep_spot,
    "find_activities": find_activities,
    "get_weather_forecast": get_weather_forecast
}

def resolve_placeholders(args: dict, context: dict) -> dict:
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

def handle_run(request):
    user_prompt = request.get("prompt")
    state = request.get("state", {})
    memory = request.get("memory", [])

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
    try:
        plan = json.loads(plan_text)
        steps = plan.get("steps", [])
    except Exception as e:
        return {"error": "Failed to parse plan", "plan_text": plan_text, "exception": str(e)}

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
        context[tool] = output
        context[f"step{i}"] = output
        results.append({"tool": tool, "input": args, "output": output})
    return {"plan": steps, "results": results}

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            request = json.loads(line)
        except Exception as e:
            sys.stdout.write(json.dumps({"error": f"Invalid JSON: {str(e)}"}) + "\n")
            sys.stdout.flush()
            continue
        method = request.get("method")
        if method == "run":
            response = handle_run(request.get("params", {}))
        else:
            response = {"error": "Unknown method", "method": method}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main() 