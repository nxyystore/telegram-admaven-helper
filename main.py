"""
Description: This script is a Discord bot that interacts with the Ad-Maven API to scrape links, retrieve analytics, and post content to both Discord and Telegram. 
It uses KeyAuth for license management^ and CapSolver for CAPTCHA solving.

Developed by: milly (milly@nemomedia.org)

Changelogs:
- 1/30/25: Complete rewrite, start of changelog
- 2/11/25: Open-sourced using MIT license

^: We don't actually use KeyAuth here, mainly since this is a closed-source project. My anticipations for this project was to allow people to pay in order to scrape links, but that idea died quickly.
"""

# Core libs
import sys
import hashlib
import os
import json
import datetime
from typing import Dict, Any
import requests

# Third-party libs
from interactions import (
    Client, Intents, listen, slash_command, SlashContext,
    OptionType, slash_option, SlashCommandChoice, Embed,
    Status, Activity, ActivityType
)
from telethon.sync import TelegramClient
import capsolver

# Listen for bot startup
# Has to be placed before the class definition, otherwise it'll complain about async/await
@listen()
async def on_ready():
    print(f"[BOT]: Ready!")

class TelegramBot:

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.bot = Client(intents=Intents.DEFAULT, activity=Activity.create("you", ActivityType.LISTENING), status=Status.IDLE)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        }
        self._setup_telegram_client()
        self._setup_capsolver()
        self._register_commands()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(os.path.join(os.path.dirname(__file__), config_path)) as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {str(e)}")

    def _setup_telegram_client(self):
        self.telegram_client = TelegramClient(
            'session_name',
            self.config['api_id'],
            self.config['api_hash']
        )

    def _setup_capsolver(self):
        capsolver.api_key = self.config['clientKey']

    def _get_checksum(self) -> str:
        with open(''.join(sys.argv), "rb") as file:
            return hashlib.md5(file.read()).hexdigest()


    # * Start registering commands *
    def _register_commands(self):

        @slash_command(name="scrapelink", description="Scrapes the specified AdMaven link")
        @slash_option(
            name="link",
            description="Link to scrape",
            required=True,
            opt_type=OptionType.STRING
        )
        async def scrapelink(ctx: SlashContext, link: str):
            await ctx.defer()
            try:
                scraped_link = await self.bypass_link(link)
                embed = Embed(
                    title="Success!",
                    description=f"{self.config['success_emoji']} Here's your scraped link :) {scraped_link}",
                    color=0x00FF00
                )
            except Exception as e:
                embed = Embed(
                    title="Error",
                    description=f"<:error:1208885864424407141> Error scraping link: {str(e)}",
                    color=0xFF0000
                )
            finally:
                await ctx.send(embed=embed)
        self.bot.add_command(scrapelink)

        @slash_command(name="analytics", description="Get Ad-Maven analytics")
        @slash_option(
            name="howlongago",
            description="How long ago do you want to go?",
            required=True,
            opt_type=OptionType.INTEGER,
            choices=[
                SlashCommandChoice(name="1 day", value=1),
                SlashCommandChoice(name="7 days", value=7),
                SlashCommandChoice(name="30 days", value=30),
                SlashCommandChoice(name="Lifetime", value=999)
            ]
        )
        @slash_option(
            name="millycut",
            description="Have the result be my cut?", # 0.40
            required=True,
            opt_type=OptionType.STRING,
            choices=[
                SlashCommandChoice(name="Yes", value="yes"),
                SlashCommandChoice(name="No", value="no")
            ]
        )
        async def analytics(ctx: SlashContext, howlongago: int, millycut: str):
            await ctx.defer()
            try:
                # Ingenious way of determining what to tell the API to query
                time_periods = {
                    1: {"api_query": "revenue_yesterday", "description": "yesterday"},
                    7: {"api_query": "revenue_last_week", "description": "last week"},
                    30: {"api_query": "revenue_last_month", "description": "last month"},
                    999: {"api_query": "revenue_overall", "description": "you've created your Ad-Maven account"}
                }

                time_period = time_periods.get(howlongago)
                
                # Somehow we broke the matrix and were able to send an invalid number
                if not time_period:
                    raise ValueError(f"Invalid time period: {howlongago}")

                auth_token = await self.get_auth_token()
                
                # Last week has to be queried by requesting the last 7 days
                if time_period["api_query"] == "revenue_last_week":
                    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
                    current_date = datetime.datetime.now() - datetime.timedelta(days=1)
                    
                    response = requests.post(
                        "https://publishers.ad-maven.com/api/reports",
                        
                        # * For some strange reason we HAVE to include every single one of these headers. If we don't, *
                        # * the API will return a 504 or 500 error *
                        headers = {
                            'accept': 'application/json, text/plain, */*',
                            'accept-language': 'en-US,en;q=0.9',
                            'authorization': auth_token,
                            'cache-control': 'no-cache',
                            'content-type': 'application/json',
                            'dnt': '1',
                            'origin': 'https://publisher.ad-maven.com',
                            'pragma': 'no-cache',
                            'priority': 'u=1, i',
                            'referer': 'https://publisher.ad-maven.com/',
                            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"macOS"',
                            'sec-fetch-dest': 'empty',
                            'sec-fetch-mode': 'cors',
                            'sec-fetch-site': 'same-site',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                        },
                        json={
                            "group_by": "report_date",
                            "tags_list": [989775, 1029573],
                            "ad_formats": [2, 51],
                            "from_date": week_ago.strftime("%Y-%m-%d"),
                            "to_date": current_date.strftime("%Y-%m-%d"),
                            "links_source": 989775
                        },
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                    amount = sum(item["total_revenue"] for item in data["message"]["results"])
                    
                # Everything else is queried thru 1 endpoint though
                else:
                    response = requests.get(
                        "https://publishers.ad-maven.com/api/revenue",
                        headers={'Authorization': auth_token},
                        timeout=10
                    )
                    response.raise_for_status()
                    amount = response.json()['message'][time_period["api_query"]] * 0.40 if millycut == "yes" else response.json()['message'][time_period["api_query"]]

                formatted_amount = "${:,.2f}".format(amount)
                
                # TODO: Clean this up
                embed = Embed(
                    title=f"{self.config['success_emoji']} Success!",
                    description=f"You've made {formatted_amount} since {time_period['description']}!",
                    color=0x00FF00
                )
            except Exception as e:
                embed = Embed(
                    title=f"{self.config['error_emoji']} Error",
                    description=f"There was an error while retrieving analytics: {str(e)}",
                    color=0xFF0000
                )
            finally:
                await ctx.send(embed=embed)
        self.bot.add_command(analytics)

        @slash_command(name="checkusage", description="Check remaining API requests")
        async def checkusage(ctx: SlashContext):
            await ctx.defer()
            try:
                response = requests.post(
                    'https://byp.tcbl.xyz/api/bypass/key/usage',
                    headers={
                        'Content-Type': 'application/json',
                        'X-API-KEY': self.config['bypass_api_key']
                    },
                    timeout=60
                )
                # Raise exception if request times out
                response.raise_for_status()
                data = response.json()

                creditsLeft = data["creditedBypasses"] - data["usedBypasses"]
                embed = Embed(
                    title=f"{self.config['success_emoji']} Success!",
                    description=(
                        f"Credits used: {data['usedBypasses']}\n"
                        f"Total credits: {data['creditedBypasses']}\n"
                        f"Remaining credits: {creditsLeft:,.2f}"
                    ),
                    color=0x00FF00
                )
            except Exception as e:
                embed = Embed(
                    title=f"{self.config['error_emoji']} Error",
                    description=f"There was an error while checking the usage: {str(e)}",
                    color=0xFF0000
                )
            finally:
                await ctx.send(embed=embed)
        self.bot.add_command(checkusage)

        @slash_command(name="manualpost", description="Manually post an embed to both Discord & Telegram!")
        @slash_option(
            name="link",
            description="The original, un-adgated link (e.g article.com/article)",
            required=True,
            opt_type=OptionType.STRING
        )
        @slash_option(
            name="name",
            description="The title of the post (i.e 'Best ways to obtain riches in 2025')",
            required=True,
            opt_type=OptionType.STRING
        )
        @slash_option(
            name="image",
            description="The image to post",
            required=True,
            opt_type=OptionType.ATTACHMENT
        )
        async def manualpost(ctx: SlashContext, link: str, name: str, image: dict):
            await ctx.defer()
            try:
                response = requests.get(image.url, timeout=10)
                # Raise exception if request times out
                response.raise_for_status()
                
                with open("media.jpg", "wb") as f:
                    f.write(response.content)
                
                payload = {
                    "content": "",
                    "embeds": [{
                        "title": f"{name} ", # This is the title, change as you'd like!
                        "description": f"{link}",
                        "color": 16711937,
                        "image": {
                            "url": f"{image.url}"
                        }
                    }]
                }
                
                await self.post_to_telegram(link, name)
                embed = Embed(
                    title=f"{self.config['success_emoji']} Success!",
                    description=f"Successfully posted! 🎉",
                    color=0x00FF00
                )
            except Exception as e:
                embed = Embed(
                    title=f"{self.config['error_emoji']} Error",
                    description=f"Uhoh! We encountered an error while posting the content: {str(e)}",
                    color=0xFF0000
                )
            finally:
                await ctx.send(embed=embed)
                if os.path.exists("media.jpg"):
                    os.remove("media.jpg")
        self.bot.add_command(manualpost)

    async def bypass_link(self, link: str) -> str:
        try:
            response = requests.post(
                "https://byp.tcbl.xyz/api/bypass/new/admaven",
                headers={
                    "accept": "application/json",
                    "X-API-KEY": self.config['bypass_api_key'],
                    "Content-Type": "application/json"
                },
                json={"url": link},
                timeout=60
            )
            # Raise exception if request times out
            response.raise_for_status()
            
            # * We can return many things, such as the final link. But due to the unreliability of it, *
            # * and the fact some post multiple folders, we just go ahead and return the intended destination *
            return response.json()["destination"]
        except Exception as e:
            raise RuntimeError(f"Failed to bypass link: {str(e)}")

    async def get_auth_token(self) -> str:
        try:
            solution = capsolver.solve({
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": "https://publisher.ad-maven.com",
                "websiteKey": "6LebMRcpAAAAAEhPNI4WR68L3Ruf2N-GwmVPcxIe",
                "pageAction": "login",
                "minScore": 0.1, # Ad-Maven is so terrible at configuring their captcha that we can use the lowest "score" (quality) possible
                "reload": self.config['reload'],
                "fetch": self.config['fetch'],
                "userAgent": self.headers['User-Agent']
            })
            
            captcha_token = solution['gRecaptchaResponse']
            payload = json.dumps(self.config['auth_payload']).replace("CAPTCHA", captcha_token)
            
            response = requests.post(
                "https://publisher.ad-maven.com/api/user",
                data=payload,
                headers=self.config['authTokenHeaders'],
                timeout=10
            )
            # Raise exception if request times out
            response.raise_for_status()
            
            # Return auth token
            return response.json()['message']['token']
        except Exception as e:
            raise RuntimeError(f"Failed to get auth token: {str(e)}")

    async def post_to_discord(self, payload: Dict[str, Any]) -> requests.Response:
        try:
            response = requests.post(
                self.config['production_webhook'],
                headers=self.config['discordHeaders'],
                json=payload,
                timeout=10
            )
            # Raise exception if request times out
            response.raise_for_status()
            
            # Return Discord's response
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to post to Discord: {str(e)}")

    async def post_to_telegram(self, link: str, title: str):
        try:
            await self.telegram_client.start()
            channel = await self.telegram_client.get_entity(self.config['telegram_channel'])
            await self.telegram_client.send_message(
                channel,
                f'{title} \n {link}', # This is what's sent to the channel, modify as you wish!
                file='media.jpg'
            )
        except Exception as e:
            raise RuntimeError(f"Failed to post to Telegram: {str(e)}")
        finally:
            await self.telegram_client.disconnect()

    def run(self):
        self.bot.start(self.config['discord_token'])



if __name__ == "__main__":
    bot = TelegramBot('config.json')
    bot.run()
