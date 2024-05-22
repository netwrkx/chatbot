import discord
from dotenv import load_dotenv
from dialoggptUtils import *
import subprocess
import  time
import asyncio
import os
import re
from unidecode import unidecode
import sqlite3
import random

import requests
import sseclient
import json

url = "http://127.0.0.1:5000/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

queue = []

isGenerating = False

async def parser(content, usrmsg):
    #print("Parsing: " + content)
    prompt = ""
    tokens = 1500
    temperature = 0.7
    top_p = 1
    top_k = 0
    typical_p = 1
    min_p = 0.05
    repetition_penalty = 1
    frequency_penalty = 0
    presence_penalty = 0

    c = content.split("--")
    prompt = c[0]
    c.pop(0)
    for i in c:
        cs = i.split()
        if (cs[0] == "tokens"):
            try:
                tokens = int(cs[1])
                if (tokens <= 9 or tokens > 4096):
                    await usrmsg.reply("Invalid token count")
                    return
            except:
                await usrmsg.reply("Error: --tokens")
                return
        elif (cs[0] == "temp"):
            try:
                temperature = float(cs[1])
                if (temperature > 5 or temperature < 0):
                    await usrmsg.reply("Invalid temperature")
                    return
            except:
                await usrmsg.reply("Error: --temp")
                return
        elif (cs[0] == "top_p"):
            try:
                top_p = float(cs[1])
                if (top_p > 1 or top_p < 0):
                    await usrmsg.reply("Invalid top_p")
                    return
            except:
                await usrmsg.reply("Error: --top_p")
                return
        
        elif (cs[0] == "top_k"):
            try:
                top_k = int(cs[1])
                if (top_p > 200 or top_p < 0):
                    await usrmsg.reply("Invalid top_k")
                    return
            except:
                await usrmsg.reply("Error: --top_k")
                return
        elif (cs[0] == "typical_p"):
            try:
                typical_p = float(cs[1])
                if (typical_p > 1 or typical_p < 0):
                    await usrmsg.reply("Invalid typical_p")
                    return
            except:
                await usrmsg.reply("Error: --typical_p")
                return

        elif (cs[0] == "min_p"):
            try:
                min_p = float(cs[1])
                if (min_p > 1 or min_p < 0):
                    await usrmsg.reply("Invalid min_p")
                    return
            except:
                await usrmsg.reply("Error: --min_p")
                return

        elif (cs[0] == "rep_p"):
            try:
                repetition_penalty = float(cs[1])
                if (repetition_penalty > 1.5 or repetition_penalty < 1):
                    await usrmsg.reply("Invalid rep_p")
                    return
            except:
                await usrmsg.reply("Error: --rep_p")
                return

        elif (cs[0] == "freq_p"):
            try:
                frequency_penalty = float(cs[1])
                if (frequency_penalty > 2 or frequency_penalty < 0):
                    await usrmsg.reply("Invalid freq_p")
                    return
            except:
                await usrmsg.reply("Error: --freq_p")
                return

        elif (cs[0] == "pres_p"):
            try:
                presence_penalty = float(cs[1])
                if (presence_penalty > 2 or presence_penalty < 0):
                    await usrmsg.reply("Invalid pres_p")
                    return
            except:
                await usrmsg.reply("Error: --pres_p")
                return
        else:
            await usrmsg.reply("Invalid switch. Please use the following switches instead: --tokens, --temp, --top_p, --top_k, --typical_p, --min_p, --rep_p, --freq_p, --pres_p")
            return
    return prompt, tokens, temperature, top_p, top_k, typical_p, min_p, repetition_penalty, frequency_penalty, presence_penalty






