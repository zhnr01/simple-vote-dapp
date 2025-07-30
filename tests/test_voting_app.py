import pytest
from ape.exceptions import ContractLogicError


def test_chairperson(contract, deployer):
    chairperson = contract.chairperson()
    assert chairperson == deployer


def test_addProposal(contract, deployer):
    # Initially, no proposals
    assert contract.amountProposals() == 0
    assert contract.proposals(0).name == ""

    # Add a proposal
    contract.addProposal("beach", sender=deployer)

    # Verify proposal count and name
    assert contract.amountProposals() == 1
    assert contract.proposals(0).name == "beach"


def test_addProposal_fail(contract, accounts):
    # Expect failure because accounts[1] is not the chairperson
    with pytest.raises(ContractLogicError):
        contract.addProposal("beach", sender=accounts[1])


def test_giveRightToVote(contract, deployer, accounts):
    user = accounts[1]

    # Initially, no voters
    assert contract.voterCount() == 0
    assert contract.voters(user).weight == 0

    # Chairperson gives voting rights to user
    contract.giveRightToVote(user, 1, sender=deployer)

    # Verify voting rights were assigned
    assert contract.voterCount() == 1
    assert contract.voters(user).weight == 1

    # Another user (power_user) has no rights yet
    power_user = accounts[2]
    assert contract.voters(power_user).weight == 0

    contract.giveRightToVote(power_user, 9, sender=deployer)
    assert contract.voterCount() == 2
    assert contract.voters(power_user).weight == 9


def test_giveRightToVote_fail(contract, deployer, accounts):
    user = accounts[1]

    # Expect failure because the sender is not the chairperson
    with pytest.raises(ContractLogicError):
        contract.giveRightToVote(user, 1, sender=accounts[1])



def test_vote(contract, deployer, accounts):
    # Add proposals
    contract.addProposal("beach", sender=deployer)
    contract.addProposal("mountain", sender=deployer)

    # Assign voting rights to two users
    user = accounts[1]
    user2 = accounts[2]
    contract.giveRightToVote(user, 1, sender=deployer)
    contract.giveRightToVote(user2, 1, sender=deployer)

    # Check initial voter state for user
    assert contract.voters(user).weight == 1
    assert contract.voters(user).voted is False
    assert contract.voters(user).vote == 0
    assert contract.proposals(0).voteCount == 0

    # User votes for proposal 0 ("beach")
    contract.vote(0, sender=user)

    # Verify vote was counted
    assert contract.proposals(0).voteCount == 1
    assert contract.voters(user).weight == 0
    assert contract.voters(user).voted is True
    assert contract.voters(user).vote == 0

    # Ensure user2's state is unchanged
    assert contract.voters(user2).weight == 1
    assert contract.voters(user2).voted is False
    assert contract.voters(user2).vote == 0

    # Ensure proposal 1 has no votes initially
    assert contract.proposals(1).voteCount == 0

    # User2 votes for proposal 1 ("mountain")
    contract.vote(1, sender=user2)

    # Verify vote was counted
    assert contract.proposals(1).voteCount == 1
    assert contract.voters(user2).weight == 0
    assert contract.voters(user2).voted is True
    assert contract.voters(user2).vote == 1


def test_vote_fail(contract, deployer, accounts):
    # Add proposals
    contract.addProposal("beach", sender=deployer)
    contract.addProposal("mountain", sender=deployer)

    # Give voting rights to user
    user = accounts[1]
    contract.giveRightToVote(user, 1, sender=deployer)

    # User votes for proposal 0 ("beach")
    contract.vote(0, sender=user)

    # User tries to vote again - should fail
    with pytest.raises(ContractLogicError):
        contract.vote(0, sender=user)


def test_winnerName(contract, deployer, accounts):
    # Add proposals
    contract.addProposal("beach", sender=deployer)
    contract.addProposal("mountain", sender=deployer)

    # Assign voting rights to three users
    user1 = accounts[1]
    user2 = accounts[2]
    user3 = accounts[3]
    contract.giveRightToVote(user1, 1, sender=deployer)
    contract.giveRightToVote(user2, 1, sender=deployer)
    contract.giveRightToVote(user3, 1, sender=deployer)

    # Voting
    contract.vote(0, sender=user1)  # 1 vote for beach
    contract.vote(1, sender=user2)  # 1 vote for mountain
    contract.vote(1, sender=user3)  # 2nd vote for mountain

    # Verify vote counts
    assert contract.proposals(0).voteCount == 1
    assert contract.proposals(1).voteCount == 2

    # Verify winning proposal name
    assert contract.winnerName() == "mountain"


import pytest
from ape.exceptions import ContractLogicError


