Description: This script is a Discord bot that interacts with the Ad-Maven API to scrape links, retrieve analytics, and post content to both Discord and Telegram. 
It uses KeyAuth for license management^ and CapSolver for CAPTCHA solving.

Developed by: milly (milly@nemomedia.org)

Changelogs:
- 1/30/25: Complete rewrite, start of changelog
- 2/11/25: Open-sourced with MIT license

^: We don't actually use KeyAuth here, mainly since this is a closed-source project. My anticipations for this project was to allow people to pay in order to scrape links, but that idea died quickly.

## This project has been open-sourced with the MIT license!

Due to a disagreement, this project has been open-sourced as to allow the management of all types of Discord servers.

This bot was intended to be used as a "helper bot", but I have discontinued the use of it. In the interest of the wider public, open-sourcing this project feels like the best move :)



## What'd with the "READ-THE-README"?

For the `bypass_api_key` field, this is an API obtained by contacting `tecno.blast303` on Discord. As of 2/11/25, this is their current contact. This is only required if you want to be able to bypass Ad-Maven links.

For `img_dump_webhook`, this is a webhook that "dumps" all the images/thumbnails to a Discord channel, then we use the link it generates as a thumbnail for the embed, that way we can embed the image in the same message. This is only required if you want to use the `/manualpost` command.

All of the other configuration options are self-explanatory if you have knowledge of Ad-Maven (https://publisher.ad-maven.com) & Discord as-well as Telegram.

