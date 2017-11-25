#!/usr/bin/python3
#
# taker.py: EtherDelta API client in python using websocket
# =========================================================
#
# This example will connect to EtherDelta's WebSocket API,
# query the market, get the order book, get recent trades,
# and then it will perform a buy order of 0.0001 ETH worth
# of Aeternity coin at the lowest offered rate.
#
# The order is sent to Infura's mainnet Ethereum endpoint.
#
# After that, the client stays connected, listening for data and
# updating the order book and the trade history as updates come in.
#
#
# Prerequisites
# =============
#
# This script needs the EtherDelta ABI JSON file,
# expected to be found in contracts/etherdelta.json
# and the generic token ABI JSON file,
# expected in contracts/token.json
#
# Author: Tom Van Braeckel <tomvanbraeckel+etherdelta@gmail.com>
# License: MIT License (MIT), contributed to Piper Merriam's web3.py
#
#
# Install dependencies on Ubuntu 16.04 Long Term Support
# ======================================================
#
# Tested with Python 3.5.2 (default, Sep 14 2017, 22:51:06)
# Python dependencies: websocket-client, web3 (after Thu Sep 28 because we need signTransaction())
#
#
# Install Python 3 virtual environment (skip this if you have Python 3 installed system-wide)
# -------------------------------------------------------------------------------------------
# sudo apt-get install virtualenv python3-virtualenv
# virtualenv -p python3 venv
# . venv/bin/activate
#
# Install the dependencies that we need:
# --------------------------------------
# sudo apt-get install python-pip
# pip install websocket-client
#
# Install web3 from source because we need signTransaction:
# ---------------------------------------------------------
# git clone https://github.com/pipermerriam/web3.py.git
# pip install -r web3.py/requirements-dev.txt
# pip install -e web3.py
#
# Run the example:
# ----------------
# . venv/bin/activate	# initialize Python 3 virtual environment
# python taker.py

__version__ = "2.0"

import websocket
import _thread
import time
import json
import sys
import web3

from web3 import Web3, HTTPProvider
from operator import itemgetter
from collections import OrderedDict

#################
# CONFIGURATION #
#################

# Your Ethereum wallet's public key
# You can copy-paste it from your MetaMask browser extension
userAccount = '0xb5Ba8b93860394033B09cbd19fdE8B3D0E70fA40'

# Your Ethereum wallet's private key
# This is only needed if you want the buy order to succeed.
user_wallet_private_key = ''

# The smart contract address of the token you want to trade
# On EtherDelta.com, click "Tokens" in the top-right hand corner,
# click the token you want to trade and copy-paste the 0x... address.
# Example: Smart Contract: 0x9742fa8cb51d294c8267ddfead8582e16f18e421
token = "0x5ca9a71b1d01849c0a95490cc00559717fcf0d1d"  # Aeternity token
#token = "0xaec2e87e0a235266d9c5adc9deb4b2e29b54d009"  # SNGLS
# EtherDelta contract address
# This rarely changes.
addressEtherDelta = '0x8d12A197cB00D4747a1fe03395095ce2A5CC6819'  # etherdelta_2's contract address

########################
# END OF CONFIGURATION #
########################

# Global API interfaces
web3 = Web3(HTTPProvider('http://35.205.255.115:8545'))

# Global lists of sells, buys and trades that are always sorted and updated whenever data comes in
orders_sells = []
orders_buys = []
trades = []


def updateOrders(newOrders):
    global orders_sells, orders_buys, token, userAccount

    # Parse the sells
    new_sells = newOrders['sells']
    valid_new_sells = [x for x in new_sells if x['tokenGive'].lower() == token.lower() and float(
        x['ethAvailableVolumeBase']) >= 0.001 and x.get('deleted', None) == None and x not in orders_sells]
    if len(valid_new_sells) > 0:
        print("Adding " + str(len(valid_new_sells)) + " new sell orders to the list...")
        orders_sells.extend(valid_new_sells)
        orders_sells = sorted(orders_sells, key=itemgetter('price', 'amountGet'))
        # printOrderBook()

    # Parse the buys
    new_buys = newOrders['buys']
    valid_new_buys = [x for x in new_buys if
                      x['tokenGet'].lower() == token.lower() and float(x['ethAvailableVolumeBase']) >= 0.001 and x.get(
                          'deleted', None) == None and x not in orders_buys]
    if len(valid_new_buys) > 0:
        print("Adding " + str(len(valid_new_buys)) + " new buy orders to the list...")
        orders_buys.extend(valid_new_buys)
        orders_buys = sorted(orders_buys, key=itemgetter('price', 'amountGet'), reverse=True)
        # printOrderBook()

    # Remove the deleted orders from the order book because they are cancelled, filled or expired
    todelete = [x for x in new_buys if x['tokenGet'].lower() == token.lower() and x.get('deleted', None) != None]
    if len(todelete) > 0:
        print("Deleting these orders: " + str(todelete))
        orders_buys.delete(todelete)


