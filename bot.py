import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()

import os
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.vectorstores import Qdrant
from logic.database import search_image
from logic.conversation import process_question



# Discord

intents = discord.Intents.default()
intents.message_content = True
intents.typing = True
intents.messages = True

channel_id_1 = int(os.getenv('TARGET_CHANNEL_ID'))
channel_id_2 = int(os.getenv('TARGET_CHANNEL_ID_2'))
target_channels = [channel_id_1, channel_id_2]

bot = commands.Bot(command_prefix='!', intents=intents)
last_message_id = None

@bot.event
async def on_message(message):
    global last_message_id

    if message.channel.id not in target_channels:
        print("Not in target channel")
        return

    # Überprüfe, ob die Nachricht eine Antwort ist
    if message.reference:
        # Hole die ursprüngliche Nachricht, auf die geantwortet wurde
        original_message = await message.channel.fetch_message(message.reference.message_id)
        # Überprüfe, ob der Bot in der ursprünglichen Nachricht erwähnt wurde
        if bot.user not in original_message.mentions:
            return

    # ignore message if already sent
    if message.id == last_message_id:
        return
    
    if bot.user in message.mentions:
        last_message_id = message.id
        print("@MarketMaker Mentioned!")
        print(f"Nachricht von {message.author}: {message.content}")
        content = message.content

        question = content.replace(f'<@{bot.user.id}>', '').strip()
        # check if question is empty
        if not question:
            await message.channel.send("Entschuldigung, aber ich kann deine Anfrage nicht verstehen. Kannst du mir bitte weitere Informationen geben oder deine Frage klären?")
            return

        try:
            async with message.channel.typing():
                print("Question: ", question)

                response = process_question(question)
                if not response:
                    raise Exception("Keine Antwort von der Conversation Chain erhalten")

                # answer = '> ' + question + '\n' + response['answer']
                answer = response['answer']

                # add image
                img_links = search_image(answer)

                # print("Image Link: ", image_link)

                if not img_links == []:
                    # Fügen Sie den Bildlink in Ihre Antwort ein
                    if len(img_links) > 1:
                        answer += "\n\nHier sind einige Beispiele:\n\n"
                    else:
                        answer += "\n\nHier ist ein Beispiel:\n\n"

                    for img_link in img_links:
                        answer += f"{img_link}\n"

                # print("Answer: ", answer)

                # Generiere die Antwort
                max_length = 2000
                first_message = True
                while len(answer) > 0:
                    if len(answer) > max_length:
                        # Finde das letzte Leerzeichen innerhalb der maximalen Länge
                        last_space = answer.rfind(' ', 0, max_length)
                        if last_space == -1:
                            # Kein Leerzeichen gefunden, teile an der maximalen Länge
                            part = answer[:max_length]
                            answer = answer[max_length:]
                        else:
                            # Teile am letzten Leerzeichen
                            part = answer[:last_space]
                            answer = answer[last_space+1:]
                    else:
                        part = answer
                        answer = ""

                    if first_message:
                        await message.reply(part)
                        first_message = False
                    else:
                        await message.channel.send(part)

        except Exception as e:
            print(f"Error occurred: {e}")
            await message.channel.send("Entschuldige, ich konnte deine Frage nicht beantworten.")
    
    await bot.process_commands(message)


bot.add_listener(on_message)      
bot.run(os.environ.get("DISCORD_TOKEN"))

