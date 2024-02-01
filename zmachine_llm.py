import pprint

from openai import OpenAI

from zmachine_client import ZMachineClient

llm_client = OpenAI()
zmachine_client = ZMachineClient()

model = "gpt-3.5-turbo"

games = {
    "zork": {"name": "Zork 1", "file": "Zork 1.z5"},
    "ballyhoo": {"name": "Ballyhoo", "file": "Ballyhoo.z5"},
}
game = games["zork"]

system_prompt = "You are a helpful assistant who likes to play text adventures."

opening_prompt = f"""
We're going to start the game {game["name"]}.
I will play the role of the game. You will play the role of the player.
To repeat, you are the player. Do not mimic the game's text or error messages;
your responses should be commands or actions a player would take.
If you're not being understood, do not apologize. Simply reply with another command.
My next response will be the start of the game.
All of my succeeding responses will be from the game itself.
Look around and see if you can score any points.
Do not add a > character to the front of your commands--type exactly what a user would type when playing.
Do not complete text from the game itself--you are the player, not the game.
Periodically you should respond with 'SCORE' to check on your progress.
Try not to repeat yourself too much. Explore the scenes. Take your time.
A hint! Look underneath moveable objects.
Ready?
"""


def start_conversation():
    conversation = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": opening_prompt,
        },
    ]

    response = llm_client.chat.completions.create(model=model, messages=conversation)
    opening_response = response.choices[0].message.content
    new_message = {"role": "assistant", "content": opening_response}
    conversation.append(new_message)
    return opening_response, conversation


def start_game(game, conversation):
    new_game = zmachine_client.new_game(game=game["file"], label="testing")
    game_pid = new_game["pid"]
    intro_text = new_game["data"] + "\n>"
    new_message = {"role": "user", "content": intro_text}
    conversation.append(new_message)
    return game_pid, intro_text, conversation


def get_next_command(llm_client, model, conversation):
    llm_response = llm_client.chat.completions.create(
        model=model, messages=conversation
    )
    command = llm_response.choices[0].message.content

    new_message = {"role": "assistant", "content": command}
    conversation.append(new_message)
    return command, conversation


def perform_game_action(zmachine_client, conversation, game_pid, command):
    new_state = zmachine_client.action(game_pid=game_pid, command=command)
    new_state_text = new_state["data"] + "\n> "

    new_message = {"role": "user", "content": new_state_text}
    conversation.append(new_message)
    return new_state_text, conversation


print("PROMPT: ", opening_prompt)
opening_response, conversation = start_conversation()
print("LLM: ", opening_response)
game_pid, intro, conversation = start_game(game, conversation)
print("GAME INTRO: ", intro)

for _ in range(5):
    command, conversation = get_next_command(llm_client, model, conversation)
    print(f"LLM: {command}\n")

    if command == "QUIT":
        break

    new_state_text, conversation = perform_game_action(
        zmachine_client, conversation, game_pid, command
    )
    print(f"ZMACHINE:\n {new_state_text}")

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(conversation)

zmachine_client.delete_game(game_pid)
