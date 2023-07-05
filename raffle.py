#Note - This currently expects the admin  wallet to hold on to heroes rather than a smart contract. Will need to be modified in the future if smart contract involved
from main import client
import discord
from web3 import Web3
from discord import app_commands
from discord.ext import tasks
import json
import time
import random
from discord.utils import utcnow
import datetime
import requests


ticketPrice = 1 #ticket price in jewel
tax = 0.95
gasPrice = 0.1
#--------{REPEATED VARIABLES}----------
db_conn = 1
currency = "Jewel"
web3 = Web3(Web3.HTTPProvider(rpc))
chainId = 335
#--------------------------------------

heroCA = "0x3bcaCBeAFefed260d877dbE36378008D4e714c8E"
with open("heroabi.json") as f:
    heroABIJson = json.load(f)
heroABI = heroABIJson

heroContract = web3.eth.contract(address=heroCA, abi=heroABI)

def heroInfo(id):
    response = requests.get(f'https://heroes.defikingdoms.com/token/{id}')
    heroName = response['name']#does this need to be response.content['name'] perhaps?
    heroGen = str(response['trait_type']['Generation']['value'])
    heroLevel = str(response['trait_type']['Level']['value'])
    heroProfession = str(response['trait_type']['Profession']['value'])
    heroProfession = professionConverter(heroProfession)
    response = requests.get(f'https://heroes.defikingdoms.com/image/{id}')
    heroImage = response.content

    return heroLevel, heroImage, heroName, heroGen, heroProfession

def professionConverter(profession):
    d = {'gardening': "Gardener", 'mining': "Miner", 'foraging': "Forager", 'fishing': "Fisher"}
    if profession in d:
        return d[profession]
    else:
        return ""

cur.execute('''
CREATE TABLE raffles(
    raffleID INTEGER PRIMARY KEY AUTOINCREMENT,
    guildID INTEGER NOT NULL,
    userID INTEGER NOT NULL,
    userAddress STRING NOT NULL,
    itemID INTEGER NOT NULL,
    minTickets INTEGER NOT NULL,
    timeLeft INTEGER NOT NULL,
    ticketsSold INTEGER NOT NULL,
    completed BOOL NOT NULL,
    winnerID INTEGER
)
''')
cur.execute('''
CREATE TABLE entrants(
    ID PRIMARY KEY,
    entrantID INTEGER NOT NULL,
    entrantAddress STRING NOT NULL,
    raffleID INTEGER
    tickets INTEGER NOT NULL,
    FOREIGN KEY(raffleID) REFERENCES raffles(raffleID) ON DELETE CASCADE
)
''')

