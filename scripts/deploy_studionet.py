import time
import json
import genlayer_py
from eth_account import Account
from genlayer_py.types.transactions import TransactionStatus

def main():
    account = Account.create()
    client = genlayer_py.create_client(chain=genlayer_py.studionet, account=account)
    print(f"Deployer account: {account.address}")
    
    fund_tx = client.fund_account(account.address, 2 * 10**18)
    print("Funded account:", fund_tx.hex() if isinstance(fund_tx, bytes) else fund_tx)
    time.sleep(2)
    print("Balance:", client.get_balance(account.address))

    contract_code = open("contracts/contract.py", "r", encoding="utf-8").read()
    print("Deploying contract to studionet...")
    deploy_tx = client.deploy_contract(contract_code)
    print("Deploy TX hash:", deploy_tx.hex() if isinstance(deploy_tx, bytes) else deploy_tx)

    receipt = client.wait_for_transaction_receipt(deploy_tx, status=TransactionStatus.ACCEPTED, interval=3000, retries=50)
    contract_address = receipt.get("to")
    print(f"Contract deployed successfully at: {contract_address}")

    # Confirm initial count
    cnt = client.read_contract(address=contract_address, function_name="get_event_count", args=[])
    print(f"Initial get_event_count: {cnt}")
    return contract_address, account

if __name__ == "__main__":
    main()
