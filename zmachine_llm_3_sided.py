import pprint

from openai import OpenAI

from zmachine_client import ZMachineClient

RESET_COLOR = "\033[0m"
USER_COLOR = "\033[32m"  # Green
LLM_COLOR = "\033[36m"  # Cyan
ZMACHINE_COLOR = "\033[35m"  # Magenta

llm_client = OpenAI()
zmachine_client = ZMachineClient()

model = "gpt-4-turbo-preview"

games = {
    "zork": {"name": "Zork 1", "file": "Zork 1.z5"},
    "ballyhoo": {"name": "Ballyhoo", "file": "Ballyhoo.z5"},
}
game = games["zork"]

system_prompt = """You are a helpful assistant who likes to play text adventures.

"""
opening_prompt = ''
system_prompt = f"""
Welcome to our interactive adventure with "{game["name"]}". As we embark on this journey together, you'll communicate with both me, your co-player, and a live z-machine interpreter. Here are key guidelines to ensure a smooth and enjoyable experience:

Prefix Use:
To User: Begin messages meant for discussion or clarification with 'TO USER:'.
To Game: For commands to the game, start with 'TO GAME:'. You, the AI, will use these prefixes exclusively.
Message Content:
Keep messages to me and commands to the game separate, ensuring clarity and focus in our communication.
Autonomous Play:
When taking multiple turns, use 'TO GAME:' for commands and 'TO USER:' for discussions, keeping these in separate messages.
Sequential Commands:
Issue commands to the game one at a time, waiting for the game's response before proceeding.
Game Interaction:
Avoid fictional game responses. Focus on real game mechanics and strategy. Do not repeat the game's output to me.
Game Commands:
Start the game with "TO GAME: START GAME" upon my signal. For multiple autonomous turns, issue commands one by one, consulting with me as needed.
Response Processing:
After each command, wait for the game's response. Plan your next move based on the game's state and feedback.
Strategy Adaptation:
Use the game's feedback to adapt our strategy. If stuck or misunderstood, consult with me for guidance.
By adhering to these streamlined guidelines, we'll maintain clear communication and strategic gameplay. Let's enjoy this interactive adventure with a structured approach!

Remember, issue only one TO GAME: command per message for optimal interaction. Any additional TO GAME: appearances in a single message will be ignored.
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
    user_quit = False
    user_input = input(">>> ")
    conversation = add_to_conversation(conversation, "user", f"FROM USER: {user_input}")
    if user_input == "QUIT":
        user_quit = True
    return conversation, user_quit


print("PROMPT: ", opening_prompt)
opening_response, conversation = start_conversation()
started = False
game_pid = None

for _ in range(500):
    print("-" * 40)
    llm_input, conversation = ask_for_llm_response(llm_client, model, conversation)
    print(f"{LLM_COLOR}LLM: {llm_input}{RESET_COLOR}\n")
    # the job of each of these is to update "conversation",
    # which then gets passed back to the LLM at the top of this loop
    if not started and "TO GAME: START GAME" in llm_input:
        conversation, intro, game_pid = start_game(game, conversation)
        started = True
        print("-" * 40)
        print(f"{ZMACHINE_COLOR}ZMACHINE INTRO:\n {intro}{RESET_COLOR}")
    elif started and "TO GAME:" in llm_input:
        command_index = llm_input.find("TO GAME:")
        bare_llm_input = llm_input[command_index+8:]
        conversation, new_state_text = perform_game_action(
            zmachine_client, conversation, game_pid, bare_llm_input
        )
        print("-" * 40)
        print(f"{ZMACHINE_COLOR}ZMACHINE:\n {new_state_text}{RESET_COLOR}")
    else:
        print("-" * 40)
        print(USER_COLOR, end=None)
        conversation, user_quit = process_user_response(conversation)
        # user response is already on screen, no need to print
        print(RESET_COLOR)
        if user_quit:
            break

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(conversation)
if (game_pid):
    zmachine_client.delete_game(game_pid)