@tasks.loop()
async def yourtask():
    # if you don't care about keeping records of old tasks, remove this WHERE and change the UPDATE to DELETE
    cur = client.db.cursor()
    await cur.execute('SELECT * FROM raffles WHERE NOT completed ORDER BY timeLeft LIMIT 1')
    next_task = cur.fetchall()
    
    # if no remaining tasks, stop the loop
    if next_task is None:
        yourtask.stop()

    # sleep until the task should be done
    await discord.utils.sleep_until(next_task['end_time'])

    # do your task stuff here with `next_task`
    raffleID, guildID, creatorID, creatorAddress,nftID, minTickets, timeLeft, ticketsSold, completed, winnerID = next_task
    heroLevel, heroImage, heroName, heroGen, heroProfession = await heroInfo(nftID)
    #MIN TICKETS REACHED?
    if minTickets > ticketsSold:
        cur = client.db.cursor()
        await cur.execute('SELECT * FROM admin WHERE guildid = ?', [guildID])
        admin_results = cur.fetchall()
        if admin_results:
            guildID,admin_address,admin_pkey,logs = admin_results[0]
    #IF NO: RETURN ALL FUNDS -5% TAX AND HERO
        cur = client.db.cursor()
        await cur.execute('SELECT * FROM entrants WHERE raffleid = ?', [raffleID])
        entrants = cur.fetchall()
        for entrant in entrants:
            uID, entrantID,entrantAddress, raffleID, tickets = entrant
            value = (tickets * ticketPrice)*tax #potential issue: Admin changes ticket price while raffle is ongoing, users could get more/less back than expected
            try:
                nonce = web3.eth.get_transaction_count(admin_address)
                outgoing_tx = {
                    'nonce': nonce,
                    'to': entrantAddress,
                    'value': value,
                    'gas': 500000,
                    'gasPrice': gasPrice,
                    'chainId' : chainId
                }
                outgoing_signed_tx = web3.eth.account.sign_transaction(outgoing_tx, admin_pkey)
                outgoing_tx_hash = web3.eth.send_raw_transaction(outgoing_signed_tx.rawTransaction)
                outgoing_tx = web3.to_hex(outgoing_tx_hash)
            except ValueError as vError:
                evalError = eval(str(vError))
                if evalError["code"] == -32000:
                    outgoing_tx = "Contact Admin Team"
                    logs_channel = logs
                    channel = client.get_channel(logs_channel)
                    await channel.send(f"Raffle Error")
        try:
            transfer = heroContract.functions.transferFrom(admin_address,creatorAddress,nftID)
            tx = {
                'gasPrice': gasPrice,
                'chainId' : chainId
            }
            tx = transfer.buildTransaction(tx)
            signed_tx = web3.eth.account.sign_transaction(tx, admin_pkey)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_address = web3.to_hex(tx_hash)
        except ValueError as vError:
            evalError = eval(str(vError))
            if evalError["code"] == -32000:
                logs_channel = logs
                print(logs_channel)
                channel = client.get_channel(logs_channel)
                await channel.send(f"Failed to send hero {nftID} back to user {creatorAddress} from raffle {raffleID} (Insufficient gas). Please send when possible.")
        await db_conn.execute('UPDATE raffles SET completed = true WHERE row_id = $1', next_task['row_id'])
        #announcement embed pinging winner
    else: #IF YES:
        value = (ticketsSold*ticketPrice)*tax
        #RETRIEVE ENTRANTS FOR RAFFLE SELECTED
        cur = client.db.cursor()
        await cur.execute('SELECT * FROM entrants WHERE raffleid = ?', [raffleID])
        results = cur.fetchall()
        data = {}
        for result in results:
            uID = result['uID']
            userID = result['entrantID']
            address = result['entrantAddress']
            tickets = result[3]
            data[uID] = {"userID": userID, "address": address, "tickets": tickets}
        #WORK OUT WINNER
        winner = random.choices(list(data.keys()), weights=[d["tickets"] for d in data.values()], k=1)[0]
        # Calculate the percentage chance that the winner had to win
        winnerID = data[winner]["userID"]
        winnerAddress = data[winner]["Address"]
        winnerTickets = data[winner]["tickets"]
        winnerPercentage = round(winnerTickets / ticketsSold * 100, 2)
        print(f"<@{winnerID}> won raffle {raffleID} (Gen{heroGen} {heroProfession}) with a {winnerPercentage}% chance!")
        #SEND FUNDS TO CREATOR - TAX
        try:
            nonce = web3.eth.get_transaction_count(admin_address)
            outgoing_tx = {
                'nonce': nonce,
                'to': creatorAddress,
                'value': value,
                'gas': 500000,
                'gasPrice': gasPrice,
                'chainId' : chainId
            }
            outgoing_signed_tx = web3.eth.account.sign_transaction(outgoing_tx, admin_pkey)
            outgoing_tx_hash = web3.eth.send_raw_transaction(outgoing_signed_tx.rawTransaction)
            outgoing_tx = web3.to_hex(outgoing_tx_hash)
        except ValueError as vError:
            evalError = eval(str(vError))
            if evalError["code"] == -32000:
                outgoing_tx = "Contact Admin Team"
                logs_channel = logs
                channel = client.get_channel(logs_channel)
                await channel.send(f"Raffle Error (Creator Payout {creatorAddress})")
        #SEND NFT TO WINNER -- WIP
        try:
            transfer = heroContract.functions.transferFrom(admin_address,winnerAddress,nftID)
            tx = {
                'gasPrice': gasPrice,
                'chainId' : chainId
            }
            tx = transfer.buildTransaction(tx)
            signed_tx = web3.eth.account.sign_transaction(tx, admin_pkey)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_address = web3.to_hex(tx_hash)
        except ValueError as vError:
            evalError = eval(str(vError))
            if evalError["code"] == -32000:
                outgoing_tx = "Contact Admin Team"
                logs_channel = logs
                channel = client.get_channel(logs_channel)
                await channel.send(f"Raffle Error (NFT Payout: Hero ID {nftID} // Receiver: {creatorAddress})")
        #ANNOUNCE WINNER
    
    # UPDATE the task to mark it completed, or DELETE it
    await db_conn.execute('UPDATE raffles SET completed = true WHERE row_id = $1', next_task['row_id'])

    # add a `before_loop` and `wait_until_ready` if you need the bot to be logged in
    yourtask.start()

    # in a command that adds new task in db
    if yourtask.is_running():
        yourtask.restart()
    else:
        yourtask.start()

