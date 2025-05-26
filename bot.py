import discord
from discord.ext import commands
import json
import requests
from discord.ext.commands import Bot
import asyncio
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_reaction_add(reaction, user):
    print(f"✅ 리액션 감지됨: {reaction.emoji} by {user}")

def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()  # 요청 실패하면 에러 발생
    return response.json()

URL="https://raw.githubusercontent.com/hhkittty/wbpj/refs/heads/main/webtoon.json" 
webtoons=fetch_json(URL)

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 준비되었습니다!')

@bot.command()
async def 추천(ctx, *장르들):
    webtoons=fetch_json(URL)
    if not 장르들:
        await ctx.send("장르는 하나이상😠")
        return

    결과 = []

    for 웹툰 in webtoons:
        if all(장르 in 웹툰["장르"] for 장르 in 장르들):
            장르_문자열=", ".join(웹툰["장르"])
            결과.append(f'📘 {웹툰["제목"]}|{장르_문자열} - {웹툰["코멘트"]}')

    if 결과:
        await ctx.send("\n".join(결과))
    else:
        await ctx.send("그건 없는데 😢")

@bot.command()
async def 웹툰(ctx):
    웹툰목록 = sorted(fetch_json(URL), key=lambda x: x["제목"])  # 최신 목록 불러오기 &가나다 순 정렬렬

# 가장 긴 제목의 길이 측정
    max_title_len = max(len(웹툰["제목"]) for 웹툰 in 웹툰목록)

    def 웹툰리스트(웹툰):
        제목 = 웹툰["제목"].ljust(max_title_len)  # 길이 맞춰 왼쪽 정렬
        장르 = ", ".join(웹툰["장르"])
        코멘트 = 웹툰["코멘트"]
        return f'{제목} | {장르} - {코멘트}'
    
    웹툰목록열 = [웹툰리스트(웹툰) for 웹툰 in 웹툰목록]

    페이지당개수 = 20
    총페이지 = (len(웹툰목록열) - 1) // 페이지당개수 + 1
    현재페이지 = 0

    def get_page_text(페이지):
        시작 = 페이지 * 페이지당개수
        끝 = 시작 + 페이지당개수
        리스트 = 웹툰목록열[시작:끝]
        텍스트 = "\n".join(f"{시작 + i + 1}. {제목}" for i, 제목 in enumerate(리스트))
        return f"**📄 웹툰 목록 (페이지 {페이지+1}/{총페이지})**\n\n{텍스트}"

    메시지 = await ctx.send(get_page_text(현재페이지))
    await 메시지.add_reaction("◀️")
    await 메시지.add_reaction("▶️")

    def 체크(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == 메시지.id

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=체크)

            if str(reaction.emoji) == "▶️" and 현재페이지 < 총페이지 - 1:
                현재페이지 += 1
                await 메시지.edit(content=get_page_text(현재페이지))
                try:
                    await 메시지.remove_reaction(reaction, user)
                except discord.errors.Forbidden:
                    pass  # 권한 없으면 무시
            elif str(reaction.emoji) == "◀️" and 현재페이지 > 0:
                현재페이지 -= 1
                await 메시지.edit(content=get_page_text(현재페이지))
                try:
                    await 메시지.remove_reaction(reaction, user)
                except discord.errors.Forbidden:
                    pass
            else:
                try:
                    await 메시지.remove_reaction(reaction, user)
                except discord.errors.Forbidden:
                    pass

        except asyncio.TimeoutError:
            try:
              await 메시지.delete()
            except discord.errors.Forbidden:
              pass
            break
 
@bot.command()
async def 장르(ctx):
    webtoons=fetch_json(URL)
    장르목록=set()
    for 웹툰 in webtoons:
        for 장르 in 웹툰["장르"]:
            장르목록.add(장르)
    장르리스트=sorted(list(장르목록))
    장르열 = "\n".join(장르리스트)

    await ctx.send(f'**장르 목록**:\n```{장르열}```')
 

@bot.command()
async def 도움말(ctx):
    help_text="""
**명령어 목록**
 `!웹툰`
  웹툰 전부 보여줄게

 `!장르`
  전체 장르 종류 보여줄게

 `!추천 장르1`
  해당 장르인 웹툰 추천해줄게 (장르 1개 이상)

 `!도움말`
  지금 바로 이거
 """
    await ctx.send(help_text)

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run('token')