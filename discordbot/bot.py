import discord
from discord.ext import commands
import json
import re
import openai
import os

# ====== CONFIG ======
DISCORD_TOKEN = "MTQwNTk1OTY5NDM0NTgzMDQ3MA.GOGhUN.Is_Nc8QqyII0EqLqFi5C5pE7lwN2kz5KbuLRbY"
OPENAI_API_KEY = "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"
BOT_NAME = "support"
TRIGGERS_FILE = "triggers.json"

openai.api_key = OPENAI_API_KEY

# ====== BOT SETUP ======
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix=".", intents=intents)

# ====== TRIGGERS STORAGE ======
if not os.path.exists(TRIGGERS_FILE):
    with open(TRIGGERS_FILE, "w") as f:
        json.dump({}, f)

with open(TRIGGERS_FILE, "r") as f:
    triggers = json.load(f)

def save_triggers():
    with open(TRIGGERS_FILE, "w") as f:
        json.dump(triggers, f, indent=4)

def is_whole_word_in_text(word, text):
    # Escapes word so regex special chars in trigger don't break
    return re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE) is not None

async def is_reply_to_bot(message):
    if message.reference:
        replied_msg = await message.channel.fetch_message(message.reference.message_id)
        return replied_msg.author.id == bot.user.id
    return False

# ====== COMMANDS ======
@bot.command()
async def addtrigger(ctx, trigger: str, *, response: str):
    triggers[trigger.lower()] = response
    save_triggers()
    await ctx.send(f"✅ trigger '{trigger}' added with response: {response}")

@bot.command()
async def removetrigger(ctx, *, trigger: str):
    if trigger.lower() in triggers:
        del triggers[trigger.lower()]
        save_triggers()
        await ctx.send(f"🗑 trigger '{trigger}' removed")
    else:
        await ctx.send(f"⚠️ trigger '{trigger}' not found")

@bot.command()
async def triggerslist(ctx):
    if not triggers:
        await ctx.send("📭 no triggers added yet")
    else:
        trigger_list = "\n".join([f"**{t}** → {r}" for t, r in triggers.items()])
        await ctx.send(f"📜 **Trigger List:**\n{trigger_list}")

# ====== AI RESPONSE ======
async def get_ai_response(user_message):
    prompt = f"reply casually in lowercase without punctuation and sound like a friendly discord friend: {user_message}"
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "you are a friendly discord friend who replies casually in lowercase with no punctuation"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(error talking to ai: {e})"

# ====== MESSAGE HANDLING ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    msg_lower = message.content.lower()

    # 1. Trigger word/phrase match
    for trigger_word, trigger_response in triggers.items():
        if is_whole_word_in_text(trigger_word, msg_lower):
            await message.channel.send(trigger_response)
            return

    # 2. Reply to bot
    if await is_reply_to_bot(message):
        ai_reply = await get_ai_response(message.content)
        await message.channel.send(ai_reply)
        return

    # 3. Bot name mention directly
    if BOT_NAME in msg_lower and (
        msg_lower.startswith(BOT_NAME) or
        msg_lower.endswith(BOT_NAME) or
        msg_lower.strip() == BOT_NAME
    ):
        ai_reply = await get_ai_response(message.content)
        await message.channel.send(ai_reply)
        return

    await bot.process_commands(message)

# ====== START BOT ======
bot.run(DISCORD_TOKEN)
