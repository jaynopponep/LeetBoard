import discord
from discord.ext import commands
import json
import os
import requests
import asyncio
import re


class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix="lc ", intents=intents, **kwargs)

    async def on_ready(self):
        print(f"Logged in as {self.user.name}")
        # this is higly not recommended, instead try to make a separate command and only allow the server owner/bot owner to run this
        # await self.tree.sync()
        # print(f"Commands synced: {self.commands}")


intents = discord.Intents.all()
bot = Bot(intents=intents)

# if the user provides an argument like "--test", then use the test_token env variable
# otherwise, use the actual token
if len(os.sys.argv) > 1 and os.sys.argv[1] == "--test":
    token = os.getenv("test_token")
else:
    token = os.getenv("token")


# TODO: extract helper functions to a separate file
def extract_problem(link):
    try:
        if "/submissions" in link and "/problems/" in link:
            problem = (link.split("/problems/")[1].split("/submissions")[0]).replace("-", " ")
        else:
            return None
        return problem
    except IndexError:
        return None

def get_difficulty(link):
    title_slug = link.split('/problems/')[1].split('/')[0]
    url = "https://leetcode.com/graphql"
    query = """
    query getProblemDetails($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        title
        difficulty
      }
    }
    """
    variables = {
            "titleSlug": title_slug
    }
    response = requests.post(url=url, json={"query": query, "variables": variables})
    if response.status_code == 200:
        data = response.json()
        difficulty=data['data']['question']['difficulty']
        return difficulty
    else:
        return f"An error occurred: {response.text}"


async def validate_page(link):
    return True


#    async with async_playwright() as p:
#        browser = await p.chromium.launch(headless=True)
#        page = await browser.new_page()
#        await page.goto(link)
#        page_content = await page.content()
#        print(page_content)
#        #try:
#            #await page.wait_for_selector('text=Accepted', timeout=10000)
#            #await browser.close()
#            #return True
#        #except Exception:
#            #await browser.close()
#            #return False
#        #page_content = await page.content()
#        #if "Accepted" not in page_content:
#            #return False
#        #await browser.close()
#        return True

@bot.tree.command(name="submit", description="Submit a leetcode problem link")
async def submit(interaction: discord.Interaction, link: str):
    try:
        is_valid = await validate_page(link)
        if not is_valid:
            await interaction.send("Not a valid submission link or problem")
            return
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf8') as f:
                users = json.load(f)
        else:
            users = {}
        problem_name = extract_problem(link)
        # read users & problem name^
        difficulty = get_difficulty(link)
        score = 0
        if difficulty == "Easy":
            score = 1
        elif difficulty == "Medium":
            score = 2
        else:
            score = 4
        if problem_name is None:
            await interaction.response.send_message(
                "Wrong link format, resubmit the link that contains the submission ID")
            return
        # handle submission, retrieve problem name

        if str(interaction.user.id) in users:
            users[str(interaction.user.id)]['submissions'] += score
            if 'links' in users[str(interaction.user.id)] and 'problems' in users[str(interaction.user.id)]:
                users[str(interaction.user.id)]['links'].append(link)
                if problem_name in users[str(interaction.user.id)]['problems']:
                    await interaction.response.send_message(
                        "Cannot submit the same problem more than once! Nice try Diddy")
                    return
                else:
                    users[str(interaction.user.id)]['problems'].append(problem_name)
            elif 'links' not in users[str(interaction.user.id)]:
                users[str(interaction.user.id)]['links'] = [link]
            else:
                users[str(interaction.user.id)]['problems'] = [problem_name]
        else:
            users[str(interaction.user.id)] = {
                'submissions': score,
                'links': [link],
                'problems': [problem_name]
            }
        # handle new data in json^

        with open('users.json', 'w', encoding='utf8') as f:
            json.dump(users, f, sort_keys=True, indent=4, ensure_ascii=False)
        subs = users[str(interaction.user.id)]['submissions']
        await interaction.response.send_message(
            f"{difficulty} problem submitted: {link}. \n{interaction.user.name}'s score is now {subs}!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="Leaderboard", description="", color=discord.Color.random())
        leaderboard = ""

        with open('users.json', 'r', encoding='utf8') as f:
            users = json.load(f)

        sorted_users = sorted(users.items(), key=lambda x: x[1]['submissions'], reverse=True)

        # working implementation for top 3 (emoji addition) 
        count = 1

        for user_id, score in sorted_users:
            user = await bot.fetch_user(int(user_id))
            if count == 1:
                leaderboard += f"🌟{user.name} - {score['submissions']}\n"
                count += 1
            elif count == 2:
                leaderboard += f"⭐{user.name} - {score['submissions']}\n"
                count += 1
            elif count == 3:
                leaderboard += f"✨{user.name} - {score['submissions']}\n"
                count += 1
            else:
                leaderboard += f"{user.name} - {score['submissions']}\n"

        embed.add_field(name="Highest Leetcode Scores (All Time)", value=leaderboard, inline=False)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"Error occurred: {e}")