def test_delegate(delegate_contract, deployer, accounts):
    user = accounts[1]
    user2 = accounts[2]

    # Give voting rights
    delegate_contract.giveRightToVote(user, 1, sender=deployer)
    delegate_contract.giveRightToVote(user2, 2, sender=deployer)

    # Initial assertions
    assert delegate_contract.voters(user).weight == 1
    assert not delegate_contract.voters(user).voted
    assert delegate_contract.voters(user).vote == 0

    assert delegate_contract.voters(user2).weight == 2
    assert not delegate_contract.voters(user2).voted
    assert delegate_contract.voters(user2).vote == 0

    # Delegate from user2 → user
    delegate_contract.delegate(user, sender=user2)

    # After delegation
    assert delegate_contract.voters(user).weight == 3
    assert not delegate_contract.voters(user).voted
    assert delegate_contract.voters(user).vote == 0

    assert delegate_contract.voters(user2).weight == 0
    assert delegate_contract.voters(user2).voted
    assert delegate_contract.voters(user2).vote == 0


def test_delegate_2_levels(delegate_contract, deployer, accounts):
    user = accounts[1]
    user2 = accounts[2]
    user3 = accounts[3]

    # Give voting rights
    delegate_contract.giveRightToVote(user, 1, sender=deployer)
    delegate_contract.giveRightToVote(user2, 2, sender=deployer)
    delegate_contract.giveRightToVote(user3, 5, sender=deployer)

    # Initial checks
    assert delegate_contract.voters(user).weight == 1
    assert delegate_contract.voters(user2).weight == 2
    assert delegate_contract.voters(user3).weight == 5

    # Delegate chain: user3 → user2 → user
    delegate_contract.delegate(user, sender=user2)
    delegate_contract.delegate(user2, sender=user3)

    # Final weights
    assert delegate_contract.voters(user).weight == 8
    assert delegate_contract.voters(user2).weight == 0
    assert delegate_contract.voters(user3).weight == 0

    # Voting status
    assert not delegate_contract.voters(user).voted
    assert delegate_contract.voters(user2).voted
    assert delegate_contract.voters(user3).voted


def test_vote_after_delegate_2_levels(delegate_contract, deployer, accounts):
    # Add proposals
    delegate_contract.addProposal("beach", sender=deployer)
    delegate_contract.addProposal("mountain", sender=deployer)

    user = accounts[1]
    user2 = accounts[2]
    user3 = accounts[3]

    # Give rights
    delegate_contract.giveRightToVote(user, 1, sender=deployer)
    delegate_contract.giveRightToVote(user2, 2, sender=deployer)
    delegate_contract.giveRightToVote(user3, 5, sender=deployer)

    # Delegate chain
    delegate_contract.delegate(user, sender=user2)
    delegate_contract.delegate(user2, sender=user3)

    # User votes
    delegate_contract.vote(1, sender=user)

    # Assertions
    assert delegate_contract.voters(user).weight == 0
    assert delegate_contract.voters(user).voted
    assert delegate_contract.voters(user).vote == 1
    assert delegate_contract.proposals(0).voteCount == 0
    assert delegate_contract.proposals(1).voteCount == 8
    assert delegate_contract.winnerName() == "mountain"


def test_delegate_after_vote(delegate_contract, deployer, accounts):
    # Add proposals
    delegate_contract.addProposal("beach", sender=deployer)
    delegate_contract.addProposal("mountain", sender=deployer)

    user = accounts[1]
    user2 = accounts[2]
    user3 = accounts[3]

    # Give rights
    delegate_contract.giveRightToVote(user, 1, sender=deployer)
    delegate_contract.giveRightToVote(user2, 2, sender=deployer)
    delegate_contract.giveRightToVote(user3, 5, sender=deployer)

    # User votes before delegation
    delegate_contract.vote(1, sender=user)

    # Delegations after vote
    delegate_contract.delegate(user, sender=user2)
    delegate_contract.delegate(user2, sender=user3)

    # Final checks
    assert delegate_contract.voters(user).weight == 0
    assert delegate_contract.voters(user).voted
    assert delegate_contract.voters(user).vote == 1

    assert delegate_contract.voters(user2).weight == 0
    assert delegate_contract.voters(user2).voted
    assert delegate_contract.voters(user2).delegate == user

    assert delegate_contract.voters(user3).weight == 0
    assert delegate_contract.voters(user3).voted
    assert delegate_contract.voters(user3).delegate == user2

    # Winner check
    assert delegate_contract.proposals(0).voteCount == 0
    assert delegate_contract.proposals(1).voteCount == 8
    assert delegate_contract.winnerName() == "mountain"

