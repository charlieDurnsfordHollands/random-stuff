import csv
import datetime
import random

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from sys import argv
from discord import Intents, Client
from discord.ext import tasks


def parse_args(inp_args):
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument(
        "-r",
        "--role",
        metavar="ROLE",
        help="The name of the role allowed to use commands",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--channel",
        metavar="CHANNEL",
        help="The id of the channel to post weekly prompts",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--token",
        metavar="TOKEN",
        help="The token of the discord bot",
        required=True,
    )
    args = parser.parse_args(inp_args)
    return args


async def send_message(message, user_message):
    try:
        response = handle_response(user_message)
        if response == "Unknown":
            return

        for i in range(0, len(response), 1800):
            await message.channel.send(response[i:i + 1800])

    except Exception as e:
        await message.channel.send(
            f"```{str(e)},"
            f" please ensure that all values and command syntax are correct```"
        )


def handle_response(message) -> str:
    p_message = message.lower()

    if p_message[:4] == "rfg!":
        p_message = p_message[4:]
    else:
        return "Unknown"

    if p_message[:4] == "help":
        return "```rfg!add_prompt <prompt> - Adds a prompt\n" \
               "rfg!remove_prompt <prompt> - Removes a prompt\n" \
               "rfg!list_prompts - Lists all current prompts\n" \
               "rfg!clear_prompts - Clears the list of prompts```"

    if p_message[:10] == "add_prompt":
        return add_prompt(p_message)

    if p_message[:13] == "remove_prompt":
        return remove_prompt(p_message)

    if p_message[:12] == "list_prompts":
        return list_prompts()

    if p_message[:13] == "clear_prompts":
        return clear_prompts()

    return "```Unknown command - Use rfg!help for a list of commands```"


def add_prompt(p_message):
    p_message = p_message[11:]

    if not p_message:
        return "```Command must include a prompt```"

    prompts_list = []

    with open("data.csv", "r", newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            prompts_list.append(row[0])

    if p_message in prompts_list:
        return "```Prompt already exists```"
    else:
        with open("data.csv", "a", newline='') as csvfile:
            csvfile.write(f"{p_message}\n")
        return "```Prompt added successfully```"


def remove_prompt(p_message):
    p_message = p_message[14:]

    if not p_message:
        return "```Command must include a prompt```"

    with open("data.csv", "r", newline='') as csvfile_read:
        reader = csv.reader(csvfile_read, delimiter=",")
        data = [row for row in reader]

        if [p_message] in data:
            data.remove([p_message])
        else:
            return f"```{p_message} not found in the prompts list```"

        with open("data.csv", "w", newline='') as csvfile_write:
            writer = csv.writer(csvfile_write)
            writer.writerows(data)

        return f"```Removing {p_message} from the prompts list```"


def list_prompts():
    with open("data.csv", "r", newline='') as csvfile_read:
        reader = csv.reader(csvfile_read, delimiter=",")
        data = [row for row in reader]

    return "```" + "\n".join(sum(data, [])) + "```"


def clear_prompts():
    open("data.csv", "w", newline='')

    return "```Prompts list cleared```"


def random_forum_generator():
    args = parse_args(argv[1:])
    role_name = args.role
    channel_id = args.channel
    token = args.token

    intents = Intents.default()
    intents.message_content = True

    client = Client(intents=intents)

    open("data.csv", "a+")

    @client.event
    async def on_ready():
        print(f'{client.user} is now running.')
        my_daily_task.start()

    @client.event
    async def on_message(message):

        user_message = str(message.content)

        if(message.author == client.user or
                len(user_message) == 0 or
                role_name not in list(role.name for role in message.author.roles)):
            return

        await send_message(message, user_message)

    @tasks.loop(time=datetime.time(hour=5, tzinfo=datetime.timezone.utc))
    async def my_daily_task():
        if datetime.datetime.now().weekday() != 0:
            with open("data.csv", "r", newline='') as csvfile_read:
                reader = csv.reader(csvfile_read, delimiter=",")
                data = sum([row for row in reader], [])
            if data:
                channel = client.get_channel(int(channel_id))
                await channel.create_thread(
                    name=f"Weekly Art Together Activity: "
                         f"{datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%d')}",
                    content=f"```This weeks prompt is: \"{random.choice(data)}\"```",
                )
            else:
                print("No Prompts to create a thread from")

    client.run(token)


if __name__ == '__main__':
    random_forum_generator()
