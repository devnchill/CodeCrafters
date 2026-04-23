import argparse
import os
import json
import subprocess

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()
    messages = [{"role": "user", "content": args.p}]

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    while True:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "Read",
                        "description": "Read and return the contents of a file",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path to the file to read",
                                }
                            },
                            "required": ["file_path"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Write",
                        "description": "Write content to a file",
                        "parameters": {
                            "type": "object",
                            "required": ["file_path", "content"],
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to write to",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The content to write to the file",
                                },
                            },
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "description": "Execute a shell command",
                        "parameters": {
                            "type": "object",
                            "required": ["command"],
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The command to execute",
                                }
                            },
                        },
                    },
                },
            ],
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choicesin response")
        ai_message = chat.choices[0].message
        message_dict = {"role": "assistant", "content": ai_message.content or ""}
        if ai_message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in ai_message.tool_calls
            ]
        messages.append(message_dict)

        if not ai_message.tool_calls:
            print(ai_message.content)
            exit(0)
        for tool_call in ai_message.tool_calls:
            func = tool_call.function
            args = json.loads(func.arguments)
            if func.name == "Write":
                file_path = args["file_path"]
                content = args["content"]
                with open(file_path, "w+") as f:
                    f.write(content)
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": content}
                )
            elif func.name == "Bash":
                command = args["command"].split(" ")
                res = subprocess.run(command, capture_output=True, text=True)
                output = (res.stdout or "") + (res.stderr or "")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": output,
                    }
                )

            else:
                file_path = args["file_path"]
                with open(file_path) as f:
                    data = f.read()
                    messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": data}
                    )


if __name__ == "__main__":
    main()