#--------------------------------------------------------------------------------------------------------------------------------------------------------

@client.tree.command(name="newraffle",
    description="Create a raffle in your server")
#@app_commands.default_permissions(manage_guild=True)
@app_commands.choices(choices=[
    app_commands.Choice(name="3 Days", value=3),
    app_commands.Choice(name="5 Days", value=5),
    app_commands.Choice(name="7 Days", value=7)
    ])
async def newraffle(interaction: discord.Interaction, heroID: int, minPrice:int, timelimit:app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)
    #Work out minimum tickets
    minTickets = minPrice/ticketPrice
    #endTime is current time after epoch in seconds + how many days were specified * seconds in a day
    currentTime = utcnow()
    endTime = currentTime + datetime.timedelta(days=timelimit)
    #Check if user has a wallet set up
    cur = client.db.cursor()
    cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ?", [interaction.user.id, interaction.guild_id])
    results = cur.fetchall()
    if results:
        uID, guildID, address, private_key = results[0]
        callerAddress = address
        callerPkey = private_key
    else:
        embedVar = discord.Embed(title=f"No wallet found", description=f"Ensure you have set up your wallet.", color=0xf21313)
        await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
        return
    
    cur = client.db.cursor()
    cur.execute("SELECT * FROM admin WHERE guildid = ?", [int(interaction.guild_id)])
    admin_results = cur.fetchall()
    if admin_results:
        guildID,admin_address,admin_pkey,logs = admin_results[0]
    else:
        embedVar = discord.Embed(title=f"Raffle system not established", description=f"Speak to your administrators about setting up a pool", color=0xf21313)
        await interaction.followup.send(embed=embedVar,ephemeral=True)
   
    #Check if user has hero_id in the wallet
    heroAddress = heroContract.functions.ownerOf(heroID)
    if heroAddress != address:
        embedVar = discord.Embed(title=f"You don't own this hero", description=f"Ensure you have sent the desired hero to your discord wallet before running this command.", color=0xf21313)
        await interaction.followup.send(embed=embedVar,ephemeral=True)
        return
    #Check if user has enough gas in wallet to send NFT
    #Try to send hero to guild wallet - Return error message if failed
    try:
        transfer = heroContract.functions.transferFrom(address,admin_address,heroID)
        tx = {
            'gasPrice': gasPrice,
            'chainId' : chainId
        }
        tx = transfer.buildTransaction(tx)
        signed_tx = web3.eth.account.sign_transaction(tx, callerPkey)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_address = web3.to_hex(tx_hash)
    except ValueError as vError:
        evalError = eval(str(vError))
        if evalError["code"] == -32000:
            embedVar = discord.Embed(title=f"Insufficient Funds", description=f"You do not have enough funds, including gas, to send a hero to be raffled.", color=0xFFD700)
            await interaction.followup.send(embed=embedVar,ephemeral=True)
            return
        
    #Add to raffle database:
    cur = client.db.cursor()
    cur.execute('''
    INSERT INTO raffles(
        guildID
        userID,
        userAddress,
        nftID,
        minTickets,
        timeLeft,
        ticketsSold,
        completed) VALUES (?,?,?,?,?,?,?)
    ''', [interaction.guild.id,interaction.user.id,address,heroID,minTickets,endTime,0,False])

    embedVar = discord.Embed(title=f"Raffle created!", description="", color=0x00ff00)
    embedVar.add_field(name=f"Hero ID: {heroID}", value=f"{tx_address}", inline=False)
    embedVar.add_field(name="Transaction hash: ", value=f"{tx_address}", inline=False)
    try:
        heroLevel, heroImage, heroName, heroGen, heroProfession = await heroInfo(heroID)
        embedVar.set_image(heroImage)
    except:
        pass

    await interaction.followup.send(embed=embedVar,ephemeral=True)

#--------------------------------------------------------------------------------------------------------------------------------------------------------

