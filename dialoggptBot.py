import discord
from dotenv import load_dotenv
from dialoggptUtils import *
import subprocess
import  time
import asyncio
import os
#from threading import Timer

async def delMsg(msg):
    await asyncio.sleep(10)
    await msg.delete()


###config stuff
load_dotenv()
debug=False

client = discord.Client()
##init model
tokenizer, model = load_tokenizer_and_model()
print("Model Loaded")
###init chatbot_history
#lazy way rn, may change latter to record and load back
chat_histories={}

serious_channels = [974553346591576105,927849858025529474, 972963507916128297]

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    print(chat_histories)

    author = message.author.id
    #stop it from fucking around if it looking at its own message
    if message.author == client.user:
        return
    if (message.channel.id in serious_channels):
        return
    #1984 feature could be added here ;)
    if ("pipi" in message.content.lower()):
        msg = await message.channel.send("""Are you kidding ??? What the \\*\\*\\*\\* are you talking about man ? You are a biggest looser i ever seen in my life ! You was doing PIPI in your pampers when i was beating players much more stronger then you! You are not proffesional, because proffesionals knew how to lose and congratulate opponents, you are like a girl crying after i beat you! Be brave, be honest to yourself and stop this trush talkings!!! Everybody know that i am very good blitz player, i can win anyone in the world in single game! And \"w\"esley \"s\"o is nobody for me, just a player who are crying every single time when loosing, ( remember what you say about Firouzja ) !!! Stop playing with my name, i deserve to have a good name during whole my chess carrier, I am Officially inviting you to OTB blitz match with the Prize fund! Both of us will invest 5000$ and winner takes it all!

I suggest all other people who's intrested in this situation, just take a look at my results in 2016 and 2017 Blitz World championships, and that should be enough... No need to listen for every crying babe, Tigran Petrosyan is always play Fair ! And if someone will continue Officially talk about me like that, we will meet in Court! God bless with true! True will never die ! Liers will kicked off...""")
        await asyncio.sleep(10)
        await msg.delete()
        return
    
    if ("fortune" in message.content.lower() and message.channel.id == 912240638664257555):
        fort = subprocess.run(["fortune"], stdout=subprocess.PIPE, text=True)
        await message.channel.send(fort.stdout)
        return
    # rms copypasta
    if ("linux" in message.content.lower() and "gnu/linux" not in message.content.lower() and "gnu+linux" not in message.content.lower() and "ucla.edu" not in message.content.lower()):
        msg=await message.channel.send("""
I'd just like to interject for a moment. What you're refering to as Linux, is in fact, GNU/Linux, or as I've recently taken to calling it, GNU plus Linux. Linux is not an operating system unto itself, but rather another free component of a fully functioning GNU system made useful by the GNU corelibs, shell utilities and vital system components comprising a full OS as defined by POSIX.

Many computer users run a modified version of the GNU system every day, without realizing it. Through a peculiar turn of events, the version of GNU which is widely used today is often called Linux, and many of its users are not aware that it is basically the GNU system, developed by the GNU Project.

There really is a Linux, and these people are using it, but it is just a part of the system they use. Linux is the kernel: the program in the system that allocates the machine's resources to the other programs that you run. The kernel is an essential part of an operating system, but useless by itself; it can only function in the context of a complete operating system. Linux is normally used in combination with the GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. All the so-called Linux distributions are really distributions of GNU/Linux!
""")
        #time.sleep(10)
        #await msg.delete()
        #Timer(10.0, deleteMsg, (msg,)).start()
        asyncio.ensure_future(delMsg(msg))
        return

    # anti-typeracer
    if "typeracer.com/" in message.content.lower():
        await message.channel.send(f"Give it up folks, {message.author.display_name} over here has something to say. What's that buddy? Wha- A faster WPM?!? WHAT?!? B... Bu... That can't be possible! Surely not! A FASTER WPM? IN MY SIGHT?!? What a great, absolute miracle that you and your 57 WPM fingers were here to beat me! Thank you! Have my grattitude, Actually, What's your cashapp? I'd like to give you 20$... Know what? While we're at it have the keys to my car. Actually, no, scratch that. Have the keys to my house, go watch my kids grow up and fuck my wife. Also, my Paypal username and password is: Ihavenolife4 and 968386329. Go have fun. Thank you for your work.")
        return

        #check if we are in the right channel
    if (message.channel.id != 912240638664257555):
        return

    #check if the chatbot trigger word, !chatbot is in the message
    if not message.content.startswith('!chatbot'):
        #if it isn't stop (return)
        return

    #get string
    message_string=message.content[9:].lower()
    #actually important message things
    #erase message history
    if message_string=="reset!":
        await message.channel.send("reseting the chatbot for this user")
        chat_histories[author]=None
        await message.channel.send("chatbot erased")
        return
    #maybe an actuall info thing would be usefull
    if message_string=="info!":
        await message.channel.send("Hello! I am an AI chatbot running on Microsoft's DialogGpt model")
        await message.channel.send("You can chat with me using the !chatbot [insert messsage] command")
        await message.channel.send("And also you can reset my conversation with you with the !Chatbot reset! command")
        return
    #dumbass trolling maybe

    #check the message author
    if author not in  chat_histories.keys():
        chat_histories[author]=None
    #actual juciy chatbot shit now
    chat_histories[author],chatbotOutput=generate_response(tokenizer, model, chat_histories[author]==None, 
                    chat_histories[author],message_string)
    
    await message.channel.send(chatbotOutput)

client.run(os.environ.get('TOKEN'))
