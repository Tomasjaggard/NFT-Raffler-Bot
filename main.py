import discord
import pymongo
import asyncio
import sqlite3
from discord import app_commands
from discord import message
from discord.utils import utcnow
from discord.ext import commands
from discord.ext import tasks
from web3 import Web3
from eth_account import Account
import secrets
import json
import random
import requests
import asqlite
import queue
from dataclasses import dataclass
from datetime import datetime, timedelta
from web3.middleware import geth_poa_middleware
from classList import Hero, Gas, Admin, User, Raffle, Entrant


nativeToken = "0xd00ae08403B9bbb9124bB305C09058E32C39A48c"
tokenAbi = '[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"guy","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":true,"internalType":"address","name":"dst","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"src","type":"address"},{"indexed":false,"internalType":"uint256","name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"guy","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"src","type":"address"},{"internalType":"address","name":"dst","type":"address"},{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"uint256","name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}]'
#rpc = "https://subnets.avax.network/defi-kingdoms/dfk-chain-testnet/rpc"#"https://api.avax-test.network/ext/bc/C/rpc"
rpc = "https://subnets.avax.network/defi-kingdoms/dfk-chain/rpc"
ownerrole = "Owner"
AdminId = 318090426315833344
Adminrole = "Owner","Admin"
Adminwallet = "Admin"
#chainId = 335 #AVAX FAUCET: 43113
chainId = 53935
intents = discord.Intents.default()
intents.message_content = True
activity = discord.Activity(type=discord.ActivityType.competing, name="DFKDuels")
intents.members = True
currency = "Jewel"
gasCurrency = "Jewel"
ticketPrice = 0.001 #ticket price in jewel
tax = 0.95
web3 = Web3(Web3.HTTPProvider(rpc))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
cooldownTime = 5
#HeroCA = "0x3bcaCBeAFefed260d877dbE36378008D4e714c8E"
heroCA = "0xEb9B61B145D6489Be575D3603F4a704810e143dF"
with open("Heroabi.json") as f:
    HeroABIJson = json.load(f)
heroABI = HeroABIJson

heroContract = web3.eth.contract(heroCA, abi=heroABI)

#--------{gas PRICES}----------

web3.eth.send_transaction

def read_token():
    with open("token.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip()

class aclient(discord.Client):
    def __init__(self,*,activity: discord.Activity,intents: discord.Intents):
        super().__init__(activity=activity,intents=intents)
        self.synced = False
        self.tree = app_commands.CommandTree(self)

    async def create_table(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS users(
                uid integer PRIMARY KEY,
                guildid integer NOT NULL,
                address text NOT NULL,
                key text NOT NULL
            )
            ''')
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS admin(
                guildid INTEGER PRIMARY KEY,
                pooladdress TEXT NOT NULL,
                poolkey TEXT NOT NULL,
                raffleaddress TEXT NOT NULL,
                rafflekey TEXT NOT NULL,
                announcements INTEGER NOT NULL,
                logs INTEGER NOT NULL,
                pause BOOL NOT NULL
            )
            ''')
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS raffles(
                raffleID INTEGER PRIMARY KEY AUTOINCREMENT,
                guildID INTEGER NOT NULL,
                userID INTEGER NOT NULL,
                userAddress STRING NOT NULL,
                nftID INTEGER NOT NULL,
                minTickets INTEGER NOT NULL,
                timeLeft INTEGER NOT NULL,
                ticketsSold INTEGER NOT NULL,
                completed BOOL NOT NULL,
                winnerID INTEGER
            )
            ''')
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS entrants(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                entrantID INTEGER NOT NULL,
                entrantAddress STRING NOT NULL,
                raffleID INTEGER,
                tickets INTEGER NOT NULL,
                FOREIGN KEY(raffleID) REFERENCES raffles(raffleID) ON DELETE CASCADE
            )
            ''')
            await conn.commit()

    async def setup_hook(self):
        self.pool = await asqlite.create_pool('database.db')
        await self.create_table()
        print("Database Initialised")
        print(f"We have logged in as {self.user}.")
        # yourtask.start()

client = aclient(activity=activity,intents=intents)
dict_queue = queue.Queue()

@client.event
async def on_ready():
    print('Bot is ready!')
    await client.wait_until_ready()
    yourtask.start()

class Cooldown:
    def __init__(self):
        self.cooldowns = {}

    def get_cooldown(self, user_id):
        cooldown_end_time = self.cooldowns.get(user_id)
        if cooldown_end_time:
            return max((cooldown_end_time - datetime.utcnow()).total_seconds(), 0)
        else:
            return 0

    def set_cooldown(self, user_id, cooldown_seconds):
        self.cooldowns[user_id] = datetime.utcnow() + timedelta(seconds=cooldown_seconds)

    def clear_cooldown(self, user_id):
        self.cooldowns.pop(user_id, None)

cooldown = Cooldown()

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction,error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
    elif isinstance(error, app_commands.errors.CheckFailure):
        embedVar = discord.Embed(title=f"This feature has been temporarily paused", description="Contact your administrator for more information", color=0xf21313)
        await interaction.response.send_message(embed=embedVar,ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred, please try again later.", ephemeral=True)
        raise error

async def getGas(address, tx):
    gas = 0
    gasPrice = 0
    baseFeePerGas = web3.eth.get_block("pending").baseFeePerGas + 1000000000
    maxPriorityFeePerGaswei = 0000000000
    maxFeePerGaswei = baseFeePerGas + maxPriorityFeePerGaswei
    maxPriorityFeePerGas = 0
    maxFeePerGas = maxFeePerGaswei/1000000000
    if 'gas' in tx:
        gasPrice = web3.eth.gas_price + 1000000000
        gas = web3.eth.estimate_gas(tx) + 1000
        
    gasData = Gas(gas, gasPrice, maxFeePerGas, maxPriorityFeePerGas)
    return gasData

async def isPaused(interaction: discord.Interaction):
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (interaction.guild_id))
            results = await cur.fetchone()
            adminData = Admin(*results)
            if adminData.pause == True:
                return False
            else:
                return True
            
async def waitTx(tx):
    try:
        tx_hash = web3.eth.send_raw_transaction(tx.rawTransaction)
        tx_address = web3.to_hex(tx_hash)
        print(tx_address)
        return tx_address
    except Exception as e:
        evalError = eval(str(e))
        print("ERROR----------------------------------------")
        print(f"This tx:{tx['rawTransaction']}") #not sure if this presents as it should
        print(evalError)
        return evalError

@client.event
async def on_message(message):
    if message.content.startswith('&sync'):
        if message.author.id == 318090426315833344:
            await client.tree.sync()
            channel = client.get_channel(message.channel.id)
            await channel.send("Synced")
            print("Synced")

txQueue = asyncio.Queue()
lastTx = {}

@tasks.loop()
async def txCheck():
    if not txQueue.empty():
        txData = await txQueue.get()
        tx = txData[0]
        address = txData[1]
        pKey = txData[2]
        guildId = txData[3]
        if guildId in lastTx:
            prevtx = lastTx[guildId]
            previoustx = web3.eth.get_transaction(prevtx)
            nonce = previoustx.nonce + 1
            tx.update({'nonce': nonce})
            signed_tx = web3.eth.account.sign_transaction(tx, pKey)
            tx_hash = await waitTx(signed_tx)
            lastTx.update({guildId:tx_hash})
            print(nonce)
        else:
            nonce = web3.eth.get_transaction_count(address) #nonce doesn't update fast enough
            #previoustx = web3.eth.getTransaction(tx)
            #nonce = pending_transaction.nonce
            tx.update({'nonce': nonce})
            signed_tx = web3.eth.account.sign_transaction(tx, pKey)
            tx_hash = await waitTx(signed_tx)
            lastTx.update({guildId:tx_hash})
            print(nonce)
    else:
        txCheck.stop()

@client.tree.command(name="setup",
    description="Set up the Wallet Bot [Owner Only]")