def updateTrades(newTrades):
    global trades, token
    valid_new_trades = [x for x in newTrades if
                        ('tokenAddr' not in x or x['tokenAddr'].lower() == token.lower()) and x not in trades]
    if len(valid_new_trades) > 0:
        print("Adding " + str(len(valid_new_trades)) + " new trades to the list...")
        trades.extend(valid_new_trades)
        trades = sorted(trades, key=itemgetter('date', 'amount'), reverse=True)


def printOrderBook():
    global orders_sells, orders_buys
    ordersPerSide = 10
    print()
    print('Order book')
    print('----------')
    topsells = reversed(orders_sells[0:ordersPerSide])
    topbuys = orders_buys[0:ordersPerSide]
    for sell in topsells:
        print(str(sell['price']) + " " + str(round(float(sell['ethAvailableVolume']), 3)))
    if (len(orders_sells) > 0 and len(orders_buys) > 0):
        spread = float(orders_sells[0]['price']) - float(topbuys[0]['price'])
        print("---- Spread (" + "%.10f" % spread + ") ----")
    else:
        print('--------')
    for buy in topbuys:
        print(str(buy['price']) + " " + str(round(float(buy['ethAvailableVolume']), 3)))


def printTrades():
    global trades
    print()
    print('Recent trades')
    print('-------------')
    numTrades = 10
    for trade in trades[0:numTrades]:
        print(trade['date'] + " " + trade['side'] + " " + trade['amount'] + " @ " + trade['price'])


def trade(order, etherAmount):
    global user_wallet_private_key, web3, addressEtherDelta, contractEtherDelta

    print("\nTrading " + str(etherAmount) + " ETH of tokens against this order: %.10f tokens @ %.10f ETH/token" % (
    float(order['ethAvailableVolume']), float(order['price'])))
    print("Details about order: " + str(order))

    # Transaction info
    amount_to_buyWei = web3.toWei(etherAmount, 'ether')
    maxGas = 250000
    gasPriceWei = 1000000000  # 1 Gwei

    # trade function arguments
    kwargs = {
        'tokenGet': Web3.toChecksumAddress(order['tokenGet']),
        'amountGet': int(float(order['amountGet'])),
        'tokenGive': Web3.toChecksumAddress(order['tokenGive']),
        'amountGive': int(float(order['amountGive'])),
        'expires': int(order['expires']),
        'nonce': int(order['nonce']),
        'user': Web3.toChecksumAddress(order['user']),
        'v': order['v'],
        'r': web3.toBytes(hexstr=order['r']),
        's': web3.toBytes(hexstr=order['s']),
        'amount': int(amount_to_buyWei),
    }

    # Build binary representation of the function call with arguments
    abidata = contractEtherDelta.encodeABI('trade', kwargs=kwargs)
    nonce = web3.eth.getTransactionCount(userAccount)
    transaction = {'to': addressEtherDelta, 'from': userAccount, 'gas': 250000, 'gasPrice': 100000000, 'data': abidata,
                   'nonce': nonce, 'chainId': 1}
    if len(user_wallet_private_key) == 64:
        signed = web3.eth.account.signTransaction(transaction, user_wallet_private_key)
        result = web3.eth.sendRawTransaction(web3.toHex(signed.rawTransaction))
        print("Transaction returned: " + str(result))
        print("\nDone! You should see the transaction show up at https://etherscan.io/tx/" + web3.toHex(result))
    else:
        print("WARNING: no valid private key found, user_wallet_private_key must be 64 characters long")


def send_getMarket(ws):
    global token, userAccount
    print("Sending getMarket request")
    ws.send('42["getMarket",{"token":"' + token + '","user":"' + userAccount + '"}]')


def on_cont_message(ws, message_string, continueflag):
    # This event never seems to trigger, but better to be aware of it anyway
    print('Received continued message from WebSocket: ' + message_string)


