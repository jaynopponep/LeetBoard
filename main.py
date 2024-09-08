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

@bot.command()
async def leaderboard(ctx):
	try:
		embed = discord.Embed(title="Leaderboard", description="", color=discord.Color.random())
		leaderboard = ""
		with open('users.json', 'r', encoding='utf8') as f:
			users = json.load(f)
		for user_id, score in users.items():
			user = await bot.fetch_user(int(user_id))
			leaderboard += f"{user.name} - {score['submissions']}\n"
		embed.add_field(name="Highest Leetcode Submissions (all time)", value=leaderboard, inline=False)
		await ctx.channel.send(embed=embed)
	except Exception as e:
		await ctx.send(f"Error occurred: {e}")
bot.run(token)
