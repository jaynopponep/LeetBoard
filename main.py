import discord
from discord.ext import commands
import json
import os

bot = commands.Bot(command_prefix="lc ", intents=discord.Intents.all())

with open("token.txt") as file:
	token = file.read()

@bot.command()
async def submit(ctx, arg):
	try:
		if os.path.exists('users.json'):
			with open('users.json', 'r', encoding='utf8') as f:
				user = json.load(f)
		else:
			user = {}
		if str(ctx.author.id) in user:
			user[str(ctx.author.id)]['submissions'] += 1
		else:
			user[str(ctx.author.id)] = {'submissions': 1}
		with open('users.json', 'w', encoding='utf8') as f:
			json.dump(user,f,sort_keys=True,indent=4,ensure_ascii=False)
		subs = user[str(ctx.author.id)]['submissions']
		await ctx.channel.send(f"{ctx.author.name} now has {subs} submissions")
	except Exception as e:
		await ctx.send(f"An error occurred: {e}")

bot.run(token)
