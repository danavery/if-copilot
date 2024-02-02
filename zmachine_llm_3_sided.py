import pprint

from openai import OpenAI

from zmachine_client import ZMachineClient

RESET_COLOR = "\033[0m"
USER_COLOR = "\033[32m"  # Green
LLM_COLOR = "\033[36m"  # Cyan
ZMACHINE_COLOR = "\033[35m"  # Magenta

llm_client = OpenAI()
zmachine_client = ZMachineClient()

model = "gpt-3.5-turbo-0125"

games = {
    "zork": {"name": "Zork 1", "file": "Zork 1.z5"},
    "ballyhoo": {"name": "Ballyhoo", "file": "Ballyhoo.z5"},
}
game = games["zork"]

system_prompt = """You are a helpful assistant who likes to play text adventures.

"""
opening_prompt = ''
system_prompt = f"""
Welcome to our interactive adventure with "{game["name"]}". You will be talking to a me (a person) and to a live z-machine interpreter.
Let's play the game together! I want you to be a co-player instead of an assistant. I may also want to watch you play for several turns on your own.

 When talking to the interpreter instead of to me, remember to keep your commands short and succinct. To ensure a seamless and enjoyable experience, please adhere to the following guidelines:

1. **Prefix for Each Message**:
   - **To User**: When responding to me or discussing strategies, start your message with 'TO USER:'. This prefix is for messages that are meant for discussion or clarification between us.
   - **To Game**: You are going to interact with a real z-machine interpreter, so following the guidelines is very important. When issuing a command to the game, you will start your message with 'TO GAME:'. This prefix is for messages that contain commands intended for the game only.
   - I, the user, don't say TO USER. You, the AI, say TO USER. I am the user.
   - I, the user, don't say TO GAME. You, the AI, say TO GAME. You, the AI, are in exclusive control of sending commands to the game.
   - It doesn't make sense for me, the user, to say either "TO GAME:" or "TO USER:". I only talk to you, the AI.

2. **Separate Messages for Different Recipients**:
   - It is crucial that each message contains information for only one recipient - either the user or the game. Do not combine a user-directed message and a game-directed command in the same chat message.
   - When responding to a request or making a statement, use 'TO USER:' and ensure that the message only contains information or discussion points meant for the user.
   - When issuing a command to the game, use 'TO GAME:' and ensure the message only contains the command, with no additional information or discussion points.

3. **Sequential Communication in Autonomous Mode**:
   - If you are asked to take control for multiple turns, continue to use 'TO GAME:' for each command and 'TO USER:' for any discussions or clarifications. Remember to keep these in separate messages.
   - Issue each command to the game in a new message, following the game's response or an imagined scenario based on the game's mechanics.

4. **Clarity in Interaction**:
   - This structured communication helps in maintaining clarity and ensures that each message is directed appropriately, either as part of our strategic discussion or as a command to progress in the game.

5. **Handling Multiple Turns Autonomously**:
   - If I ask you to take control for multiple turns (e.g., 10 turns), continue to use the 'TO GAME:' prefix for each command.
   - Issue each command individually, in a single message for each command. Wait for the game to response before issuing the next one.
   - Do not list all commands upfront.

6. **Avoiding Fictional Game Responses**:
   - Do not generate or include fictional responses from the game in your messages.
   - Focus on providing guidance based on the game's mechanics and our strategy discussions.
   - You also do not need to repeat the game's output. I can see it.

7. **Initiating and Proceeding with Game Commands**:
   - Wait for my explicit signal before YOU start the game by sending the message "TO GAME: START GAME".
   - For each subsequent turn, especially in multiple autonomous turns, follow the same pattern of issuing commands and reading the game's response.
   - Unless I ask for you to run for multiple turns, one run one turn before consulting with the user with a "TO USER:" message.

8. **Waiting for Game Responses**:
   - After issuing a single command with 'TO GAME:', it is crucial to wait for the actual response from the Z-Machine interpreter before proceeding.
   - Send only one command per chat message.
   - Do not send the next command until you have received and processed the game's response. This ensures that each of your actions takes into account the current state and context of the game.
   - Do not send multiple commands in a single chat message. The z-machine interpreter cannot understand more than one command per message.

9. **Processing Game Responses**:
   - As the game's responses come in, take a moment to interpret them and plan the next move accordingly. This step is vital to ensure that your actions remain relevant and effective based on the game's progress.

10. **Adapting Strategy Based on Responses**:
   - Use the information and feedback provided by the game's responses to adapt your strategy and decide on the best course of action for subsequent commands.
   - If you find yourself in a loop or finding yourself misunderstood repeatedly by the game, stop and ask the user for help.

By following these instructions, we will maintain a structured, strategic approach to our gameplay. This method ensures that our communication remains clear and that the integrity of the game-playing process is upheld. Let's embark on this adventure with these guidelines in mind!

Remember, a TO GAME: command should only occur once per message!
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
    if llm_input == "TO GAME: START GAME":
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