@bot.tree.command(name="stats", description="Get your leetcode stats")
async def stats(interaction: discord.Interaction):
    try:
        url = "https://leetcode.com/graphql"
        query = """
            query getUserProfile($username: String!) {
                matchedUser(username: $username) {
                    username
                    submitStats: submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                        submissions
                    }
                    }
                }
                }
        """
        with open('users.json', 'r', encoding='utf8') as f:
            users = json.load(f)
        username = users[str(interaction.user.id)]['username']
        variables = {
            "username": username
        }
        response = requests.post(url=url, json={"query": query, "variables": variables})
        if response.status_code == 200:
            data = response.json()
            # make a nice embed
            embed = discord.Embed(title=f"{username}'s Leetcode Stats", description="", color=discord.Color.random())
            for difficulty in data['data']['matchedUser']['submitStats']['acSubmissionNum']:
                embed.add_field(name=f"{difficulty['difficulty']} problems",
                                value=f"Submissions: {difficulty['submissions']}, Count: {difficulty['count']}",
                                inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            interaction.response.send_message(f"An error occurred: {response.text}")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="register")
async def register(interaction: discord.Interaction, username: str):
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf8') as f:
                users = json.load(f)
        else:
            users = {}
        user_id = str(interaction.user.id)
        if user_id in users:
            users[user_id]['username'] = username
        else:
            users[user_id] = {
                'submissions': 0,
                'links': [],
                'problems': [],
                'username': username
            }
        with open('users.json', 'w', encoding='utf8') as f:
            json.dump(users, f, sort_keys=True, indent=4, ensure_ascii=False)
        await interaction.response.send_message(f"{interaction.user.name} has been registered with username {username}")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")

@bot.tree.command(name="suggest")
async def suggest(interaction: discord.Interaction, suggestion: str):
    try:
        if os.path.exists('suggestions.json'):
            with open('suggestions.json', 'r', encoding='utf8') as f:
                suggestions = json.load(f)
        else:
            suggestions = {}
        username = str(interaction.user.name)
        if username in suggestions:
            suggestions[username]['suggestions'].append(suggestion)
        else:
            suggestions[username] = {
                    'suggestions': [suggestion]
            }
        with open('suggestions.json', 'w', encoding='utf8') as f:
            json.dump(suggestions, f, sort_keys=True, indent=4, ensure_ascii=False)
        await interaction.response.send_message(f"Submission received. Thank you :)")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")

@bot.command()
async def sync(ctx):
    try:
        await bot.tree.sync()
        await ctx.send("Commands synced!")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
async def problems(ctx):
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf8') as f:
                users = json.load(f)
        if 'problems' not in users[str(ctx.author.id)]:
            await ctx.channel.send("You have not solved any problems yet!")
        problems = ""
        for i in range(len(users[str(ctx.author.id)]['problems'])):
            problems += users[str(ctx.author.id)]['problems'][i] + ", "
        problems = problems.rstrip(", ")
        await ctx.channel.send(f"{ctx.author.name} has solved: {problems}")
        print(problems)
    except Exception as e:
        print(e)


@bot.listen()
async def on_message(message):
    poll = r'y/n'
    versus = r'v/s'
    if re.search(poll, message.content):
        await message.add_reaction(u"\u2B06\uFE0F")
        await message.add_reaction(u"\u2B07\uFE0F")
    if re.search(versus, message.content):
        await message.add_reaction(u"\u2B05")
        await message.add_reaction(u"\u27A1")

bot.run(token)
