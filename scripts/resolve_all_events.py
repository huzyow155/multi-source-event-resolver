import time
import json
import genlayer_py
from eth_account import Account
from genlayer_py.types.transactions import TransactionStatus

CONTRACT_ADDRESS = "0xe594F4FCD0A55fE72281c99F1B7872993039a4f8"

def run_event(client, event_id, desc, url1, url2):
    print(f"\n==========================================")
    print(f"Resolving: {event_id}")
    print(f"Description: {desc}")
    print(f"URL 1: {url1}")
    print(f"URL 2: {url2}")
    
    tx = client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="resolve_event",
        args=[event_id, desc, url1, url2]
    )
    tx_hex = tx.hex() if isinstance(tx, bytes) else str(tx)
    print(f"Transaction submitted! Hash: {tx_hex}")
    
    receipt = client.wait_for_transaction_receipt(tx, status=TransactionStatus.ACCEPTED, interval=3000, retries=50)
    print(f"Transaction confirmed! Status: {receipt.get('status')}")
    
    ev = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_event", args=[event_id])
    print(f"Stored Event Record:")
    for k, v in ev.items():
        print(f"  {k}: {v}")
    return tx_hex, ev

def main():
    account = Account.create()
    client = genlayer_py.create_client(chain=genlayer_py.studionet, account=account)
    print(f"Client account: {account.address}")
    client.fund_account(account.address, 3 * 10**18)
    time.sleep(2)
    print(f"Balance: {client.get_balance(account.address)}")

    # 1. Event 1 (HAPPENED)
    # Testing with clean, reliable open encyclopedic/documentation sources
    # Python language created by Guido van Rossum
    tx1, ev1 = run_event(
        client,
        event_id="evt-python-creator-guido",
        desc="The Python programming language was created by Guido van Rossum",
        url1="https://raw.githubusercontent.com/python/cpython/main/README.rst",
        url2="https://en.wikipedia.org/wiki/Guido_van_Rossum"
    )

    # 2. Event 2 (NOT_HAPPENED)
    # A clearly false claim: Neil Armstrong landed on Mars in 1969
    tx2, ev2 = run_event(
        client,
        event_id="evt-armstrong-mars-1969",
        desc="Astronaut Neil Armstrong landed on planet Mars during the 1969 space mission",
        url1="https://en.wikipedia.org/wiki/Neil_Armstrong",
        url2="https://raw.githubusercontent.com/nasa/nasa-3d-resources/master/README.md"
    )

    # 3. Event 3 (UNRESOLVED)
    # Reuters paywall / inaccessible or non-existent claim / broken source
    tx3, ev3 = run_event(
        client,
        event_id="evt-spacex-reuters-unresolved",
        desc="SpaceX caught the Super Heavy booster of Starship during flight 5",
        url1="https://en.wikipedia.org/wiki/Starship_integrated_flight_test_5",
        url2="https://www.reuters.com/technology/space/spacex-launches-fifth-starship-test-flight-aims-booster-catch-2024-10-13/"
    )

    # Check final count
    final_count = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_event_count", args=[])
    print(f"\n==========================================")
    print(f"Final get_event_count: {final_count}")

if __name__ == "__main__":
    main()
