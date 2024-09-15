import discord
from discord.ext import commands
import json
import os
import asyncio
from playwright.async_api import async_playwright

bot = commands.Bot(command_prefix="lc ", intents=discord.Intents.all())

token = os.getenv("token")

def extract_problem(link):
	try:
		if "/submissions" in link and "/problems/" in link:
			problem = (link.split("/problems/")[1].split("/submissions")[0]).replace("-", " ")
		else:
			return None
		return problem
	except IndexError:
		return None

async def validate_page(link):
	async with async_playwright() as p:
		browser = await p.chromium.launch(headless=True)
		page = await browser.new_page()
		await page.goto(link)
		page_content = await page.content()
		print(page_content)
		#try:
			#await page.wait_for_selector('text=Accepted', timeout=10000)
			#await browser.close()
			#return True
		#except Exception:
			#await browser.close()
			#return False
		#page_content = await page.content()
		#if "Accepted" not in page_content:
			#return False
		#await browser.close()
		return True

@bot.command()
async def submit(ctx, link):
	try:
		is_valid = await validate_page(link)
		if not is_valid:
			await ctx.send("Not a valid submission link or problem")
			return
		if os.path.exists('users.json'):
			with open('users.json', 'r', encoding='utf8') as f:
				users = json.load(f)
		else:
			users = {}
		problem_name = extract_problem(link)
		# read users & problem name^

		if problem_name is None:
			await ctx.send("Wrong link format, resubmit the link that contains the submission ID")
			return
		# handle submission, retrieve problem name

		if str(ctx.author.id) in users:
			users[str(ctx.author.id)]['submissions'] += 1
			if 'links' in users[str(ctx.author.id)] and 'problems' in users[str(ctx.author.id)]:
				users[str(ctx.author.id)]['links'].append(link)
				if problem_name in users[str(ctx.author.id)]['problems']:
					await ctx.send("Cannot submit the same problem more than once! Nice try Diddy")
					return
				else:
					users[str(ctx.author.id)]['problems'].append(problem_name)
			elif 'links' not in users[str(ctx.author.id)]:
				users[str(ctx.author.id)]['links'] = [link]
			else:
				users[str(ctx.author.id)]['problems'] = [problem_name]
		else:
			users[str(ctx.author.id)] = {
				'submissions': 1,
				'links': [link],
				'problems': [problem_name]
			}
		# handle new data in json^

		with open('users.json', 'w', encoding='utf8') as f:
			json.dump(users,f,sort_keys=True,indent=4,ensure_ascii=False)
		subs = users[str(ctx.author.id)]['submissions']
		await ctx.channel.send(f"{ctx.author.name} has solved {subs} leetcode problems!")
	except Exception as e:
		await ctx.send(f"An error occurred: {e}")

@bot.command()
async def leaderboard(ctx):
    try:
        embed = discord.Embed(title="Leaderboard", description="", color=discord.Color.random())
        leaderboard = ""
        
        with open('users.json', 'r', encoding='utf8') as f:
            users = json.load(f)
        
        sorted_users = sorted(users.items(), key=lambda x: x[1]['submissions'], reverse=True)
        
        for user_id, score in sorted_users:
            user = await bot.fetch_user(int(user_id))
            leaderboard += f"{user.name} - {score['submissions']}\n"
        
        embed.add_field(name="Highest Leetcode Submissions (all time)", value=leaderboard, inline=False)
        
        await ctx.channel.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"Error occurred: {e}")

@bot.command()
async def problems(ctx):
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf8') as f:
                users = json.load(f)
        if 'problems' not in users[str(ctx.author.id)]
            await ctx.channel.send("You have not solved any problems yet!")
        problems = ""
        for i in range(len(users[str(ctx.author.id)]['problems'])):
            problems += users[str(ctx.author.id)]['problems'][i] + ", "
        problems = problems.rstrip(", ")
        await ctx.channel.send(f"{ctx.author.name} has solved: {problems}")
        print(problems)
    except Exception as e:
        print(e)
bot.run(token)