@client.tree.command(name="enterraffle",
    description="Join a raffle")
#@app_commands.default_permissions(manage_guild=True)
async def enterraffle(interaction: discord.Interaction, raffleID: int, tickets:int):
    await interaction.response.defer(ephemeral=True)
    value = float(tickets*ticketPrice) #total price in selected token
    #Find the raffle that was designated
    cur = client.db.cursor()
    cur.execute("SELECT * FROM raffles WHERE guildid = ? AND raffleid = ? LIMIT 1", [interaction.guild_id,raffleID])
    results = cur.fetchall()
    if results:
        raffleID, guildID, creatorID, creatorAddress,nftID, minTickets, timeLeft, ticketsSold, completed, winnerID = results[0]
    else:
        embedVar = discord.Embed(title=f"Raffle not found", description=f"No raffle was found with the ID provided.", color=0xFFD700)
        await interaction.followup.send(embed=embedVar,ephemeral=True)
    if completed:
        embedVar = discord.Embed(title=f"This raffle has ended", description=f"Winner: {winnerID}", color=0xFFD700) #HERE
        await interaction.followup.send(embed=embedVar,ephemeral=True)
    #Check if user has a wallet set up
    cur = client.db.cursor()
    cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ?", [interaction.user.id, interaction.guild_id])
    results = cur.fetchall()
    if results:
        uID, guildID, address, private_key = results[0]
        callerAddress = address
        callerPkey = private_key
    else:
        embedVar = discord.Embed(title=f"No wallet found", description=f"Ensure you have set up your wallet.", color=0xf21313)
        await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
        return
    #Check if user has enough funds & gas in wallet for transaction
    balance = web3.eth.get_balance(callerAddress)
    if balance < value + gasPrice:
        embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Please add more funds before trying this transaction again.", color=0xf21313)
        await interaction.response.send_message(embed=embedVar,ephemeral=True)
    #Try to send funds - Return error message if failed
    cur = client.db.cursor()
    cur.execute("SELECT * FROM admin WHERE guildid = ?", [int(interaction.guild_id)])
    admin_results = cur.fetchall()
    if admin_results:
        guildID,admin_address,admin_pkey,logs = admin_results[0]
        try:
            nonce = web3.eth.get_transaction_count(callerAddress)
            incoming_tx = {
                'nonce': nonce,
                'to': admin_address,
                'value': value,
                'gas': 500000,
                'gasPrice': 30000000000,
                'chainId' : chainId
            }
            incoming_signed_tx = web3.eth.account.sign_transaction(incoming_tx, callerPkey)
            incoming_tx_hash = web3.eth.send_raw_transaction(incoming_signed_tx.rawTransaction)
            incoming_tx = web3.to_hex(incoming_tx_hash)
        except ValueError as vError:
            evalError = eval(str(vError))
            if evalError["code"] == -32000:
                embedVar = discord.Embed(title=f"Insufficient Funds", description="Not enough funds to cover amount + gas. Please top up your account before trying to flip again", color=0xFFD700)
                await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
                return
    heroLevel, heroImage, heroName, heroGen, heroProfession = await heroInfo(nftID)
    #On success: Add entry to database
    cur = client.db.cursor()
    results = cur.execute('SELECT id FROM entrants WHERE userID = ?', (uID))
    row = results.fetchone()
    if row: #Check if they already purchased tickets, if so UPDATE
        cur = client.db.cursor()
        cur.execute('UPDATE entrants SET tickets = ? WHERE userID = ?', ((row['tickets'] + tickets), uID))
        embedVar = discord.Embed(title=f"Additional tickets bought for raffle {raffleID}", description="", color=0x00ff00)
        embedVar.add_field(name=f"Hero ID: {nftID}", value=f"Gen {heroGen} {heroProfession}", inline=False)
        embedVar.add_field(name=f"Tickets Purchased", value=f"{tickets}", inline=False)
        embedVar.add_field(name="Transaction hash: ", value=f"{incoming_tx}", inline=False)
    cur = client.db.cursor()
    cur.execute('''
    INSERT INTO entrants(
        ID
        userID,
        userAddress,
        raffleID,
        tickets,
        ) VALUES (?,?,?,?)
    ''', [interaction.user.id,address,raffleID,tickets])
    # Return ticket numbers & transaction ID
    embedVar = discord.Embed(title=f"Raffle Entered!", description="", color=0x00ff00)
    embedVar.add_field(name=f"Hero ID: {nftID}", value=f"Gen {heroGen} {heroProfession}", inline=False)
    embedVar.add_field(name=f"Tickets Purchased", value=f"{tickets}", inline=False)
    embedVar.add_field(name="Transaction hash: ", value=f"{incoming_tx}", inline=False)
