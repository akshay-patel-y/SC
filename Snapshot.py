import requests
import pandas as pd
import time

# Question 1: Top 20 Addresses
def get_votes_for_proposal(proposal_id, created_lt=0):
    # Define the GraphQL query for fetching votes for a proposal
    endpoint = "https://hub.snapshot.org/graphql"
    params = ""
    if created_lt:    
        params = {
            "query": """
        query Votes($proposal_id: String!, $created_lt: Int!) {
            votes (
                first: 1000
                where: {
                proposal: $proposal_id
                created_lt: $created_lt
                }
            ){
                id
                voter
                created
                choice
                space {
                id
                }
            }
            }
            """,
            "variables": {
                "proposal_id": proposal_id,
                "created_lt": created_lt
            }
        }
    else:
        params = {
            "query": """
        query Votes($proposal_id: String!) {
            votes (
                first: 1000
                where: {
                proposal: $proposal_id
                }
            ){
                id
                voter
                created
                choice
                space {
                id
                }
            }
            }
            """,
            "variables": {
                "proposal_id": proposal_id,
            }
        }
    response = requests.post(endpoint, json=params)
    response.raise_for_status()
    return response.json()["data"]["votes"]

# Set up the API endpoint and query parameters
endpoint = "https://hub.snapshot.org/graphql"
# Define the GraphQL query for fetching closed proposals from the Aave Snapshot space
params = {
    "query": """
        query Proposals {
            proposals(
                first: 1000,
                where: {
                    space: "aave.eth",
                    state: "closed"
                }
            ) {
    id
    author
    space {
      id
      name
    }
  }
        }
    """
}

# Send the GraphQL request to the Snapshot API and parse the JSON response
response = requests.post(endpoint, json=params)
response.raise_for_status()
data = response.json()
# Extract the list of unique addresses that participated in the proposals
participation_rates = {}
# Note: The current implementation of the script will only retrieve the first 1000 proposals and their corresponding votes. The script will not be able to retrieve all the data. The script will need to be amended to follow a similar pattern to handling retrieving more than 1000 votes.
if(len(data["data"]["proposals"]) > 1000):
    print("Data ommitted. Please add support for retrieval of more than 1000 proposals")
for proposal in data["data"]["proposals"]:
    proposal_id = proposal['id']
    created_lt = 0
    votes = get_votes_for_proposal(proposal_id, created_lt)
    dupes = set() # Check if votes are being repeated for any reason. Was not renecessary.
    while votes:
        for vote in votes:
            voter_address = vote['voter']
            if voter_address in dupes:
                continue
            dupes.add(voter_address)
            if voter_address not in participation_rates:
                participation_rates[voter_address] = 0
            participation_rates[voter_address] += 1
        # Set the created_lt parameter to the timestamp of the last vote in the current batch
        created_lt = vote["created"]
        time.sleep(.25)  # Add a .25-second delay before making the next request for the 429 error
        votes = get_votes_for_proposal(proposal_id, created_lt)

# Calculate the participation rate for each address and store it in a list of dictionaries
participation = []
for address in participation_rates:
    count = participation_rates[address]
    rate = count / len(data["data"]["proposals"])
    participation.append({"address": address, "rate": rate})

# Sort the addresses by participation rate and output the top 20
participation_df = pd.DataFrame(participation)
participation_df = participation_df.sort_values("rate", ascending=False)
top_20 = participation_df.head(20)
print(top_20.to_string(index=False))

# Question 2: Find the participation rate for UPenn's Address
upenn_address = "0x070341aA5Ed571f0FB2c4a5641409B1A46b4961b"
upenn_participation = participation_df.loc[participation_df["address"] == upenn_address, "rate"].item()
print("UPenn's Snapshot participation rate for Aave is:", upenn_participation)