async def aiGen(usrmsg):
    global isGenerating
    if (not usrmsg is None):
        content = usrmsg.content[5:]
    if(isGenerating):
        try:
            p = await parser(content, usrmsg)
            if (len(p) == 0):
                return
        except:
            return
        try:
            botmsg = await usrmsg.reply(f"Queued... Position: {len(queue)+1}")
        except:
            return
        queue.append([usrmsg, botmsg, content]) 
        return
    else:
        isGenerating = True
    history = []
    botmsg = 0



    if (usrmsg is None and len(queue) > 0):
        k = queue.pop(0)
        usrmsg = k[0]
        botmsg = k[1]
        content = k[2]
        if(len(queue) > 0):
            for d in range(len(queue)):
                await queue[d][1].edit(content=f"Queued... Position: {d+1}")
    data = {}
    try:
        (prompt, tokens, temp, top_p, top_k, typ_p, min_p, rep_p, freq_p, pres_p) = await parser(content, usrmsg)
        history.append({"role": "user", "content": prompt})
        #print("Prompt: "+ prompt)
        data = {
            "mode": "instruct",
            "stream": True,
            "max_tokens": tokens,
            "temperature": temp,
            "top_p": top_p,
            "top_k": top_k,
            "typical_p": typ_p,
            "min_p": min_p,
            "repetition_penalty": rep_p,
            "frequency_penalty": freq_p,
            "presence_penalty": pres_p,
            "messages": history
        }
    except Exception as e:
        print(e)
        isGenerating = False
        return

    stream_response = requests.post(url, headers=headers, json=data, verify=False, stream=True)
    client = sseclient.SSEClient(stream_response)
    assistant_message = ''
    charcount = 0
    if (botmsg != 0):
        await botmsg.delete()
    botmsg = 0
    try:
        botmsg = await usrmsg.reply("Generating")
    except:
        botmsg = 0
    if (botmsg != 0):    
        for event in client.events():
            payload = json.loads(event.data)
            #print(payload)
            chunk = payload['choices'][0]['delta']['content']
            assistant_message += chunk
            charcount += len(chunk)
            if (chunk == ''):
                if(assistant_message == ''):
                    continue
                else:
                    charcount = 100
            if (len(assistant_message) < 2000 and charcount > 50):
                if (len(assistant_message.strip()) > 0):
                    await botmsg.edit(content=assistant_message)
                else:
                    await botmsg.edit(content="<spaces>...")
                charcount = 0
            elif(len(assistant_message) >= 2000):
                await botmsg.edit(content=assistant_message[:-len(chunk)])
                botmsg = await botmsg.channel.send(chunk + "...")
                assistant_message = chunk
                charcount = 0
    isGenerating = False
    await asyncio.sleep(1)
    if(len(queue) > 0):
        await aiGen(None)

            


def cleanString(mystr):
    mystr3 = unidecode(mystr)
    mystr2 = ''.join(letter for letter in mystr3 if (letter.isalnum() or letter==' '))
    return ' '+mystr2+' '

async def delMsg(msg):
    await asyncio.sleep(1)
    await msg.delete()

#config stuff
load_dotenv()
debug=False

intents = discord.Intents.default()
intents.message_content = True
#intents.members = True
client = discord.Client(intents = intents)
"""
##init model
tokenizer, model = load_tokenizer_and_model()
print("Model Loaded")
###init chatbot_history
#lazy way rn, may change latter to record and load back
chat_histories={}
"""
serious_channels = [974553346591576105,927849858025529474, 972963507916128297, 912240638664257553]
allowed_channels = [960797708522758184,912240638664257555,1061819577744502794,1062285903634120755, 1062057141223034971, 1062619209047232512, 1061901489402019860]
path = "/home/lawrence/chatbot/"
con = sqlite3.connect(path  + "chatbot.db")
cur = con.cursor()
haram_users = []

admin = [757788221877911613]

sexWords = []

haramUser = []
haramTwo = []

lastHaram = 0
f = open(path + "haramwords.txt", "r")
for x in f:
    sexWords.append(x.replace("\n", ""))
f.close()

f = open(path + "haramuser.txt", "r")
for x in f:
    haramUser.append(x.replace("\n", ""))
f.close()

f = open( path + "haramtwo.txt", "r")
for x in f:
    haramTwo.append(x.replace("\n", ""))
f.close()
sexRegex = []

f = open(path + "haramregex.txt", "r")
for x in f:
    sexRegex.append(x.replace("\n", ""))
f.close()

sisRegex = []

f = open(path + "haramsis.txt", "r")
for x in f:
    sisRegex.append(x.replace("\n", ""))
f.close()


f = open(path  + "catlist.txt", "r")
lines = f.readlines()

def dellast(filename):
    with open(filename, "r+", encoding = "utf-8") as file:
        file.seek(0, os.SEEK_END)
        pos = file.tell() - 1
        while pos > 0 and file.read(1) != "\n":
            pos -= 1
            file.seek(pos, os.SEEK_SET)
        if pos > 0:
            file.seek(pos, os.SEEK_SET)
            file.truncate()
