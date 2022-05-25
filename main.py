import requests
import os
import time
import threading
import discord
from discord.ext import commands
import ast
import random
import json

itemsSendingOut = None #items that are being sent out
itemsReceiving = None #items being received

stats = 0

proxies = []

with open("proxies.txt") as file_in:
  for line in file_in:
      proxies.append(line)

intents = discord.Intents().all()

client = commands.Bot(command_prefix=".", case_insensitive=True, intents=intents)

session = requests.session()

with open('config.json') as json_file:
  data = json.load(json_file)
  session.cookies['.ROBLOSECURITY'] = data['.ROBLOSECURITY']

def ableToTrade(userId):
  response = session.get(f"https://trades.roblox.com/v1/users/{userId}/can-trade-with", proxies={'http': random.choice(proxies)}).json()

  if 'errors' not in response:
    if response['canTrade'] == True:
      return True
    else:
      return False
  else:
    return False

def massSend():
  global itemSendingOut
  global itemsReceiving
  global stats

  sendingItemData = {}
  
  randomId = random.choice(itemsReceiving)
  
  requestData = session.get(f"https://inventory.roblox.com/v2/assets/{randomId}/owners?limit=100&sort=Asce", proxies={'http': random.choice(proxies)}).json()
  sendingItemData = [{'userId': 3, 'UAIDs': []}]
  
  for invData in requestData['data']:
    if ableToTrade(invData['owner']['id']):
      sendingItemData.append(
        {
         'userId': invData['owner']['id'], 
         'UAIDs': [invData['id']]
        }
      )

  nextPageCursor = requestData['nextPageCursor']
  
  while True:
    if nextPageCursor:
      requestData = session.get(f"https://inventory.roblox.com/v2/assets/{randomId}/owners?limit=100&sort=Asce&cursor={nextPageCursor}", proxies={'http': random.choice(proxies)}).json()

      for invData in requestData['data']:
        if ableToTrade(invData['owner']['id']):
          sendingItemData.append(
            {
             'userId': invData['owner']['id'], 
             'UAIDs': [invData['id']]
            }
          )
      nextPageCursor = requestData['nextPageCursor']
    else:
      break

  userAssetIdOfMyItems = []
  limitedsToGet = itemsSendingOut

  userId = session.get("https://www.roblox.com/my/settings/json").json()['UserId']
  
  limiteds = session.get(f"https://inventory.roblox.com/v1/users/{userId}/assets/collectibles?sortOrder=Asc&limit=100").json()

  for i in limiteds['data']:
    if i['assetId'] in limitedsToGet:
      if i['userAssetId'] in userAssetIdOfMyItems:
        pass
      else:
        userAssetIdOfMyItems.append(i['userAssetId'])
        limitedsToGet.remove(i['assetId'])

  count = 0

  for i in sendingItemData:
    if count != 10:
      data = {
            "offers": [
                {
                    "userId": i['userId'], #traderUserId
                    "userAssetIds": i['UAIDS'],
                    "robux": 0
                },
                {
                    "userId": userId, #My UserId
                    "userAssetIds": userAssetIdOfMyItems,
                    "robux": 0
                }
            ]
      }
    
      data = json.dumps(data)
      req = session.post("https://trades.roblox.com/v1/trades/send", data=data, proxies={'http': random.choice(proxies)})
      if "X-CSRF-Token" in req.headers:
        session.headers["X-CSRF-Token"] = req.headers["X-CSRF-Token"]
        if req.status_code == 403:
          req = session.post("https://trades.roblox.com/v1/trades/send", data=data, proxies={'http': random.choice(proxies)})
      count += 1
      stats += 1
    else:
      count = 0
      time.sleep(60)
      
      
      
  
  

@client.event
async def on_ready():
  print("Loaded successfully.")

@client.command()
async def ping(ctx):
  await ctx.send('**pong**')

@client.command()
async def setCookie(ctx, cookie):
  session.cookies['.ROBLOSECURITY'] = str(cookie)
  await ctx.send(":cookie: Successfully changed cookie.")

@client.command()
async def sendingout(ctx, *, list): 
  global itemsSendingOut
  
  itemList = ast.literal_eval(list)

  if len(itemList) < 1:
    await ctx.send("Please have a minimum of one item in your list. :pleading_face:")
    return
  
  if len(itemList) > 4:
    await ctx.send("Please only have a max of four items in your list. :pleading_face:")
    return

  itemsSendingOut = itemList
  await ctx.send("Successfully updated items that are being sent out. :white_check_mark:")

@client.command()
async def receiving(ctx, item): 
  global itemsReceiving

  itemsReceiving = item
  await ctx.send("Successfully updated the item you receive. :white_check_mark:")

@client.command()
async def masssend(ctx):
  if itemsSendingOut == None or itemsReceiving == None:
    await ctx.send("Make sure to configure your items before running this command. :rage:")

  t = threading.Thread(target=massSend)
  t.daemon = True
  t.start()

  await ctx.send("Successfully started the mass sender. :white_check_mark:")
  
@client.command()
async def stats(ctx):
  await ctx.send(f"This mass sender has sent ```{stats}```")

client.run(os.environ['token'])