#--------------------------------------------------------------------------------------------------------------------------------------------------------

@client.tree.command(name="raffleinfo",
    description="View a specific raffle's details")
#@app_commands.default_permissions(manage_guild=True)
async def raffleinfo(interaction: discord.Interaction, raffleID: int):
    #SELECT raffleid from raffles table
    await interaction.response.defer(ephemeral=True)
    cur = client.db.cursor()
    cur.execute("SELECT * FROM raffles WHERE guildid = ? AND raffleid = ? LIMIT 1", [interaction.guild_id,raffleID])
    results = cur.fetchall()
    if results:
        raffleid, guildID, userID, userAddress,nftID, minTickets, timeLeft, ticketsSold, completed, winnerID = results[0]
    else:
        embedVar = discord.Embed(title=f"Raffle not found", description=f"No raffle was found with the ID provided.", color=0xFFD700)
        await interaction.followup.send(embed=embedVar,ephemeral=True)
    if completed:
        embedVar = discord.Embed(title=f"Raffle {raffleID}", description=f"Status: Completed", color=0x00ff00)
        embedVar.add_field(name=f"Hero: {nftID}", value=f"", inline=False)
        try:
            heroLevel, heroImage, heroName, heroGen, heroProfession = await heroInfo(nftID)
            embedVar.add_field(name=f"{heroName}", value=f"Gen {heroGen} {heroProfession}", inline=False)
            embedVar.set_image(heroImage)
        except:
            pass
        embedVar.add_field(name=f"Sold for {ticketsSold * ticketPrice} {currency}!", value=f"", inline=False)
        await interaction.followup.send(embed=embedVar,ephemeral=True)

    embedVar = discord.Embed(title=f"Raffle {raffleID}", description=f"Status: Running", color=0x00ff00)
    embedVar.add_field(name=f"Hero: {nftID}", value=f"", inline=False)
    try:
        heroLevel, heroImage, heroName, heroGen, heroProfession = await heroInfo(nftID)
        embedVar.add_field(name=f"{heroName}", value=f"Gen {heroGen} {heroProfession}", inline=False)
        embedVar.set_image(heroImage)
    except:
        pass
    embedVar.add_field(name=f"Tickets sold: {ticketsSold}", value=f"", inline=False)
    embedVar.add_field(name=f"Minimum tickets: {minTickets}", value=f"", inline=False)
    await interaction.followup.send(embed=embedVar,ephemeral=True)
    #Display embed with details of raffle including hero, hero image, current tickets bought, minimum tickets for draw
    return

#--------------------------------------------------------------------------------------------------------------------------------------------------------

@client.tree.command(name="rafflelist",
    description="View a list of currently active raffles in your server.")
#@app_commands.default_permissions(manage_guild=True)
async def rafflelist(interaction: discord.Interaction):
    count = 1
    await interaction.response.defer(ephemeral=True)
    cur = client.db.cursor()
    cur.execute("SELECT * FROM raffles WHERE guildid = ? AND completed = ?", [interaction.guild_id, False])
    results = cur.fetchall()

    if results: #if results return embed of current active raffles
        embedVar = discord.Embed(title=f"Active raffles", description=f"", color=0x75e6da)
        for result in results:
            raffleid, guildID, userID, userAddress,nftID, minTickets, timeLeft, ticketsSold, completed = result[0]
            heroLevel, heroImage, heroName, heroGen, heroProfession = await heroInfo(nftID)
            embedVar.add_field(name=f"{count}. Hero: {nftID} (Level {heroLevel} Gen {heroGen} {heroProfession})", value=f"", inline=False)
            count += 1
    else:
        embedVar = discord.Embed(title=f"No active raffles", description=f"If you believe this is a mistake, please contact your administrator.", color=0xFFD700)
        await interaction.followup.send(embed=embedVar,ephemeral=True)
    

    #ISSUES:
    #Find a way to make an embed list that goes between pages if multiple raffles active