async def getUsername(userid):
    res = cur.execute(f"SELECT username FROM totals WHERE id={userid}").fetchone()
    if (res is None or res[0] is None or res[0]==""):
        try:
            guild = await client.fetch_guild(912240638664257546)
            user = await guild.fetch_member(userid)
        except Exception as error:
            #print("Error: "+error)
            #user doesn't exist
            return None

        if (res is None):
            cur.execute(f"INSERT INTO totals VALUES({userid}, 0,\"{user.name}\", \"\")")
        else:
            cur.execute(f"UPDATE totals SET username=\"{user.name}\" WHERE id={userid}")
        con.commit()
        return user.name
    else:
        return res[0]

def increment(userid, word):
    res = cur.execute(f"SELECT count FROM totals WHERE id={userid}").fetchone()
    if (res is None):
        cur.execute(f"""INSERT INTO totals 
        VALUES ({userid}, 1, "", ?)""", (word,))
    else:
        cur.execute(f"UPDATE totals SET count={res[0]+1}, lastharam = ? WHERE id={userid}", (word,))
    con.commit()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def addItem(message, wordlist, wordfile,lastid):
    global lastHaram
    if (not "\"" in message.content.lower()):
        try:
            await message.reply("Wrong syntax - word must be in quotes")
        except:
            return
        return
    word = message.content.lower().split("\"")[1]
    if (word in wordlist or (word+" ") in wordlist or (" "+word) in wordlist or (" "+word+" ") in wordlist):
        try:
            await message.reply("Already in DB")
        except:
            return
        return
    else:
        wordlist.append(word)
        f=open(wordfile, "a")
        f.write(word+"\n")
        f.close()
        lastHaram = lastid
        try:
            await message.reply("Added: \""+word+"\"")
        except:
            return

