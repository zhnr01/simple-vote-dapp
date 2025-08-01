from ape import accounts, project
import os
import sys
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv

class VotingWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.proposals = ["---", "beach", "mountain"]
        load_dotenv()

        self.title("Voting Blockchain App")

        # Label
        self.label = tk.Label(self, text="Voting Blockchain App", font=("Arial", 14))
        self.label.pack(pady=10)

        # Combobox
        self.combobox = ttk.Combobox(self, values=self.proposals)
        self.combobox.current(0)
        self.combobox.pack(pady=5)

        # Button
        self.button = tk.Button(self, text="Vote", command=self.vote)
        self.button.pack(pady=10)

    def vote(self):
        proposal = self.combobox.get()
        proposal_index = self.proposals.index(proposal) - 1
        if proposal == "---":
            print("Please select a valid proposal.")
            return

        # Example blockchain voting logic
        password = os.environ.get("VOTER_PASSWORD")
        address = os.environ.get("VOTING_APP_ADDRESS")
        voter_account = os.environ.get("VOTER_ACCOUNT")

        voter = accounts.load(voter_account)
        voter.set_autosign(True, passphrase=password)

        contract = project.VotingApp.at(address)
        contract.vote(proposal_index, sender=voter)
        print(f"Voted for {proposal}")


def main():
    app = VotingWidget()
    app.mainloop()