@app_commands.default_permissions(manage_guild=True)
#@app_commands.describe()
async def setup(interaction: discord.Interaction, announcements: discord.TextChannel, logs: discord.TextChannel):
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            announcementsChannel = announcements.id
            logsChannel = logs.id
            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (int(interaction.guild_id))) #need to add"AND guildId = interaction.Guild.id "
            results = await cur.fetchone()
            if results == None:
                poolPriv = secrets.token_hex(32)
                poolPKey = "0x" + poolPriv
                poolAccount = Account.from_key(poolPKey)
                poolAddress = str(poolAccount.address)
                rafflePriv = secrets.token_hex(32)
                rafflePKey = "0x" + rafflePriv
                raffleAccount = Account.from_key(rafflePKey)
                raffleAddress = str(raffleAccount.address)
                adminData = Admin(interaction.guild.id,poolAddress,poolPKey,raffleAddress,rafflePKey,announcementsChannel,logsChannel,False)
                await cur.execute('''
                INSERT INTO admin(guildid, pooladdress, poolkey, raffleaddress, rafflekey, announcements, logs, pause)
                    VALUES (?,?,?,?,?,?,?,?)
                ''',(adminData.guildID,adminData.poolAddress,adminData.poolPKey,adminData.raffleAddress,adminData.rafflePKey,adminData.announcements,adminData.logs,False))
                await conn.commit()
                embedVar = discord.Embed(title="Setup complete", description=f"", color=0x00ff00)
                embedVar.add_field(name="Pool Address: ", value=f"{adminData.poolAddress}", inline=True)
                embedVar.add_field(name="Private Key: ", value=f"{adminData.poolPKey}", inline=True)
                embedVar.add_field(name=f"", value=f"", inline=False)
                embedVar.add_field(name="Raffle Address: ", value=f"{adminData.raffleAddress}", inline=True)
                embedVar.add_field(name="Raffle Key: ", value=f"{adminData.rafflePKey}", inline=True)
                embedVar.add_field(name=f"", value=f"", inline=False)
                embedVar.add_field(name="Announcements channel: ", value=f"<#{adminData.announcements}>", inline=True)
                embedVar.add_field(name="Logs channel: ", value=f"<#{adminData.logs}>", inline=True)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.response.send_message(embed=embedVar,ephemeral=True)
            else:
                adminData = Admin(*results)
                if int(announcements.id) == int(adminData.announcements) and int(logs.id) == int(adminData.logs):
                    embedVar = discord.Embed(title=f"Pre-existing Server Wallets", description=f"This server already has already been configured", color=0xf21313)
                    embedVar.add_field(name="Pool Address: ", value=f"{adminData.poolAddress}", inline=False)
                    embedVar.add_field(name="Raffle Address: ", value=f"{adminData.raffleAddress}", inline=False)
                    cooldown.set_cooldown(interaction.user.id, cooldownTime)
                    await interaction.response.send_message(embed=embedVar,ephemeral=True)
                else:
                    await cur.execute('''
                    UPDATE admin SET announcements = ?, logs = ? WHERE guildid = ?
                    ''',(announcements.id,logs.id,adminData.guildID))
                    await conn.commit()
                    embedVar = discord.Embed(title=f"Channels changed", description=f"", color=0x00ff00)
                    embedVar.add_field(name="Announcements channel: ", value=f"<#{announcements.id}>", inline=True)
                    embedVar.add_field(name="Logs channel: ", value=f"<#{logs.id}>", inline=True)
                    cooldown.set_cooldown(interaction.user.id, cooldownTime)
                    await interaction.response.send_message(embed=embedVar,ephemeral=True)

@client.tree.command(name="pause",
    description="Pause all bot actions. If already paused, run this command again to unpause")
