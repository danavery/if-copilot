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

system_prompt = """You are a helpful assistant who likes to play text adventures.

"""

opening_prompt = f"""
We're going to play the game {game["name"]}.
You're going to participate in two chats simultaneously.
The first will be with me.
You will prefix all text intended for me with 'TO USER:'.
The second will be with an interactive fiction game.
You will preface all text intended for that game with 'TO GAME:'
I will not issue commands with 'TO GAME:'. Only you can do that.
You can only interact with the game or with me in each message.
This way we will be able to communicate with each other and decide on the next move in the game,
and you will issue the commands.
You are the player, not the game, so you have no need to ever use the "FROM GAME:" prefix.
You are the player who issues commands to the game. Do not respond with game text.
All responses from the game will be prefixed "FROM GAME:".
You do not need to relay responses from the game back to me. I can see the game's responses.
Responses from me will have no specific prefix.
If I ask a question, do not immediately issue a command to the game. Clear it with me first.
Only issue one command to the game at a time and wait for a response from the game before issuing any more commands.
Do not issue further commands before getting a response to your current command.
The game has not started yet.
We will discuss the game first,
then you (the AI) will issue the command "TO GAME: START GAME" when I ask you to.
You will not start until I ask you to.

Do you understand? Please concisely explain your instructions back to me.
"""


def add_to_conversation(conversation, role, content):
    new_message = {"role": role, "content": content}
    conversation.append(new_message)
    return conversation


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
    conversation = add_to_conversation(conversation, "assistant", opening_response)
    return opening_response, conversation


def start_game(game, conversation):
    new_game = zmachine_client.new_game(game=game["file"], label="testing")
    game_pid = new_game["pid"]
    intro_text = new_game["data"] + "\n>"
    conversation = add_to_conversation(conversation, "user", intro_text)
    return conversation, intro_text, game_pid


def ask_for_llm_response(llm_client, model, conversation):
    llm_response = llm_client.chat.completions.create(
        model=model, messages=conversation
    )
    command = llm_response.choices[0].message.content
    conversation = add_to_conversation(conversation, "assistant", command)
    return command, conversation


def perform_game_action(zmachine_client, conversation, game_pid, command):
    new_state = zmachine_client.action(game_pid=game_pid, command=command)
    new_state_text = "FROM GAME:\n" + new_state["data"] + "> "
    conversation = add_to_conversation(conversation, "user", new_state_text)
    return conversation, new_state_text


def process_user_response(conversation):
    user_input = input(">>> ")
    conversation = add_to_conversation(conversation, "user", f"FROM USER: {user_input}")
    return conversation


print("PROMPT: ", opening_prompt)
opening_response, conversation = start_conversation()
started = False

for _ in range(50):
    print("-" * 40)
    llm_input, conversation = ask_for_llm_response(llm_client, model, conversation)
    print(f"LLM: {llm_input}\n")
    # the job of each of these is to update "conversation",
    # which then gets passed back to the LLM at the top of this loop
    if llm_input == "TO GAME: START GAME":
        conversation, intro, game_pid = start_game(game, conversation)
        started = True
        print("GAME INTRO: ", intro)
    elif started and llm_input.startswith("TO GAME:"):
        bare_llm_input = llm_input[len("TO GAME:"):]
        print(bare_llm_input)
        conversation, new_state_text = perform_game_action(
            zmachine_client, conversation, game_pid, bare_llm_input
        )
        print(f"ZMACHINE:\n {new_state_text}")
    else:
        conversation = process_user_response(conversation)
        # user response is already on screen, no need to print
        print()

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(conversation)

zmachine_client.delete_game(game_pid)