@client.event
async def on_message(message):
    global lastHaram
    #print(message.content)
    if (message.content[:5] == "!gen "):
        if(message.channel.id in allowed_channels):
            await aiGen(message)
        else:
            try:
                await message.reply("Chatbot disabled in this channel")
            except:
                return
    if (message.content == "!queue"):
        r = f"Queue Length: {len(queue)}\n"
        for d in range(min(len(queue), 10)):
            pr = queue[d][2]
            if (len(pr) > 150):
                pr = pr[:150] + "..."
            r += f"{d+1}: {pr} \n"
        try:
            await message.reply(r)
        except:
            pass
        return

    if (message.author.id in admin and message.content.lower()[:9] == "!haramadd"):
        await addItem(message, sexWords, "haramwords.txt", 0)
        return
    if (message.author.id in admin and message.content.lower()[:9] == "!haramreg"):
        await addItem(message, sexRegex, "haramregex.txt", 1)
        return
    if (message.content == "!haramnum"):
        try:
            await message.reply("Haram list: "+str(len(sexWords))+", Haram regex: "+str(len(sexRegex))+ ", Haram sis: "+str(len(sisRegex)))
        except:
            pass
        return
    if (message.author.id in admin and message.content.lower()[:9] == "!haramsis"):
        await addItem(message, sisRegex, "haramsis.txt", 2)
        return
    if (message.author.id in admin and message.content.lower()[:9] == "!haramusr"):
        await addItem(message, haramUser, "haramuser.txt", 3)
        return
    if (message.author.id in admin and message.content.lower()[:9] == "!haramtwo"):
        await addItem(message, haramTwo, "haramtwo.txt", 4)
        return
    if (message.content.lower()[:10] == "!haramrand"):
        try:
            await message.reply(random.choice(lines))
        except:
            pass
        return
    if(message.author.id in admin and message.content.lower() == "!haramdel"):
        try:
            if (lastHaram == 0):
                dellast("haramwords.txt")
                await message.reply("Deleted: "+sexWords.pop())
            if (lastHaram == 1):
                dellast("haramreg.txt")
                await message.reply("Deleted: "+sexRegex.pop())
            if (lastHaram == 2):
                dellast("haramsis.txt")
                await message.reply("Deleted: "+sisRegex.pop())
            if (lastHaram == 3):
                dellast("haramuser.txt")
                await message.reply("Deleted: "+haramUser.pop())
            if (lastHaram == 4):
                dellast("haramtwo.txt")
                await message.reply("Deleted: "+haramTwo.pop())
            return
        except:
            return
    if (message.content.lower()[:10] == "!haramlist"):
        try:
            if (not "\"" in message.content.lower()):
                msg = await message.reply("Bad syntax, no quotes")
                await asyncio.sleep(3)
                await msg.delete()
                return
            word = message.content.lower().split("\"")[1]
            if (not "," in word):
                msg = await message.reply("Bad syntax, expected list number + comma + start index")
                await asyncio.sleep(3)
                await msg.delete()
                return
            list_num = word.split(",")[0].strip()
            list_ind = word.split(",")[1].strip()
            if not(list_num.isdigit() and list_ind.isdigit()):
                msg = await message.reply("Not integers")
                await asyncio.sleep(3)
                await msg.delete()
                return
            list_num = int(list_num)
            list_ind = int(list_ind)
            titles = ["Haram words", "Haram regex", "Haram sis"]
            if (list_num < 0 or list_num > 2):
                msg = await message.reply ("Bad list")
                await asyncio.sleep(3)
                await msg.delete()
                return
            reply = "Here is a list of "+str(titles[list_num]) + " starting from "+str(list_ind)+":\n"
            msg = 0
            if (list_num == 0):
                for i in range(list_ind, list_ind + 10):
                    if (i<0 or i >= len(sexWords)):
                        continue
                    reply += str(i)+". \""+sexWords[i]+"\"\n"
                msg = await message.reply(reply)
            elif (list_num == 1):
                for i in range(list_ind, list_ind + 10):
                    if (i<0 or i >= len(sexRegex)):
                        continue
                    reply += str(i)+". \""+sexRegex[i]+"\"\n"
                msg = await message.reply(reply)
            elif (list_num == 2):
                for i in range(list_ind, list_ind + 10):
                    if (i<0 or i >= len(sisRegex)):
                        continue
                    reply += str(i)+". \""+sisRegex[i]+"\"\n"
                msg = await message.reply(reply)
            else:
                msg = await message.reply("Bad list")
            await asyncio.sleep(3)
            await msg.delete()
        except:
            pass
        return
    if (message.content.lower()[:11] ==  "!haramcount"):
        try:
            m = message.content
            i = str(message.author.id)
            if ("\"" in m):
                i = m.split("\"")[1]
            if i.isdigit():
                res = cur.execute(f"SELECT count FROM totals WHERE id={i}").fetchone()
                total = 0
                if not(res is None):
                    total = res[0]
                usern = await getUsername(i)
                if (usern is None):
                    await message.reply("Invalid ID")
                    return
                await message.reply(f"User {usern} has said {total} haram things")
                return
            await message.reply("Syntax Error, put user ID in quotes")
        except:
            return
    if (message.content.lower()[:10] == "!haramlast"):
        try:
            m = message.content
            i = str(message.author.id)
            if ("\"" in m):
                i = m.split("\"")[1]
            if i.isdigit():
                res = cur.execute(f"SELECT lastharam FROM totals WHERE id={i}").fetchone()
                lh = ""
                if not(res is None):
                    lh = res[0]
                usern = await getUsername(i)
                if (usern is None):
                    await message.reply("Invalid ID")
                    return
                await message.reply(f"User {usern} has last said: {lh}")
                return
            await message.reply("Syntax Error, put user ID in quotes")
        except:
            return

    if (message.content == "!haramtop"):
        res = cur.execute("SELECT id, count FROM totals ORDER BY count DESC LIMIT 10").fetchall()
        msg = "Most haram users:\n"
        for i in res:
            user = await getUsername(i[0])
            if (user is None):
                continue
            msg = msg + f"{user}: {i[1]} harams\n"
        try:
            await message.reply(msg)
        except:
            pass
        return
    author = message.author.id
    cleanedStr = cleanString(message.content.lower())
    #stop it from fucking around if it looking at its own message
    if message.author == client.user:
        return
    if (message.channel.id in serious_channels):
        return
    #1984 feature could be added here ;)
    for word in sexWords:
        if (word in message.content.lower() or word in cleanedStr):
            increment(message.author.id, word)
            try:
                msg = await message.reply("<:gogetmarried:1204950895217999984>")
            except:
                return
            await asyncio.sleep(3)
            await msg.delete()
            return
    for reg in sexRegex:
        if (re.search(reg," "+ message.content.lower()+" ") or message.author.id in haram_users):
            increment(message.author.id, "Regex: "+reg)
            try:
                msg = await message.reply("<:gogetmarried:1204950895217999984>")
            except:
                return
            await asyncio.sleep(3)
            await msg.delete()
            return
    for reg in sisRegex:
        if (re.search(" sis.*"+reg," "+ message.content.lower()+" ") or re.search(reg+".* sis", " "+message.content.lower()+" ")):
            increment(message.author.id, "Sis: "+reg)
            try:
                msg = await message.reply("<:gogetmarried:1204950895217999984>")
            except:
                return
            await asyncio.sleep(3)
            await msg.delete()
            return
    if (str(message.author.id) in haramUser):
        for reg in haramTwo:
            if (re.search(reg," "+message.content.lower()+" ")):
                increment(message.author.id, "Haram2: "+reg)
                try:
                    msg = await message.reply("<:gogetmarried:1204950895217999984>")
                except:
                    return
                await asyncio.sleep(3)
                await msg.delete()
                return
    if (message.content.lower() in ["go get married", "gogetmarried"]):
        try:
            await message.reply("<:halal:1204949791717457940>")
        except:
            pass
        return
    if ("pipi" in message.content.lower()):
        msg = await message.channel.send("""Are you kidding ??? What the \\*\\*\\*\\* are you talking about man ? You are a biggest looser i ever seen in my life ! You was doing PIPI in your pampers when i was beating players much more stronger then you! You are not proffesional, because proffesionals knew how to lose and congratulate opponents, you are like a girl crying after i beat you! Be brave, be honest to yourself and stop this trush talkings!!! Everybody know that i am very good blitz player, i can win anyone in the world in single game! And \"w\"esley \"s\"o is nobody for me, just a player who are crying every single time when loosing, ( remember what you say about Firouzja ) !!! Stop playing with my name, i deserve to have a good name during whole my chess carrier, I am Officially inviting you to OTB blitz match with the Prize fund! Both of us will invest 5000$ and winner takes it all!

I suggest all other people who's intrested in this situation, just take a look at my results in 2016 and 2017 Blitz World championships, and that should be enough... No need to listen for every crying babe, Tigran Petrosyan is always play Fair ! And if someone will continue Officially talk about me like that, we will meet in Court! God bless with true! True will never die ! Liers will kicked off...""")
        await asyncio.sleep(0.5)
        await msg.delete()
        return
    
    if ("alpine" in message.content.lower()):
        msg = await message.channel.send('''"I use Linux as my operating system," I state proudly to the unkempt, bearded man. He swivels around in his desk chair with a devilish gleam in his eyes, ready to mansplain with extreme precision. "Actually", he says with a grin, "Linux is just the kernel. You use GNU+Linux!' I don\'t miss a beat and reply with a smirk, "I use Alpine, a distro that doesn\'t include the GNU coreutils, or any other GNU code. It\'s Linux, but it\'s not GNU+Linux." The smile quickly drops from the man\'s face. His body begins convulsing and he foams at the mouth and drops to the floor with a sickly thud. As he writhes around he screams "I-IT WAS COMPILED WITH GCC! THAT MEANS IT\'S STILL GNU!" Coolly, I reply "If windows was compiled with gcc, would that make it GNU?" I interrupt his response with "-and work is being made on the kernel to make it more compiler-agnostic. Even you were correct, you won\'t be for long." With a sickly wheeze, the last of the man\'s life is ejected from his body. He lies on the floor, cold and limp. I\'ve womansplained him to death.''')
        await asyncio.sleep(0.5)
        await msg.delete()
        return
    if ("fortune" in message.content.lower()):
        fort = subprocess.run(["fortune" , "-a"], stdout=subprocess.PIPE, text=True)
        await message.channel.send("```\n"+fort.stdout+"```")
        return
    if (message.content.lower() == "!gpustats"):
        fort = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, text=True)
        await message.channel.send("```\n"+fort.stdout+"```")
        return
    if ("asciiart" in message.content.lower()):
        fort = subprocess.run(["fortune", "mario.arteascii"], stdout=subprocess.PIPE, text=True)
        #cow = subprocess.run(["cowthink", "-n"], stdin=fort.stdout, stdout=subprocess.PIPE, text=True)
        await message.channel.send("```\n"+fort.stdout.replace("`", "\'")+"```")
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

    # femboy
    if "femboy" in message.content.lower():
        try:
            await message.reply("says the femboy")
        except:
            pass
        return

        #check if we are in the right channel
    if (message.channel.id != 912240638664257555):
        return

    #check if the chatbot trigger word, !chatbot is in the message
    if not message.content.startswith('!chatbot'):
        #if it isn't stop (return)
        return
"""
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
"""
print(os.environ.get('TOKEN'))
client.run(os.environ.get('TOKEN'))