def on_message(ws, message):
    global userAccount

    print('Received message from WebSocket: ' + message[0:140])
    # Only handle real data messages
    if message[:2] != "42":
        return
    # Convert message to object
    j = json.loads(message[2:])
    # Parse the message
    if 'market' in j:
        print("Received market reply!")
        market = j[1]
        # Fill the list of trades
        if 'trades' in market:
            updateTrades(j[1]['trades'])
        else:
            print(
                "WARNING: no trades found in market response from EtherDelta API, this happens from time to time but we don't really need it here so not retrying.")
        # Fill the list of orders
        if 'orders' in market:
            updateOrders(j[1]['orders'])
            # When we get a market reply with orders in it,
            # we update the list of orders, print them,
            # and then buy the cheapest sell order, if possible.
            printOrderBook()
            printTrades()
            if (len(orders_sells) > 0):
                print("\nThere are sell orders available. Taking the cheapest one for a trade of 0.0001 ETH!")
                trade(orders_sells[0], 0.0001)
            else:
                print(
                    "\nWARNING: market reply from API contained no valid sell orders to buy, perhaps this is a really calm market...?")
        else:
            print(
                "WARNING: market response from EtherDelta API did not contain order book, this happens from time to time, retrying after a 5 second grace period...")
            time.sleep(5)
            send_getMarket(ws)
    elif 'orders' in j:
        print("Got order event")
        updateOrders(j[1])
    elif 'trades' in j:
        print("Got trade event")
        updateTrades(j[1])
    elif 'funds' in j:
        print("Received funds event from EtherDelta API, no action to take.")
    else:
        print("Received an unrecognized event from the EtherDelta API, no action to take.")


def on_error(ws, error):
    print('Error:' + str(error))


def on_ping(ws, ping):
    # websocket-client does not seem to call this on_ping callback when it sends a ping...
    print('Ping:' + str(ping))


def on_pong(ws, pong):
    print('EtherDelta WebSocket API replied to our ping with a pong:' + str(pong))


def on_close(ws):
    # The server closes the connection, regardless of our pings...
    print("WebSocket closed, reconnecting...")
    ws.close()  # Ensure it is really closed
    time.sleep(5)  # Grace period, just being polite
    websocket_connect()


def on_open(ws):
    def run(*args):
        global token, userAccount
        print("EtherDelta WebSocket connected")
        if len(orders_sells) == 0:
            send_getMarket(ws)
        while True:
            time.sleep(10)
            print("Waiting for data to come in...")
        else:
            print("WARNING: no sell orders available to buy! Perhaps the API did not send any orders?")
        ws.close()

    _thread.start_new_thread(run, ())


def websocket_connect():
    ws = websocket.WebSocketApp(
        "wss://socket.etherdelta.com/socket.io/?transport=websocket",
        on_message=on_message,
        on_ping=on_ping,
        on_pong=on_pong,
        on_error=on_error,
        on_close=on_close)
    ws.on_open = on_open
    # The API seems to close the connection, even when we send a periodic ping
    ws.run_forever(ping_interval=10)


if __name__ == "__main__":
    print("EtherDelta API client in python using websocket")
    print("More info and details in this script's source code.")
    time.sleep(1)

    # Most of web3's functions need checksummed addresses
    userAccount = Web3.toChecksumAddress(userAccount)
    token = Web3.toChecksumAddress(token)
    addressEtherDelta = Web3.toChecksumAddress(addressEtherDelta)

    # Load the ABI of the EtherDelta contract
    with open('contracts/etherdelta.json', 'r') as abi_definition:
        abiEtherDelta = json.load(abi_definition)
    print(sys.version)
    contractEtherDelta = web3.eth.contract(address=addressEtherDelta, abi=abiEtherDelta)
    # Load the ABI of the ERC20 token
    with open('contracts/token.json', 'r') as token_abi_definition:
        token_abi = json.load(token_abi_definition)
    contractToken = web3.eth.contract(address=token, abi=token_abi)

    print("")
    print("Account balances:")
    print("=================")
    print("Wallet account balance: " + str(web3.fromWei(web3.eth.getBalance(userAccount), 'ether')) + " ETH")
    balance = contractToken.call().balanceOf(userAccount)
    print("Wallet token balance: " + str(web3.fromWei(balance, 'ether')) + " tokens")

    balance = contractEtherDelta.call().balanceOf(token="0x0000000000000000000000000000000000000000", user=userAccount)
    print("EtherDelta ETH balance: " + str(web3.fromWei(balance, 'ether')) + " ETH")
    balance = contractEtherDelta.call().balanceOf(token=token, user=userAccount)
    print("EtherDelta token balance: " + str(web3.fromWei(balance, 'ether')) + " tokens")
    print("")

    '''
    # For debugging and testing:
    with open('api_replies/market.txt', 'r') as myfile:
        on_message("test", myfile.read())
        printOrderBook()
        printTrades()
        trade(orders_sells[0], 0.0001)
        sys.exit()
    '''

print('Starting WebSocket version ' + websocket.__version__)
websocket_connect()

