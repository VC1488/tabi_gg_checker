import asyncio
import logging
import csv  # Добавлен импорт csv

from web3 import AsyncWeb3
from web3 import AsyncHTTPProvider

logging.getLogger('asyncio').setLevel(logging.CRITICAL)

CHAIN_ID = 9788
RPC_URL = "https://rpc.testnetv2.tabichain.com"
TOKEN_CONTRACT_ADDRESS = "0xD8BF160Cd5049B6439d11258E96B7535126aB648"

TOKEN_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

def read_private_keys(filename: str) -> list:
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

async def get_token_balance(private_key: str):
    provider = AsyncHTTPProvider(RPC_URL)
    async_web3 = AsyncWeb3(provider)
    account = async_web3.eth.account.from_key(private_key)
    wallet_address = account.address
    contract = async_web3.eth.contract(address=TOKEN_CONTRACT_ADDRESS, abi=TOKEN_ABI)

    balance = None
    while balance is None:
        try:
            balance = await contract.functions.balanceOf(wallet_address).call()
            print(f"Адрес: {wallet_address} | Баланс токена: {balance / 10 ** 18}")
            return wallet_address, balance
        except Exception as e:
            print(f"Ошибка при обработке {wallet_address}: {e}")
            print("Повторная попытка")

async def sem_get_token_balance(semaphore: asyncio.Semaphore, private_key: str):
    async with semaphore:
        return await get_token_balance(private_key)

async def main():
    private_keys = read_private_keys("private_keys.txt")
    semaphore = asyncio.Semaphore(250)

    # Очищаем или создаём txt и csv файлы
    with open("points.txt", "w", encoding="utf-8") as f:
        f.write("")
    with open("points.csv", "w", newline="", encoding="utf-8") as csvfile:
        pass

    async def process_wallet(index: int, pk: str):
        wallet_address, balance = await sem_get_token_balance(semaphore, pk)
        balance_eth = int(balance / 10**18)

        # Записываем в txt
        with open("points.txt", "a", encoding="utf-8") as f:
            f.write(f"{wallet_address} | {balance_eth:<5} | {pk}\n")

        # Записываем в csv
        with open("points.csv", "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([wallet_address, balance_eth, pk])

    tasks = []
    for i, pk in enumerate(private_keys):
        tasks.append(asyncio.create_task(process_wallet(i, pk)))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
