# @version ^0.3.0
struct Voter:
    weight: uint256
    voted: bool
    vote: uint256

struct Proposal:
    name: String[100]
    voteCount: uint256

voters: public(HashMap[address, Voter])
proposals: public(HashMap[uint256, Proposal])
voterCount: public(uint256)
chairperson: public(address)
amountProposals: public(uint256)


MAX_NUM_PROPOSALS: constant(uint256) = 3

@external
def __init__():
    self.chairperson = msg.sender

@external
def addProposal(_proposalName: String[100]):
    # Only the chairperson can add proposals
    assert msg.sender == self.chairperson, "Only chairperson can add proposals"

    # Get the current proposal index
    i: uint256 = self.amountProposals

    # Store the new proposal
    self.proposals[i] = Proposal({
        name: _proposalName,
        voteCount: 0
    })

    # Increase the proposal count
    self.amountProposals += 1

@external
def giveRightToVote(voter: address, _weight: uint256):
    # Only the chairperson can give voting rights
    assert msg.sender == self.chairperson, "Only chairperson can give voting rights"

    # Ensure the voter has not already voted
    assert not self.voters[voter].voted, "Voter has already voted"

    # Ensure the voter does not already have a voting weight
    assert self.voters[voter].weight == 0, "Voter already has voting rights"

    # Assign voting weight
    self.voters[voter].weight = _weight

    # Increment the voter count
    self.voterCount += 1


@external
def vote(proposal: uint256):
    # Ensure the voter has not already voted
    assert not self.voters[msg.sender].voted, "Already voted"

    # Ensure the proposal exists
    assert proposal < self.amountProposals, "Invalid proposal"

    # Record the voter's choice
    self.voters[msg.sender].vote = proposal
    self.voters[msg.sender].voted = True

    # Add the weight of the voter's vote to the proposal
    self.proposals[proposal].voteCount += self.voters[msg.sender].weight

    # Reset the voter's weight to prevent double voting
    self.voters[msg.sender].weight = 0


@view
@internal
def _winningProposal() -> uint256:
    winning_vote_count: uint256 = 0
    winning_proposal: uint256 = 0

    # Loop through all proposals to find the one with the most votes
    for i in range(MAX_NUM_PROPOSALS):
        if self.proposals[i].voteCount > winning_vote_count:
            winning_vote_count = self.proposals[i].voteCount
            winning_proposal = i

    return winning_proposal


@view
@external
def winningProposal() -> uint256:
    return self._winningProposal()


@view
@external
def winnerName() -> String[100]:
    return self.proposals[self._winningProposal()].name
