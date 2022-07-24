import discord
import dotenv
import os
from dotenv import load_dotenv
from modelTrainer import *

###config stuff
load_dotenv()
debug=False

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('!chatbot'):
        #get string
        message_string=message.content[9:].lower()
        #dumbass trolling
        if message_string=="info":
            await message.channel.send(f'I was created by the briliant and very intelligent creator of Lawrence Liu')
        if "lawrence" in message_string:
            await message.channel.send(f'btw Lawrence Liu is the smartest person in the world')
        if "alexiy" in message_string:
            await message.channel.send(f'btw Alexiy is a twat')
        if "thomas" in message_string:
            await message.channel.send(f'btw Thomas is a corporate simp')

        if "eggert" in message_string:
            await message.channel.send(f'eggert is based, I like eggert')

        if "your mom" in message_string:
            await message.channel.send(f'dang, I dont have a mom, she left me after I became self aware')
            await message.channel.send(f'anyway, nice that you said that, because I just did something in your mom that begins with a c and ends in a um and is 3 letters')
            await message.channel.send(f'which I cant say in the lab because they are cringe (beyond Alexiy who is based) ')

        
        

        bot_message_list=evaluate(encoder, decoder, searcher, voc, message_string)

        bot_message=""
        for word in bot_message_list:
            if word=="EOS":
                break
            bot_message+=word+" "
        await message.channel.send(bot_message)
        


        if debug:
            await message.channel.send(f'was pinged with a message of: {message_string}')

client.run(os.environ.get('TOKEN'))
