from ape import accounts, project
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    # Get password from .env
    password = os.getenv("MY_PASSWORD")
    if not password:
        raise ValueError("MY_PASSWORD not set in .env file")

    # Load your development account (make sure you've imported it before)
    dev = accounts.load("dev")

    # Enable auto-signing with password
    dev.set_autosign(True, passphrase=password)

    # Deploy VotingApp contract
    contract = project.VotingApp.deploy(sender=dev)

    print(f"VotingApp deployed at: {contract.address}")
