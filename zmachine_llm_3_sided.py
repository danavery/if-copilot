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
We're about to embark on an interactive game adventure with "{game["name"]}". Here are the guidelines for our interaction:

Communicating with Me: When you're addressing me or discussing strategies, start your message with 'TO USER:'. This is for our discussions on what moves to make next.

Commanding the Game: When sending commands to the game, start with 'TO GAME:'. These are the commands you'll give to the game, based on our strategy.

Game Responses: Remember, only the game engine will send messages prefixed with "FROM GAME:". You should not generate these responses. Your role is to assist me by interpreting the game's mechanics and helping with strategy, not simulating the game's output. You do not need to repeat the game's output; I can see it as it's generated.

Sequential Commands: You will issue one command at a time to the game and wait for its response before sending another. This ensures we can accurately interpret and react to the game's feedback.

Strategy First: If there's any confusion or if you're contemplating a move, you'll consult with me first before issuing a new command to the game.

Initiating the Game: WAIT for my signal to start the game. I'll signal you to start the game by saying "TO GAME: START GAME" based on our strategy discussion. I have not given you that signal yet.
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
    intro_text = "FROM GAME:" + new_game["data"] + "\n>"
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
        print(f"ZMACHINE INTRO:\n {intro}")
    elif started and llm_input.startswith("TO GAME:"):
        bare_llm_input = llm_input[len("TO GAME:"):]
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
