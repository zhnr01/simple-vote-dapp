# @version ^0.3.0 

struct Voter:
    weight: uint256
    voted: bool
    vote: uint256
    delegate: address


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


@external
def delegate(to: address):
    # Ensure the sender has not already voted
    assert not self.voters[msg.sender].voted, "Already voted"

    # Prevent self-delegation
    assert to != msg.sender, "Cannot delegate to yourself"

    # Ensure valid delegate address
    assert to != empty(address), "Invalid delegate address"

    # Mark the sender as having voted and set delegate
    self.voters[msg.sender].voted = True
    self.voters[msg.sender].delegate = to

    # Forward voting weight to the delegate
    self._forwardWeight(msg.sender)


@view
@internal
def _delegated(addr: address) -> bool:
    """
    Internal helper to check if a voter has delegated their vote.
    """
    return self.voters[addr].delegate != empty(address)

@view
@external
def delegated(addr: address) -> bool:
    """
    External view function to check if a given address has delegated.
    """
    return self._delegated(addr)

@view
@internal
def _directlyVoted(addr: address) -> bool:
    """
    Internal helper to check if a voter has directly voted
    without delegating their vote.
    """
    return self.voters[addr].voted and self.voters[addr].delegate == empty(address)


@view
@external
def directlyVoted(addr: address) -> bool:
    """
    External view function to check if a given address has directly voted.
    """
    return self._directlyVoted(addr)

@internal
def _forwardWeight(delegate_with_weight_to_forward: address):
    """
    Forward voting weight from a delegator to the final delegate target.

    Args:
        delegate_with_weight_to_forward: The address whose voting weight
        should be forwarded.
    """
    # Ensure the address has delegated and has weight to forward
    assert self._delegated(delegate_with_weight_to_forward)
    assert self.voters[delegate_with_weight_to_forward].weight > 0

    # Start with their delegate
    target: address = self.voters[delegate_with_weight_to_forward].delegate

    # Follow the chain of delegations (max depth: 4 to prevent loops)
    for i in range(4):
        if self._delegated(target):
            target = self.voters[target].delegate
        else:
            break

    # Transfer the voting weight
    weight_to_forward: uint256 = self.voters[delegate_with_weight_to_forward].weight
    self.voters[delegate_with_weight_to_forward].weight = 0
    self.voters[target].weight += weight_to_forward

    # If target already voted directly, immediately apply weight to their chosen proposal
    if self._directlyVoted(target):
        self.proposals[self.voters[target].vote].voteCount += weight_to_forward
        self.voters[target].weight = 0
