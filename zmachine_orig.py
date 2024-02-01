from openai import OpenAI
import pprint
import requests

client = OpenAI()
opening_prompt = """
We're going to start the game Zork.
I will be the game. You will be the player.
To repeat, you will be the player.
My next response will be the start of the game.
All of my succeeding responses will be from the game itself.
Look around and see if you can score any points.
Do not add a > character to the front of your commands--type exactly what a user would type when playing.
Do not complete text from the game itself--you are the player, not the game.
Periodically you should respond with 'SCORE' to check on your progress.
Ready?
"""

conversation = [
    {
        "role": "system",
        "content": "You are a helpful assistant who likes to play text adventures.",
    },
    {
        "role": "user",
        "content": opening_prompt,
    },
]

print(f"OPENING: {opening_prompt}")
response = client.chat.completions.create(model="gpt-3.5-turbo", messages=conversation)
print("LLM: ", response.choices[0].message.content)


def zmachine(url, method="GET", payload=None):
    if method == "GET":
        response = requests.get(url)
    if method == "POST":
        response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        # print(data)
    else:
        print(f"error: {response}")
        data = ""
    return data


server = "http://localhost:3000/"

titles = zmachine(server + "titles")
new_game = zmachine(server + "games", "POST", {"game": "Zork 1.z5", "label": "testing"})
game_pid = new_game["pid"]
intro_text = new_game["data"]
print("OPENING: ", intro_text)
new_message = {"role": "user", "content": intro_text}
conversation.append(new_message)
# print("-----", conversation, "-----")

for _ in range(100):
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=conversation)
    command = response.choices[0].message.content
    print(f"LLM: > {command}\n")
    command_json = {"action": f"{command}"}
    new_message = {"role": "assistant", "content": command}
    conversation.append(new_message)
    if command == "QUIT":
        break
    command_response = zmachine(
        server + f"games/{game_pid}/action", "POST", {"action": f"{command}"}
    )
    new_status = command_response["data"]
    print(f"ZMACHINE:\n {new_status}")
    new_message = {"role": "user", "content": new_status + "\n> "}
    conversation.append(new_message)

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(conversation)