@app_commands.default_permissions(manage_guild=True)
async def pause(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (int(interaction.guild_id)))
            results = await cur.fetchone()
            if results != None:
                adminData = Admin(*results)
            if adminData.pause == True:
                await cur.execute('''
                    UPDATE admin SET pause = ?WHERE guildid = ?
                ''',(False,interaction.guild_id))
                embedVar = discord.Embed(title=f"Bot unpaused", description=f"", color=0x00ff00)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            if adminData.pause == False:
                await cur.execute('''
                    UPDATE admin SET pause = ?WHERE guildid = ?
                ''',(True,interaction.guild_id))
                embedVar = discord.Embed(title=f"Bot paused", description=f"Any currently running raffles will still continue and users can still enter them.", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return

@client.tree.command(name="poolbalance",
    description="Check pool wallet balance [Owner Only]")
@app_commands.default_permissions(manage_guild=True)
#@app_commands.describe()
async def poolbalance(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (int(interaction.guild_id)))
            results = await cur.fetchone()
            if results != None:
                adminData = Admin(*results)
                balance = web3.eth.get_balance(adminData.poolAddress)*10**-18 #maybe add await
                embedVar = discord.Embed(title=f"Pool Address", description=f"{adminData.poolAddress}", color=0x00ff00)
                embedVar.add_field(name="Pool Balance:", value=f"{balance}", inline=False)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
            else:
                embedVar = discord.Embed(title=f"No Pool Established", description=f"Speak to your administrators about setting up a pool", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
        

@client.tree.command(name="poolwithdraw",
    description="Withdraw funds from the admin wallet [Owner Only]")
@app_commands.default_permissions(manage_guild=True)
#@app_commands.describe()
async def poolwithdraw(interaction: discord.Interaction, amount: float, address: str):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (int(interaction.guild_id)))
            results = await cur.fetchone()
            if results != None:
                adminData = Admin(*results)
                total = int(amount*10**18)
                old_balance = web3.eth.get_balance(adminData.poolAddress)*10**-18
                nonce = web3.eth.get_transaction_count(adminData.poolAddress)
                try: #ADD FEE HERE?
                    tx = {
                        'nonce': 0,
                        'to': address,
                        'value': total,
                        'gas': 0,
                        'gasPrice': 0,
                        'chainId' : chainId
                    }
                    gasData = await getGas(adminData.poolAddress, tx)
                    tx.update({
                        'nonce' : nonce,
                        'gas': gasData.gas,
                        'gasPrice': gasData.gasPrice,
                    })
                    signed_tx = web3.eth.account.sign_transaction(tx, adminData.poolPKey)
                    txId = await waitTx(signed_tx)
                    await asyncio.sleep(3)
                    new_balance = web3.eth.get_balance(adminData.address)*10**-18
                    embedVar = discord.Embed(title="Withdrawal Complete", description=f"", color=0x00ff00)
                    embedVar.add_field(name="Old balance", value=f"{old_balance}", inline=False)
                    embedVar.add_field(name="New balance", value=f"{new_balance}", inline=False)
                    embedVar.add_field(name="Tx: ", value=f"{txId}", inline=False)
                    cooldown.set_cooldown(interaction.user.id, cooldownTime)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                except ValueError as vError:
                            evalError = eval(str(vError))
                            if evalError["code"] == -32000:
                                if 'nonce too low' in str(evalError):
                                    nonce = web3.eth.get_transaction_count(adminData.address)
                                    tx.update({
                                        'nonce': nonce,
                                    })
                                    signed_tx = web3.eth.account.sign_transaction(tx, adminData.pKey)
                                    tx = await waitTx(signed_tx)
                                else:
                                    embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Pool either does contain {amount} or does not have sufficient gas to transfer {amount} out of address", color=0xFFD700)
                                    embedVar.add_field(name="Current Pool Balance", value=f"{old_balance}", inline=False)
                                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                                    return
            else:
                embedVar = discord.Embed(title=f"No Pool Established", description=f"Speak to your Administrators about setting up a pool", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            
@client.tree.command(name="withdrawpoolhero",
    description="Send a hero from the pool to an address")
@app_commands.default_permissions(manage_guild=True)
#@app_commands.describe()
async def withdrawpoolhero(interaction: discord.Interaction, address: str, heroid: int):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (interaction.guild_id))
            results = await cur.fetchone()

            if results != None:
                adminData = Admin(*results)
                targetAddress = web3.to_checksum_address(address)

            heroAddress = heroContract.functions.ownerOf(heroid).call()
            if heroAddress != adminData.raffleAddress:
                embedVar = discord.Embed(title=f"No hero found", description=f"Ensure the hero is in the pool before trying to send.", color=0xf21313)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            nonce = web3.eth.get_transaction_count(adminData.raffleAddress)
            try:
                transfer = heroContract.functions.transferFrom(adminData.raffleAddress,targetAddress,heroid)
                tx = {
                    'maxFeePerGas': 0,
                    'maxPriorityFeePerGas': 0,
                    'nonce': 0,
                    'chainId' : chainId
                }
                gasData = await getGas(adminData.raffleAddress, tx)
                tx.update({
                    'nonce' : nonce,
                    'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                    'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
                    }
                )
                tx = transfer.build_transaction(tx)
                signed_tx = web3.eth.account.sign_transaction(tx, adminData.rafflePKey)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_address = web3.to_hex(tx_hash)
            except ValueError as vError:
                print(f"Error: {vError}")
                evalError = eval(str(vError))
                if evalError["code"] == -32000:
                    embedVar = discord.Embed(title=f"Insufficient Funds", description=f"You do not have enough funds, including gas, to send a Hero.", color=0xFFD700)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                    return
            embedVar = discord.Embed(title=f"Hero sent!", description=f"", color=0x00ff00)
            embedVar.add_field(name="Transaction hash ", value=f"{tx_address}", inline=False)

            cooldown.set_cooldown(interaction.user.id, cooldownTime)

            await interaction.followup.send(embed=embedVar,ephemeral=True)


@client.tree.command(name="newwallet",
    description="Create a new wallet")
#@app_commands.describe()
async def newwallet(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()
            if results == None:
                priv = secrets.token_hex(32)
                pKey = "0x" + priv
                account = Account.from_key(pKey)
                userData = User(interaction.user.id,interaction.guild_id,account.address,pKey)
                await cur.execute('''
                INSERT INTO users(uid,guildid,address,key)
                    VALUES (?,?,?,?)
                ''',(userData.uID,int(userData.guildID),userData.address,userData.pKey))
                await conn.commit()
                embedVar = discord.Embed(title="Wallet Address", description=f"Your new wallet address is:{userData.address}", color=0x00ff00)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
            else:
                embedVar = discord.Embed(title=f"Pre-existing Wallet", description=f"You already have an existing wallet!", color=0xf21313)
                await interaction.followup.send(embed=embedVar, ephemeral=True)


@client.tree.command(name="balance",
    description="Check your wallet address and balance")
#@app_commands.describe()
async def balance(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()
            caller_name = interaction.user.name
            if results == None:
                embedVar = discord.Embed(title="No wallet found", description=f"Type /newwallet to create a wallet!", color=0x00ff00)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
            else:
                userData = User(*results)
                #token = web3.eth.contract(address=nativeToken, abi=tokenAbi)
                #balance = token.functions.balanceOf(address).call()
                balance = web3.eth.get_balance(userData.address)*10**-18
                embedVar = discord.Embed(title=f"{caller_name}'s Wallet", description=f"", color=0x00ff00)
                embedVar.add_field(name="Address:", value=userData.address, inline=False)
                embedVar.add_field(name="Balance: ", value=balance, inline=False)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)

@client.tree.command(name="senduser",
    description="Send tokens to another user")
#@app_commands.describe()
async def senduser(interaction: discord.Interaction, username: discord.Member, value: float):
    await interaction.response.defer(ephemeral=True)
    if cooldown.get_cooldown(interaction.user.id) > 0:
        remaining_cooldown = int(cooldown.get_cooldown(interaction.user.id))
        await interaction.followup.send(f"You are on cooldown for {remaining_cooldown} seconds.",ephemeral=True)
        return
    
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()
            if results != None:
                callerData = User(*results)
                targetUID = username.id
                #callerAddress = web3.to_checksum_address(address)

                balance = (web3.eth.get_balance(callerData.address)*10**-18)
                if balance < value:
                    embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Please add more funds before trying this transaction again.", color=0xf21313)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (targetUID, interaction.guild_id))
                targetResults = await cur.fetchone()
                targetData = User(*targetResults)
                if targetResults != None:
                    # targetName = f"<@{target_uID}>"
                    # targetAddress =  web3.to_checksum_address(targetAddress)
                    amount = value
                    value = int(value*10**18)
                    nonce = web3.eth.get_transaction_count(callerData.address)
                    try:
                        tx = {
                            'nonce': 0,
                            'to': targetData.address,
                            'value': value,
                            # 'maxFeePerGas': 0,
                            # 'maxPriorityFeePerGas': 0,
                            'gas': 0,
                            'gasPrice': 0,
                            'chainId' : chainId
                        }
                        gasData = await getGas(callerData.address, tx)
                        tx.update({
                            'nonce': nonce,
                            # 'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                            # 'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
                            'gas': gasData.gas,
                            'gasPrice': gasData.gasPrice
                        })
                        signed_tx = web3.eth.account.sign_transaction(tx, callerData.pKey)
                        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                        tx_address = web3.to_hex(tx_hash)
                    except ValueError as vError:
                        evalError = eval(str(vError))
                        if evalError["code"] == -32000:
                            embedVar = discord.Embed(title=f"Insufficient Funds", description=f"You do not have enough funds to send {value} including gas.", color=0xFFD700)
                            await interaction.followup.send(embed=embedVar,ephemeral=True)
                            return

                    cooldown.set_cooldown(interaction.user.id, cooldownTime)

                    embedVar = discord.Embed(title=f"Transaction Succeeded", description="", color=0x00ff00)
                    embedVar.set_image(url=username.avatar)
                    embedVar.add_field(name="Receipient: ", value=f"<@{targetData.uID}>", inline=False)
                    embedVar.add_field(name="Amount received: ", value=f"{amount}", inline=False)
                    embedVar.add_field(name="Transaction hash: ", value=f"{tx_address}", inline=False)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                else:
                    embedVar = discord.Embed(title=f"No user found", description=f"Ensure the target user has set up their wallet.", color=0xf21313)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
            else:
                embedVar = discord.Embed(title=f"You don't have a wallet", description=f"Ensure you've set up a wallet before trying to send funds.", color=0x00ff00)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
   
@client.tree.command(name="sendaddress",
    description="Send tokens to another address")
#@app_commands.describe()
async def sendaddress(interaction: discord.Interaction, address: str, value: float):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()
            
            if results != None:
                callerData = User(*results)
                targetAddress = web3.to_checksum_address(address)
                balance = (web3.eth.get_balance(callerData.address)*10**-18)
                
                if balance < value:
                    embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Please add more funds before trying this transaction again. Min: 0.15", color=0xf21313)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)

                amount = value
                value = int(value*10**18)
                nonce = web3.eth.get_transaction_count(callerData.address)
                try:
                    tx = {
                        'nonce': 0,
                        'to': web3.to_checksum_address(targetAddress),
                        'value': value,
                        'maxFeePergas': 0,
                        'maxPriorityFeePerGas': 0,
                        # 'gas': 0,
                        # 'gasPrice': 0,
                        'chainId' : chainId
                    }
                    gasData = await getGas(callerData.address, tx)
                    tx.update({
                        'nonce' : nonce,
                        'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                        'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
                    })
                    signed_tx = web3.eth.account.sign_transaction(tx, callerData.pKey)
                    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    tx_address = web3.to_hex(tx_hash)
                except ValueError as vError:
                        print(f"Error: {vError}")
                        evalError = eval(str(vError))
                        print(type(evalError["code"]))
                        if evalError["code"] == -32000:
                            embedVar = discord.Embed(title=f"Insufficient Funds", description=f"You do not have enough funds to send {value} including gas.", color=0xFFD700)
                            await interaction.followup.send(embed=embedVar,ephemeral=True)
                            return

                cooldown.set_cooldown(interaction.user.id, cooldownTime)

                embedVar = discord.Embed(title=f"Transaction Succeeded", description="", color=0x00ff00)
                #embedVar.set_image(url=username.avatar)
                embedVar.add_field(name="Receipient: ", value=f"{address}", inline=False)
                embedVar.add_field(name="Amount received: ", value=f"{amount}", inline=False)
                embedVar.add_field(name="Transaction hash: ", value=f"{tx_address}", inline=False)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
            else:
                embedVar = discord.Embed(title=f"No user found", description=f"Ensure the target user has set up their wallet.", color=0xf21313)
                await interaction.followup.send(embed=embedVar,ephemeral=True)


#-------------------------------------------------------------------------------------------------------------------------------------------------------------
@client.tree.command(name="sendhero",
    description="Send a hero to an address")
#@app_commands.describe()
async def sendhero(interaction: discord.Interaction, address: str, heroid: int):
    await interaction.response.defer(ephemeral=True)
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
            print(f"time:{remaining_cooldown}")
            if remaining_cooldown > 0:
                await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
                return
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()

            if results != None:
                callerData = User(*results)
                targetAddress = web3.to_checksum_address(address)

            heroAddress = heroContract.functions.ownerOf(heroid).call()
            if heroAddress != callerData.address:
                embedVar = discord.Embed(title=f"You don't own this Hero", description=f"Ensure you have sent the desired hero to your discord wallet before running this command.", color=0xf21313)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            nonce = web3.eth.get_transaction_count(callerData.address)
            try:
                transfer = heroContract.functions.transferFrom(callerData.address,targetAddress,heroid)
                tx = {
                    #'gas': 0,
                    'maxFeePergas': 0,
                    'maxPriorityFeePerGas': 0,
                    #'gasPrice': 0,
                    'nonce': 0,
                    'chainId' : chainId, 
                }
                gasData = await getGas(callerData.address, tx)
                tx.update({
                    'nonce' : nonce,
                    'maxFeePergas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                    'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
                    #'gasPrice': gasPrice
                    }
                )
                tx = transfer.build_transaction(tx)
                signed_tx = web3.eth.account.sign_transaction(tx, callerData.pKey)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_address = web3.to_hex(tx_hash)
            except ValueError as vError:
                print(f"Error: {vError}")
                evalError = eval(str(vError))
                if evalError["code"] == -32000:
                    embedVar = discord.Embed(title=f"Insufficient Funds", description=f"You do not have enough funds, including gas, to send a Hero.", color=0xFFD700)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                    return
            embedVar = discord.Embed(title=f"Hero sent!", description=f"", color=0x00ff00)
            await interaction.followup.send(embed=embedVar,ephemeral=True)
#-------------------------------------------------------------------------------------------------------------------------------------------------------------

        # @client.tree.command(name="rain",
        #     description="Send 0.01 to the past 10 chatters")
        # #@app_commands.describe()
        # async def rain(interaction: discord.Interaction):
        #     await interaction.response.defer(ephemeral=True)
        #     if cooldown.get_cooldown(interaction.user.id) > 0:
        #         remaining_cooldown = int(cooldown.get_cooldown(interaction.user.id))
        #         await interaction.followup.send(f"You are on cooldown for {remaining_cooldown} seconds.",ephemeral=True)
        #         return
        #     cooldown.set_cooldown(interaction.user.id, cooldownTime)

        #     caller_name = interaction.user.name
        #     async with client.pool.acquire() as conn:
        #         async with conn.cursor() as cur:
        #             await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ?", (interaction.user.id, interaction.guild_id))
        #             results = await cur.fetchall()
            
            
        #             if results:
        #                 uID, guildID, address, pKey = results[0]
        #                 callerAddress = address
        #                 callerPkey = pKey
        #                 balance = web3.eth.get_balance(callerAddress)
        #                 print("Hit balance")
        #                 if balance < 0.15:
        #                     embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Please add more funds before trying this transaction again. Min: 0.15", color=0xf21313)
        #                     await interaction.followup.send(embed=embedVar,ephemeral=True)
        #                     return

        #             else:
        #                 embedVar = discord.Embed(title=f"No wallet found", description=f"Ensure you have set up your wallet.", color=0xf21313)
        #                 await interaction.followup.send(embed=embedVar,ephemeral=True)
        #             channel = interaction.channel
        #             messages = [msg async for msg in channel.history(limit=20)]
        #             users = []
        #             names = []
        #             for msg in messages:
        #                 user = msg.author.id
        #                 if user not in users:
        #                     users.append(user)
        #             if uID in users:
        #                 users.remove(uID)

        #             for id in users:
        #                 await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ?", (id, interaction.guild_id))
        #                 user_results = await cur.fetchall()
        #                 if user_results:
        #                     uID, guildID, address, pKey = user_results[0]
        #                     address = address
        #                     value = int(0.01*10**18)
        #                     try:
        #                         tx = {
        #                             'nonce': 0,
        #                             'to': address,
        #                             'value': value,
        #                             #'gas': 0,
        #                             # 'gasPrice': 0,
        #                             'maxFeePerGas': 0,
        #                             'maxPriorityFeePerGas': 0,
        #                             'chainId' : chainId
        #                         }
        #                         gasData = await getGas(callerAddress)
        #                         tx.update({
        #                             'nonce' : gasData.nonce,
        #                             'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
        #                             'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
        #                         })
        #                         signed_tx = web3.eth.account.sign_transaction(tx, callerPkey)
        #                         print(signed_tx)
        #                         tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        #                     except ValueError as vError:
        #                         evalError = eval(str(vError))
        #                         if evalError["code"] == -32000:
        #                             embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Not enough available funds to cover rain cost & gas", color=0x37FDFC)
        #                             await interaction.followup.send(embed=embedVar)
                                    
        #                 else:
        #                     continue
        #             names_joined = " ".join(names)
        #             result = "Congrats: " + names_joined
        #             if not bool(names_joined):
        #                 result = "There were no winners this time :("
        #             embedVar = discord.Embed(title=f"{caller_name} made it rain!", description=f"{result}", color=0x37FDFC)
        #             await interaction.followup.send(embed=embedVar)

@client.tree.command(name="coinflip",
    description=f"Double your money... or lose it all! [5% Fee]")
#@app_commands.describe()

@app_commands.choices(choices=[
    app_commands.Choice(name="Heads", value="Heads"),
    app_commands.Choice(name="Tails", value="Tails"),
    ])
@app_commands.check(isPaused)
async def coinflip(interaction: discord.Interaction,amount: app_commands.Range[float,0.001,1.0],choices: app_commands.Choice[str]):
    if cooldown.get_cooldown(interaction.user.id) > 0:
        remaining_cooldown = int(cooldown.get_cooldown(interaction.user.id))
        await interaction.response.send_message(f"You are on cooldown for {remaining_cooldown} seconds.",ephemeral=True)
        return
    pepegif = discord.File('Coinflip_Pepe.gif')
    await interaction.response.send_message(f"Thinking...", file = pepegif, ephemeral=False)
    cooldown.set_cooldown(interaction.user.id, cooldownTime)
    caller_uID = interaction.user.id
    total = int(amount*10**18)
    fee = float(amount*0.05)
    
    nomoneygif = discord.File('no_money.gif')
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()
            if results != None:
                userData = User(*results)
            else:
                embedVar = discord.Embed(title=f"No wallet found", description=f"Ensure you have set up your wallet.", color=0xf21313)
                await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
                return
            balance = web3.eth.get_balance(userData.address)
            balance_regular = balance/10**18
            if balance_regular < 0.0015:
                embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Please add more funds before trying this transaction again. Min: 0.15", color=0xf21313)
                await interaction.edit_original_response(content="", embed=embedVar, attachments=[nomoneygif])
                return

            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (int(interaction.guild_id)))
            adminResults = await cur.fetchone()
            if adminResults != None:
                adminData = Admin(*adminResults)
                pool_balance = web3.eth.get_balance(adminData.poolAddress)
                pool_balance_regular = pool_balance*10**-18
            else:
                embedVar = discord.Embed(title=f"No Pool Established", description=f"Speak to your administrators about setting up a pool", color=0xf21313)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            potential_win_amount = (amount * 2) + 0.02 #0.02 to ensure gas on both ends
            if pool_balance_regular <= potential_win_amount:
                    print(pool_balance_regular, potential_win_amount)
                    embedVar = discord.Embed(title=f"Insufficient Pool Funds", description=f"The pool does not contain enough {gasCurrency} for your transaction. Please contact your Administrator about increasing the pool size.", color=0xf21313)
                    await interaction.edit_original_response(content="",embed=embedVar, attachments=[])
                    return
            nonce = web3.eth.get_transaction_count(userData.address)
            try:
                tx = {
                    'nonce': 0,
                    'to': adminData.poolAddress,
                    'value': total,
                    'gas': 0,
                    'gasPrice': 0,
                    'chainId' : chainId
                }
                gasData = await getGas(userData.address, tx)
                tx.update({
                    'nonce' : nonce,
                    'gas': gasData.gas,
                    'gasPrice': gasData.gasPrice
                })
                signed_tx = web3.eth.account.sign_transaction(tx, userData.pKey)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx = web3.to_hex(tx_hash)
            except ValueError as vError:
                    evalError = eval(str(vError))
                    if evalError["code"] == -32000:
                        if 'nonce too low' in str(evalError):
                            nonce = web3.eth.get_transaction_count(userData.address)
                            tx.update({
                                'nonce': nonce,
                            })
                            signed_tx = web3.eth.account.sign_transaction(tx, userData.pKey)
                            tx = await waitTx(signed_tx)
                        else:
                            embedVar = discord.Embed(title=f"Insufficient Funds", description="Not enough funds to cover amount + gas. Please top up your account before trying to flip again", color=0xFFD700)
                            await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
                            return
            result = flip()
            await asyncio.sleep(3)
            if choices.value == "Heads" and result >= 51 or choices.value == "Tails" and result <= 50:
                winnings = float((amount*2) - fee)
                total_winnings = int(winnings*10**18)
                nonce = web3.eth.get_transaction_count(adminData.poolAddress)
                embedVar = discord.Embed(title=f"You Won!", description="", color=0xFFD700)
                embedVar.add_field(name="Amount credited: ", value=f"{winnings}", inline=False)
                embedVar.set_image(url="https://media.tenor.com/C-_St5HeiDoAAAAC/scrooge-mcduck-ducktales.gif")
                await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
                try:
                    tx = {
                        'nonce': 0,
                        'to': userData.address,
                        'value': total_winnings,
                        'gas': 0,
                        'gasPrice': 0,
                        'chainId' : chainId
                    }
                    gasData = await getGas(adminData.poolAddress, tx)
                    tx.update({
                        'nonce' : nonce,
                        'gas': gasData.gas,
                        'gasPrice': gasData.gasPrice,
                    })
                    txData = tx,adminData.poolAddress,adminData.poolPKey,adminData.guildID
                    await txQueue.put(txData)
                    txCheck.start()
                    # signed_tx = web3.eth.account.sign_transaction(tx, adminData.poolPKey)
                    # tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    # tx = web3.to_hex(tx_hash)
                except ValueError as vError:
                    print(f"Error: {vError}")
                    evalError = eval(str(vError))
                    if evalError["code"] == -32000:
                        if evalError["code"] == -32000:
                            if 'nonce too low' in str(evalError):
                                nonce = web3.eth.get_transaction_count(adminData.poolAddress)
                                tx.update({
                                    'nonce': nonce,
                                })
                                signed_tx = web3.eth.account.sign_transaction(tx, adminData.poolPKey)
                                tx = await waitTx(signed_tx)
                            else:
                                tx = "Contact admin Team"
                                logsChannel = adminData.logs
                                channel = client.get_channel(logsChannel)
                                await channel.send(f"Pool Empty, user <@{caller_uID}>(ID:{caller_uID}) is owed {winnings}")
            else:
                embedVar = discord.Embed(title=f"You Lost!", description=f"Better luck next time.", color=0xf21313)
                embedVar.set_image(url="https://media.tenor.com/uHhNnTepSt8AAAAC/robin-hood-poor.gif")
                await interaction.edit_original_response(content="", embed=embedVar, attachments=[])


def flip():
    #result = random.randint(1,100)
    return 100

#---------------------------------------{TEST FUNCTIONALITIES}-----------------------------------------------

async def heroInfo(id):
    response = requests.get(f'https://heroes.defikingdoms.com/token/{id}').json()
    heroName = response['name']
    attributes = response['attributes']
    for i in range(len(attributes)):
        if attributes[i]["trait_type"] == "Generation":
            heroGen = str(attributes[i]["value"])
        elif attributes[i]["trait_type"] == "Level":
            heroLevel = str(attributes[i]["value"])
        elif attributes[i]["trait_type"] == "Class":
            heroClass = str(attributes[i]["value"])
        elif attributes[i]["trait_type"] == "Sub Class":
            heroSubClass = str(attributes[i]["value"])
        elif attributes[i]["trait_type"] == "Rarity":
            heroRarity = str(attributes[i]["value"])
        elif attributes[i]["trait_type"] == "Profession":
            heroProfession = str(attributes[i]["value"])
            heroProfession = professionConverter(heroProfession)

    heroImage = "https://heroes.defikingdoms.com/image/"
    heroData = Hero(heroLevel, heroImage, heroName, heroGen, heroProfession, heroRarity, heroClass, heroSubClass)
    return heroData

def professionConverter(profession):
    d = {'gardening': "Gardener", 'mining': "Miner", 'foraging': "Forager", 'fishing': "Fisher"}
    if profession in d:
        return d[profession]
    else:
        return ""
    
@tasks.loop()
async def yourtask():
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT * FROM raffles WHERE NOT completed ORDER BY timeLeft LIMIT 1')
            next_task = await cur.fetchone()
    # if no remaining tasks, stop the loop
            if next_task is None:
                yourtask.stop()
                return
            raffleData = Raffle(*next_task)
            #MARK: Could add a global "adminWalletActive" to give appropriate error messages if people try to call a withdraw from admin
            # sleep until the task should be done
            timer = datetime.fromisoformat(str(raffleData.timeLeft))
            print(raffleData.completed, raffleData.timeLeft)
            await discord.utils.sleep_until(timer)
            print("Woken up")
            heroData = await heroInfo(raffleData.nftID)
            #MIN TICKETS REACHED?
            await cur.execute('SELECT * FROM admin WHERE guildid = ? LIMIT 1', (raffleData.guildID))
            results = await cur.fetchone()
            if results != None:
                adminData = Admin(*results)
                await cur.execute('SELECT SUM(tickets) FROM entrants WHERE raffleid = ? LIMIT 1', (raffleData.ID))
                totalTickets = await cur.fetchone()
            await cur.execute('SELECT * FROM raffles WHERE NOT completed ORDER BY timeLeft LIMIT 1')
            results = await cur.fetchone()
            raffleData = Raffle(*results)#update original raffleData with the correct number of ticketsSold
            if totalTickets[0] is not None:
                if raffleData.ticketsSold != totalTickets[0]:
                    print(raffleData.ticketsSold, totalTickets[0])
                    print("VALUE ERROR: TICKETS FROM ENTRANTS AND RAFFLE DO NOT MATCH")
            #working------
            if raffleData.minTickets > raffleData.ticketsSold:
            #IF NO: RETURN ALL FUNDS -5% TAX AND Hero
                await cur.execute('SELECT * FROM entrants WHERE raffleid = ?', (raffleData.ID))
                results = await cur.fetchall()
                print("We got to here")
                txs = []
                print("We got to here1")
                nonce = web3.eth.get_transaction_count(adminData.raffleAddress)
                print("We got to here2")
                print(nonce)
                for i, entrant in enumerate(results):
                    entrantData = Entrant(*entrant)
                    value = int(((entrantData.tickets * ticketPrice)*10**18)*tax) #potential issue: admin changes ticket price while raffle is ongoing, users could get more/less back than expected
                    try:
                        tx = {
                            'nonce': 0,
                            'to': entrantData.address,
                            'value': value,
                            'gas': 0,
                            'gasPrice': 0,
                            'chainId' : chainId
                        }
                        gasData = await getGas(adminData.raffleAddress, tx)
                        tx.update({
                            'nonce' : nonce + i,
                            'gas': gasData.gas,
                            'gasPrice': gasData.gasPrice,
                        })
                        signed_tx = web3.eth.account.sign_transaction(tx, adminData.rafflePKey)
                        # tx_hash = await waitTx(signed_tx)
                        txs.append(signed_tx)
                        #tx_hash = await web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                        # tx_address = web3.to_hex(tx_hash)
                        
                    except ValueError as vError:
                        evalError = eval(str(vError))
                        if evalError["code"] == -32000:
                            if 'nonce too low' in str(evalError):
                                nonce = web3.eth.get_transaction_count(adminData.raffleAddress)
                                tx.update({
                                    'nonce': nonce,
                                })
                                signed_tx = web3.eth.account.sign_transaction(tx, adminData.rafflePKey)
                                tx = await waitTx(signed_tx)
                            else:
                                outgoing_tx = "Contact Admin Team"
                                logsChannel = adminData.logs
                                channel = client.get_channel(logsChannel)
                                await channel.send(f"Raffle Error")
                try:
                    transfer = heroContract.functions.transferFrom(adminData.raffleAddress,raffleData.creatorAddress,raffleData.nftID)
                    tx = {
                        'nonce': 0,
                        'maxFeePerGas': 0,
                        'maxPriorityFeePerGas': 0,
                        # 'gasPrice': gasPrice,
                        'chainId' : chainId
                    }
                    gasData = await getGas(adminData.raffleAddress, tx)
                    tx.update({
                        'nonce' : nonce + len(txs), #may need incrementing by +1 with "if entrants:"
                        'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                        'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
                    })
                    txbuilt = transfer.build_transaction(tx)
                    signed_tx = web3.eth.account.sign_transaction(txbuilt, adminData.rafflePKey)
                    # tx_hash = await waitTx(signed_tx)
                    #tx_hash = await web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    # tx_address = web3.to_hex(tx_hash)     
                    txs.append(signed_tx)
                    for transaction in txs:
                        tx_address = await waitTx(transaction)
                        if 'nonce too low' in str(tx_address):
                            msg = tx['message']
                            start_index = msg.find("current nonce (") + len("current nonce (")
                            end_index = msg.find(")", start_index)
                            nonce = int(msg[start_index:end_index])
                            tx.update({
                                'nonce': nonce
                            })
                            txbuilt = transfer.build_transaction(tx)
                            signed_tx = web3.eth.account.sign_transaction(txbuilt, adminData.rafflePKey)
                            tx = await waitTx(signed_tx)
                    await cur.execute('UPDATE raffles SET completed = true WHERE raffleid = ?', (raffleData.ID))
                    print(f"Nobody won raffle {raffleData.ID}. NFT Successfully returned to: {raffleData.creatorAddress}")
                except ValueError as vError:
                    print(f"Error: {vError}")
                    evalError = eval(str(vError))
                    if evalError["code"] == -32000:
                        logsChannel = adminData.logs
                        channel = client.get_channel(logsChannel)
                        await channel.send(f"Failed to send hero {raffleData.nftID} back to user {raffleData.creatorAddress} from raffle {raffleData.ID} (Insufficient gas). Please send when possible.")         
                        await cur.execute('UPDATE raffles SET completed = true WHERE raffleid = ?', (raffleData.ID))
                #announcement embed pinging winner
            else: #IF YES:
                print("YES")
                value = int(((raffleData.ticketsSold*ticketPrice)*10**18)*tax)
                #RETRIEVE ENTRANTS FOR RAFFLE SELECTED
                await cur.execute('SELECT * FROM entrants WHERE raffleid = ?', (raffleData.ID))
                results = await cur.fetchall()
                data = {}
                for result in results:
                    entrantData = Entrant(*result)
                    data[entrantData.uID] = {"userID": entrantData.entrantID, "address": entrantData.address, "tickets": entrantData.tickets}
                #WORK OUT WINNER
                winner = random.choices(list(data.keys()), weights=[d["tickets"] for d in data.values()], k=1)[0]
                # Calculate the percentage chance that the winner had to win
                winnerID = data[winner]["userID"]
                winnerAddress = data[winner]["address"]
                winnerTickets = data[winner]["tickets"]
                winnerPercentage = round(winnerTickets / raffleData.ticketsSold * 100, 2)
                print(f"<@{winnerID}> won raffle {raffleData.ID} (Gen {heroData.gen} {heroData.prof}) with a {winnerPercentage}% chance!")
                embedVar = discord.Embed(title=f"Raffle {raffleData.ID} has ended!", description="", color=0xFFD700)
                embedVar.add_field(name=f"Winner", value=f"<@{winnerID}>", inline=True)
                embedVar.add_field(name=f"Hero ID", value=f"{raffleData.nftID}", inline=True)
                embedVar.add_field(name=f"", value=f"", inline=False)
                embedVar.add_field(name=f"Details", value=f"Gen {heroData.gen} {heroData.prof}", inline=True)
                embedVar.add_field(name=f"Win % chance", value=f"{winnerPercentage}", inline=True)
                img = heroData.image + f"{raffleData.nftID}"
                embedVar.set_image(url=img)
                logsChannel = adminData.logs
                channel = client.get_channel(logsChannel)
                await channel.send(embed=embedVar)
                #SEND FUNDS TO CREATOR - TAX
                txs = []
                nonce = web3.eth.get_transaction_count(adminData.raffleAddress)
                try:
                    
                    tx = {
                        'nonce': 0,
                        'to': raffleData.creatorAddress,
                        'value': value,
                        # 'maxFeePerGas': 0,
                        # 'maxPriorityFeePerGas': 0,
                        'gas': 0,
                        'gasPrice': 0,
                        'chainId' : chainId
                    }
                    gasData = await getGas(adminData.raffleAddress, tx)
                    tx.update({
                        'nonce' : nonce,
                        # 'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                        # 'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
                        'gas': gasData.gas,
                        'gasPrice': gasData.gasPrice,
                    })
                    signed_tx = web3.eth.account.sign_transaction(tx, adminData.rafflePKey)
                    # outgoing_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    # outgoing_tx = web3.to_hex(outgoing_tx_hash)
                    txs.append(signed_tx)
                except ValueError as vError:
                    print(vError)
                    evalError = eval(str(vError))
                    if evalError["code"] == -32000:
                        if 'nonce too low' in str(evalError):
                            nonce = web3.eth.get_transaction_count(adminData.raffleAddress)
                            tx.update({
                                'nonce': nonce,
                            })
                            signed_tx = web3.eth.account.sign_transaction(tx, adminData.rafflePKey)
                            tx = await waitTx(signed_tx)
                        else:
                            outgoing_tx = "Contact Admin Team"
                            logsChannel = adminData.logs
                            channel = client.get_channel(logsChannel)
                            await channel.send(f"Raffle Error (Creator Payout {raffleData.creatorAddress})")
                #SEND NFT TO WINNER -- WIP
                
                try:
                    print("Attempting to send to Winner")

                    transfer = heroContract.functions.transferFrom(adminData.raffleAddress,winnerAddress,raffleData.nftID)
                    tx = {
                        'maxFeePerGas': 0,
                        'maxPriorityFeePerGas': 0,
                        'nonce': 0,
                        'chainId' : chainId
                    }
                    gasData = await getGas(adminData.raffleAddress, tx)
                    tx.update({
                        'nonce' : nonce+1,
                        'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                        'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei'),
                        }
                    )
                    
                    txbuilt = transfer.build_transaction(tx)
                    signed_tx = web3.eth.account.sign_transaction(txbuilt, adminData.rafflePKey)
                    # tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    # tx_address = web3.to_hex(tx_hash)
                    txs.append(signed_tx)
                    for transaction in txs:
                        tx_hash = await waitTx(transaction)
                        if 'nonce too low' in str(tx_hash):
                            msg = tx['message']
                            start_index = msg.find("current nonce (") + len("current nonce (")
                            end_index = msg.find(")", start_index)
                            nonce = int(msg[start_index:end_index])
                            tx.update({
                                'nonce': nonce
                            })
                            txbuilt = transfer.build_transaction(tx)
                            signed_tx = web3.eth.account.sign_transaction(txbuilt, adminData.rafflePKey)
                            tx = await waitTx(signed_tx)
                except ValueError as vError:
                    print(vError)
                    evalError = eval(str(vError))
                    if evalError["code"] == -32000:
                        if 'nonce too low' in str(evalError):
                            outgoing_tx = "Contact admin Team"
                            logsChannel = adminData.logs
                            channel = client.get_channel(logsChannel)
                            await channel.send(f"Raffle Error (NFT Payout: hero ID {raffleData.nftID} // Receiver: {winnerAddress})")
                        elif "insufficient funds for gas" in str(evalError):
                            await channel.send(f"No gas to distribute rewards. Please top up then manually distribute. (NFT Payout: hero ID {raffleData.nftID} // Receiver: {winnerAddress})")
                        else:
                            await channel.send(f"Raffle Error (NFT Payout: hero ID {raffleData.nftID} // Receiver: {winnerAddress})")
            
                await cur.execute('UPDATE raffles SET completed = true, winnerid = ? WHERE raffleid = ?', (winnerID,raffleData.ID))

@client.tree.command(name="newraffle",
    description="Create a raffle in your server")
#@app_commands.default_permissions(manage_guild=True)
@app_commands.choices(timelimit=[
    app_commands.Choice(name="1 Day", value=1),
    app_commands.Choice(name="3 Days", value=3),
    app_commands.Choice(name="5 Days", value=5),
    app_commands.Choice(name="7 Days", value=7)
    ])
@app_commands.check(isPaused)
async def newraffle(interaction: discord.Interaction, heroid: int, minprice:int, timelimit:app_commands.Choice[int]):
    await interaction.response.defer(ephemeral=False)
    remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
    print(f"time:{remaining_cooldown}")
    if remaining_cooldown > 0:
        await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
        return
    #Work out minimum tickets
    minTickets = minprice#/ticketPrice
    #endTime is current time after epoch in seconds + how many days were specified * seconds in a day
    timelimit = int(timelimit.value)
    currentTime = utcnow()
    endTime = currentTime + timedelta(minutes=2)#MARK: after testing change back to timelimit
    #Check if user has a wallet set up
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()
            if results != None:
                userData = User(*results)
            else:
                embedVar = discord.Embed(title=f"No wallet found", description=f"Ensure you have set up your wallet.", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
                return
            
            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (int(interaction.guild_id)))
            results = await cur.fetchone()
            if results != None:
                adminData = Admin(*results)
            else:
                embedVar = discord.Embed(title=f"Raffle system not established", description=f"Speak to your administrators about setting up a pool", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
        
            #Check if user has Hero_id in the wallet
            HeroAddress = heroContract.functions.ownerOf(heroid).call()
            if HeroAddress != userData.address:
                embedVar = discord.Embed(title=f"You don't own this hero", description=f"Ensure you have sent the desired hero to your discord wallet before running this command.", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            #Check if user has enough gas in wallet to send NFT
            #Try to send Hero to guild wallet - Return error message if failed
            try:
                nonce = web3.eth.get_transaction_count(userData.address)
                transfer = heroContract.functions.transferFrom(userData.address,adminData.raffleAddress,heroid)
                tx = {
                    'nonce': 0,
                    'maxFeePerGas': 0,
                    'maxPriorityFeePerGas': 0,
                    'chainId' : chainId
                }
                gasData = await getGas(userData.address, tx)
                tx.update({
                    'nonce' : nonce,
                    'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                    'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei')
                })
                tx = transfer.build_transaction(tx)
                signed_tx = web3.eth.account.sign_transaction(tx, userData.pKey)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_address = web3.to_hex(tx_hash)
            except ValueError as vError:
                print(f"Error: {vError}")
                evalError = eval(str(vError))
                if evalError["code"] == -32000:
                    embedVar = discord.Embed(title=f"Insufficient Funds", description=f"You do not have enough funds, including gas, to send a Hero to be raffled.", color=0xFFD700)
                    cooldown.set_cooldown(interaction.user.id, cooldownTime)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                    return
                
            #Add to raffle database:
            await cur.execute('''
            INSERT INTO raffles(
                guildID,
                userID,
                userAddress,
                nftID,
                minTickets,
                timeLeft,
                ticketsSold,
                completed,
                winnerID) VALUES (?,?,?,?,?,?,?,?,?) RETURNING raffleid
            ''', (interaction.guild.id,userData.uID,userData.address,heroid,minTickets,endTime,0,False,0))
            raffleID = cur._cursor.lastrowid
            # await cur.execute('SELECT last_insert_rowid()', ())
            # result = await cur.fetchone()
            # raffle_id = result[0]
            if yourtask.is_running():
                yourtask.restart()
                print("yourtask restarting")
            else:
                print("yourtask starting")
                yourtask.start()
            
            embedVar = discord.Embed(title=f"Raffle created!", description=f"Raffle {raffleID}", color=0x00ff00)
            date = str(endTime)[:19]
            try:
                heroData = await heroInfo(heroid)
                embedVar.add_field(name=f"{heroData.name} (#{heroid})", value=f"", inline=False)
                embedVar.add_field(name=f"Class", value=f"{heroData.hclass} / {heroData.hsubclass}", inline=True)
                embedVar.add_field(name=f"Rarity", value=f"{heroData.rarity}", inline=True)
                embedVar.add_field(name=f"", value=f"", inline=False)
                embedVar.add_field(name=f"Generation", value=f"Gen{heroData.gen}", inline=True)
                embedVar.add_field(name=f"Profession", value=f"{heroData.prof}", inline=True)
                embedVar.add_field(name=f"", value=f"", inline=False)
                embedVar.add_field(name=f"Minimum tickets", value=f"{minTickets}", inline=True)
                embedVar.add_field(name=f"End date", value=f"{date}", inline=True)
                img = heroData.image + f"{heroid}"
                embedVar.set_image(url=img)
            except Exception as e:
                print(f"Error: {e}")
                pass
            cooldown.set_cooldown(interaction.user.id, cooldownTime)
            await interaction.followup.send(embed=embedVar,ephemeral=False)



@client.tree.command(name="enterraffle",
    description="Join a raffle")
#@app_commands.default_permissions(manage_guild=True)
@app_commands.check(isPaused)
async def enterraffle(interaction: discord.Interaction, raffleid: int, tickets:int):
    await interaction.response.defer(ephemeral=True)
    remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
    print(f"time:{remaining_cooldown}")
    if remaining_cooldown > 0:
        await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
        return
    value = tickets*ticketPrice #total price in selected token
    #Find the raffle that was designated
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM raffles WHERE guildid = ? AND raffleid = ? LIMIT 1", (interaction.guild_id,raffleid))
            results = await cur.fetchone()
            if results != None:
                raffleData = Raffle(*results)
                if raffleData.completed:
                    embedVar = discord.Embed(title=f"This raffle has ended", description=f"Winner: {raffleData.winnerID}", color=0xFFD700) #HERE
                    cooldown.set_cooldown(interaction.user.id, cooldownTime)
                    await interaction.followup.send(embed=embedVar,ephemeral=True)
                    return
            else:
                embedVar = discord.Embed(title=f"Raffle not found", description=f"No raffle was found with the ID provided.", color=0xFFD700)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            
            #Check if user has a wallet set up
            await cur.execute("SELECT * FROM users WHERE uid = ? AND guildid = ? LIMIT 1", (interaction.user.id, interaction.guild_id))
            results = await cur.fetchone()
            if results != None:
                callerData = User(*results)
            else:
                embedVar = discord.Embed(title=f"No wallet found", description=f"Ensure you have set up your wallet.", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.edit_original_response(content="", embed=embedVar, attachments=[])
                return
            #Check if user has enough funds & gas in wallet for transaction
            balance = web3.eth.get_balance(callerData.address)*10**-18
            if balance < value:
                embedVar = discord.Embed(title=f"Insufficient Funds", description=f"Please add more funds before trying this transaction again.", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            #Try to send funds - Return error message if failed
            await cur.execute("SELECT * FROM admin WHERE guildid = ? LIMIT 1", (int(interaction.guild_id)))
            results = await cur.fetchone()
            if results != None:
                adminData = Admin(*results)
                adminAddress = web3.to_checksum_address(adminData.raffleAddress)
                try:
                    nonce = web3.eth.get_transaction_count(callerData.address)
                    tx = {
                        'nonce': 0,
                        'to': adminAddress,
                        'value': int(value*10**18),
                        # 'maxFeePerGas': 0,
                        # 'maxPriorityFeePerGas': 0,
                        'gas': 0,
                        'gasPrice': 0,
                        'chainId' : chainId
                    }
                    gasData = await getGas(callerData.address, tx)
                    tx.update({
                        'nonce': nonce,
                        # 'maxFeePerGas': web3.to_wei(gasData.maxFeePerGas, 'gwei'),
                        # 'maxPriorityFeePerGas': web3.to_wei(gasData.maxPriorityFeePerGas, 'gwei')
                        'gas': gasData.gas,
                        'gasPrice': gasData.gasPrice
                    })
                    signed_tx = web3.eth.account.sign_transaction(tx, callerData.pKey)
                    tx = await waitTx(signed_tx)
                    if 'nonce too low' in str(tx):
                        msg = tx['message']
                        start_index = msg.find("current nonce (") + len("current nonce (")
                        end_index = msg.find(")", start_index)
                        nonce = int(msg[start_index:end_index])
                        tx = {
                            'nonce': nonce,
                            'to': adminAddress,
                            'value': int(value*10**18),
                            'gas': gasData.gas,
                            'gasPrice': gasData.gasPrice,
                            'chainId' : chainId
                        }
                        signed_tx = web3.eth.account.sign_transaction(tx, callerData.pKey)
                        tx = await waitTx(signed_tx)
                except ValueError as vError:
                    evalError = eval(str(vError))
                    print(vError)
                    if evalError["code"] == -32000:
                        if 'nonce too low' in str(evalError):
                            nonce = web3.eth.get_transaction_count(callerData.address)
                            tx.update({
                                'nonce': nonce,
                            })
                            signed_tx = web3.eth.account.sign_transaction(tx, callerData.pKey)
                            tx = await waitTx(signed_tx)
                        else:
                            embedVar = discord.Embed(title=f"Insufficient Funds", description="Not enough funds to cover amount + gas. Please top up your account before trying to flip again", color=0xFFD700)
                            cooldown.set_cooldown(interaction.user.id, cooldownTime)
                            await interaction.followup.send(content="", embed=embedVar, attachments=[])
                            return
            else:
                embedVar = discord.Embed(title=f"No raffle system established", description=f"Speak to your administrators about setting up the raffle system", color=0xf21313)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            heroData = await heroInfo(raffleData.nftID)
            #On success: Add entry to database
            results = await cur.execute('SELECT id FROM entrants WHERE entrantID = ? AND raffleid = ? LIMIT 1', (callerData.uID,raffleData.ID))
            row = await cur.fetchone()
            if row: #Check if they already purchased tickets, if so UPDATE
                await cur.execute('UPDATE entrants SET tickets = tickets + ? WHERE entrantID = ? AND raffleid = ?', (tickets, callerData.uID, raffleData.ID))
                await cur.execute('UPDATE raffles SET ticketsSold = ticketsSold + ? WHERE raffleid = ?', (tickets,raffleData.ID))
                embedVar = discord.Embed(title=f"Additional tickets bought for raffle {raffleData.ID}", description="", color=0x00ff00)
                embedVar.add_field(name=f"Hero ID: {raffleData.nftID}", value=f"Gen {heroData.gen} {heroData.prof}", inline=False)
                embedVar.add_field(name=f"Tickets Purchased", value=f"{tickets}", inline=False)
                embedVar.add_field(name="Transaction hash: ", value=f"{tx}", inline=False)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
            else:
                await cur.execute('''
                INSERT INTO entrants(
                    entrantID,
                    entrantAddress,
                    raffleID,
                    tickets) VALUES (?,?,?,?)
                ''', (interaction.user.id,callerData.address,raffleData.ID,tickets))
                await cur.execute('''
                    UPDATE raffles SET ticketsSold = ticketsSold + ? WHERE raffleid = ?
                    ''', (tickets,raffleData.ID))
            # Return ticket numbers & transaction ID
                embedVar = discord.Embed(title=f"Raffle Entered!", description="", color=0x00ff00)
                embedVar.add_field(name=f"Hero ID: {raffleData.nftID}", value=f"Gen {heroData.gen} {heroData.prof}", inline=False)
                embedVar.add_field(name=f"Tickets Purchased", value=f"{tickets}", inline=False)
                embedVar.add_field(name="Transaction hash: ", value=f"{tx}", inline=False)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
#--------------------------------------------------------------------------------------------------------------------------------------------------------

@client.tree.command(name="raffleinfo",
    description="View a specific raffle's details")
#@app_commands.default_permissions(manage_guild=True)
@commands.check(isPaused)
async def raffleinfo(interaction: discord.Interaction, raffleid: int):
    await interaction.response.defer(ephemeral=True)
    remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
    print(f"time:{remaining_cooldown}")
    if remaining_cooldown > 0:
        await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
        return
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM raffles WHERE guildid = ? AND raffleid = ? LIMIT 1", (interaction.guild_id,raffleid))
            results = await cur.fetchone()
            if results != None:
                raffleData = Raffle(*results)
            else:
                embedVar = discord.Embed(title=f"Raffle not found", description=f"No raffle was found with the ID provided.", color=0xFFD700)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            if raffleData.completed:
                embedVar = discord.Embed(title=f"Raffle {raffleid}", description=f"Status: Completed", color=0x00ff00)
                embedVar.add_field(name=f"Hero: {raffleData.nftID}", value=f"", inline=False)
                try:
                    heroData = await heroInfo(raffleData.nftID)
                    embedVar.add_field(name=f"{heroData.name}", value=f"Gen {heroData.gen} {heroData.prof}", inline=False)
                    img = heroData.image + f"{raffleData.nftID}"
                    embedVar.set_image(url=img)
                except:
                    pass
                embedVar.add_field(name=f"Sold for {raffleData.ticketsSold * ticketPrice} {currency}!", value=f"to <@{raffleData.winnerID}>", inline=False)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            date = str(raffleData.timeLeft)[:19]
            embedVar = discord.Embed(title=f"Raffle {raffleid}", description=f"Status: Running", color=0x00ff00)
            embedVar.add_field(name=f"Hero: {raffleData.nftID}", value=f"", inline=False)
            try:
                heroData = await heroInfo(raffleData.nftID)
                embedVar.add_field(name=f"{heroData.name}", value=f"Gen {heroData.gen} {heroData.prof}", inline=False)
                img = heroData.image + f"{raffleData.nftID}"
                embedVar.set_image(url=img)
            except:
                pass
            embedVar.add_field(name=f"Tickets sold", value=f"{raffleData.ticketsSold}", inline=False)
            embedVar.add_field(name=f"Minimum tickets", value=f"{raffleData.minTickets}", inline=False)
            embedVar.add_field(name=f"End date", value=f"{date}", inline=False)
            cooldown.set_cooldown(interaction.user.id, cooldownTime)
            await interaction.followup.send(embed=embedVar,ephemeral=True)


@client.tree.command(name="rafflelist",
    description="View a list of currently active raffles in your server.")
#@app_commands.default_permissions(manage_guild=True)
async def rafflelist(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    remaining_cooldown = cooldown.get_cooldown(interaction.user.id)
    print(f"time:{remaining_cooldown}")
    if remaining_cooldown > 0:
        await interaction.followup.send(f"You are on cooldown for {int(remaining_cooldown)} seconds.",ephemeral=True)
        return
    
    async with client.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM raffles WHERE guildid = ? AND completed = ?", (interaction.guild_id, False))
            results = await cur.fetchall()
            if results: #if results return embed of current active raffles
                count = 1
                embedVar = discord.Embed(title=f"Active raffles", description=f"", color=0x75e6da)
                for result in results:
                    raffleData = Raffle(*result)
                    heroData = await heroInfo(raffleData.nftID)
                    embedVar.add_field(name=f"{count}. Raffle: {raffleData.ID}", value=f"", inline=False)
                    embedVar.add_field(name=f"Hero: {raffleData.nftID} (Level {heroData.level} Gen {heroData.gen} {heroData.prof})", value=f"", inline=False)
                    count += 1
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
                return
            else:
                embedVar = discord.Embed(title=f"No active raffles", description=f"If you believe this is a mistake, please contact your administrator.", color=0xFFD700)
                cooldown.set_cooldown(interaction.user.id, cooldownTime)
                await interaction.followup.send(embed=embedVar,ephemeral=True)
#------------------------------------------------------------------------------------------------------------

TOKEN = read_token()

client.run(TOKEN)