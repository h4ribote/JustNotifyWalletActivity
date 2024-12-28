from web3 import Web3, HTTPProvider
from web3 import types as web3Types
from time import sleep
from typing import Sequence
from decimal import Decimal
import requests
import json

def load_json():
    with open("settings/filter_address.json") as f:
        filter_address_json:dict[str,str] = json.load(f)
        for address in filter_address_json.keys():
            filter_address[str(Web3.to_checksum_address(address))] = filter_address_json[address]

    with open("settings/options.json") as f:
        options:dict[str,str] = json.load(f)

    with open("settings/rpc_providers.json") as f:
        rpc_providers:list[str] = json.load(f)

    return filter_address_json, options, rpc_providers

filter_address, options, rpc_providers = load_json()

class URLs:
    @staticmethod
    def txHash(string:str):
        return options['explorer_transaction'].replace("{hash}", string)
    
    @staticmethod
    def address(string:str):
        return options['explorer_address'].replace("{address}", string)

def webhookEmbed(tx_hash:str, source:str, dest:str, value:str):
    content = {
                "content": None,
                "embeds": [
                    {
                      "title": "New Transaction",
                      "url": URLs.txHash(tx_hash),
                      "color": 1744356,
                      "fields": [
                        {
                          "name": "From",
                          "value": f"{filter_address.get(source,'Unknown')} ([{source[:10]}...]({URLs.address(source)}))"
                        },
                        {
                          "name": "To",
                          "value": f"{filter_address.get(dest,'Unknown')} ([{dest[:10]}...]({URLs.address(dest)}))"
                        },
                        {
                          "name": "Value",
                          "value": f"{value} {options['symbol']}"
                        }
                      ]
                    }
                ],
                "username": "Just Notify Wallet Activity (by h4ribote)"
              }
    return content

def postWebhook(webhook_url:str, content:dict):
    requests.post(webhook_url, json=content, headers={'Content-Type': 'application/json'})

def getBlock():
    errors = []
    for provider_url in rpc_providers:
        try:
            return Web3(HTTPProvider(provider_url)).eth.get_block("latest",True)
        except Exception as e:
            errors.append(str(e))
    raise Exception(str(errors))

def main():
    previous_block = 0
    while True:
        try:
            block = getBlock()
            if not block.number == previous_block:
                txs:Sequence[web3Types.TxData] = block.transactions
                for tx in txs:
                    if tx['from'] in filter_address.keys() or tx['to'] in filter_address.keys():
                        emb = webhookEmbed(tx['hash'].hex(),tx['from'],tx['to'],str(Decimal(tx['value'])/1000000000000000000))
                        postWebhook(options['webhook_urk'], emb)
                previous_block = block.number
        except Exception as e:
            print(e)
        sleep(int(options['get_transaction_interval']))

if __name__ == "__main__":
    main()
