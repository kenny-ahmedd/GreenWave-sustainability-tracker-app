# trigger_pr_merge.py

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()  # only needed locally Heroku does not need it

# Slack configurations
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

# GitHub configuration
GITHUB_REPO = "kenny-ahmedd/GreenWave-sustainability-tracker-app"
GITHUB_WORKFLOW_ID = "dispatch_merge_pr_workflow.yml"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# API endpoints
CONVERSATIONS_HISTORY_URL = "https://slack.com/api/conversations.history"
REACTIONS_GET_URL = "https://slack.com/api/reactions.get"
GITHUB_DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW_ID}/dispatches"

# Headers
slack_headers = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-Type": "application/json"
}
github_headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# File to track processed PR numbers
PROCESSED_PR_FILE = "processed_pr_numbers.txt"


# creates file if it does not exist for processed PR numbers and their timestamps
def create_processed_pr_file():
    if not os.path.exists(PROCESSED_PR_FILE):
        with open(PROCESSED_PR_FILE, "w") as file:
            file.write("")


# call create_processed_pr_file to create the file if it does not exist
create_processed_pr_file()


# method to check the PR mergeability state on GitHub
def check_pr_mergeability_state_on_github(pr_number):
    # only query GitHub if the PR is not already in the file
    if pr_number and not is_pr_already_in_file(pr_number):
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}", headers=github_headers)
        if response.status_code == 200:
            pr_data = response.json()
            # print(pr_data)
            if pr_data.get("merged") is True:
                return "merged"
            elif pr_data.get("mergeable_state") == "clean":
                return "clean"  # PR is clean and can be merged
            elif pr_data.get("mergeable_state") == "dirty":
                return "dirty"  # PR is dirty and cannot be merged
            elif pr_data.get("mergeable_state") == "unknown":
                return "unknown"  # PR mergeability is being checked
            elif pr_data.get("mergeable_state") == "blocked":
                return "blocked"  # PR is blocked and cannot be merged
            elif pr_data.get("mergeable_state") == "behind":
                return "behind"  # PR is behind the base branch
            else:
                return "other"  # Other states
        return "not_found"


# returns True if PR is mergeable and False otherwise
def is_pr_mergeable(pr_number):
    mergeable_state = check_pr_mergeability_state_on_github(pr_number)
    if mergeable_state == "clean" and not is_pr_merged(pr_number):
        return True  # PR is clean and can be merged
    return False


# returns True if PR is already merged and False otherwise
def is_pr_merged(pr_number):
    mergeable_state = check_pr_mergeability_state_on_github(pr_number)
    if mergeable_state == "merged":
        return True  # PR is merged
    return False


# waits for PR to be merged and returns True if merged and False otherwise
def wait_for_pr_to_merge(pr_number, timeout=100):  # Timeout is 120 seconds
    start_time = time.time()
    while time.time() - start_time <= timeout:
        if check_workflow_status(pr_number):
            print("checking workflow status")
            return True  # Workflow has finished executing
        time.sleep(1)  # Wait for 5 seconds before checking again
    return False  # Timeout reached, workflow execution not completed


def check_workflow_status(pr_number):
    # Get the list of workflow runs for the repository
    response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs", headers=github_headers)
    if response.status_code == 200:
        workflow_runs = response.json()["workflow_runs"]
        # print(workflow_runs)
        for run in workflow_runs:
            if f"Merge pull request #{pr_number}" in run["head_commit"]["message"] or \
               f"Merge pull request #{pr_number}" in run["display_title"]:
                if run["status"] == "completed" and run["conclusion"] == "success":
                    print(f"Workflow for PR #{pr_number} has completed.")
                    return True  # Workflow has finished executing
    return False  # Workflow execution not completed or not found


# checks if PR is merged and returns True if merged and False otherwise
def check_pr_merged(pr_number):
    response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/pulls/{pr_number}", headers=github_headers)
    if response.status_code == 200:
        pr_data = response.json()
        return pr_data.get("merged", False)
    else:
        print(f"Failed to retrieve PR data. Status: {response.status_code}, Response: {response.text}")
        return False


# method checks if PR is already in file (meaning merged)
def is_pr_already_in_file(pr_number):
    # Check if the PR is already in the file
    processed_pr_numbers = load_latest_processed_pr_data()
    if pr_number in processed_pr_numbers:
        print(f"PR #{pr_number} is already processed.")
        return True  # PR is already processed and therefore already merged
    else:
        return False


# method to save the processed PR number to the file with their timestamps
def save_processed_pr_number(pr_number, message_ts):
    print(f"local. Saving PR #{pr_number} and {message_ts} to the file.")
    with open(PROCESSED_PR_FILE, "a") as file:
        file.write(f"{pr_number},{message_ts}\n")


def load_latest_processed_pr_data():
    try:
        with open(PROCESSED_PR_FILE, "rb") as file:
            # Attempt to go to the second-to-last byte of the file
            file.seek(-2, os.SEEK_END)

            # Keep moving backwards until you find the newline character
            while file.read(1) != b'\n':
                file.seek(-2, os.SEEK_CUR)

            # Read the last line
            last_line = file.readline().decode()

    except FileNotFoundError:
        return {}
    except OSError:
        # The OSError is expected in cases where the file is empty or too small,
        # so handle it by returning an empty dictionary.
        return {}

    parts = last_line.strip().split(',')
    if len(parts) == 2:
        # Return the dictionary with the last processed PR number and its timestamp
        return {parts[0]: parts[1]}
    else:
        return {}


# Function to find the latest PR message in the channel and return it
def find_latest_pr_opened_message(channel_id, latest_ts=None):
    params = {"channel": channel_id, "limit": 900}
    if latest_ts:
        params["oldest"] = latest_ts  # Fetch messages newer than the latest_ts
    response = requests.get(CONVERSATIONS_HISTORY_URL, headers=slack_headers, params=params)
    if response.status_code == 200:
        messages = response.json().get("messages", [])
        for message in messages:
            if "text" in message and "Pull Request Opened" in message["text"]:
                return message
            if "attachments" in message:
                for attachment in message["attachments"]:
                    if "pretext" in attachment and "Pull Request Opened" in attachment["pretext"]:
                        return message
    else:
        print(f"Failed to retrieve messages. Status code: {response.status_code}")
    return None


# function to get the reaction count on a message from a Slack channel
def get_reaction_count(message_ts, channel_id):
    params = {"channel": channel_id, "timestamp": message_ts}
    response = requests.get(REACTIONS_GET_URL, headers=slack_headers, params=params)
    if response.status_code == 200:
        data = response.json()
        reactions = data.get('message', {}).get('reactions', [])
        for reaction in reactions:
            if reaction['name'] == '+1':
                return reaction['count']
    return 0


def trigger_github_workflow(pr_number):
    data = {
        "ref": "main",
        "inputs": {
            "prNumber": str(pr_number)
        }
    }
    response = requests.post(GITHUB_DISPATCH_URL, headers=github_headers, json=data)
    if response.status_code == 204:
        print("Successfully triggered the GitHub workflow.")
    else:
        print(f"Failed to trigger the GitHub workflow. Status: {response.status_code}, Response: {response.text}")


def extract_pr_number(message):
    if "attachments" in message:
        for attachment in message["attachments"]:
            if "title" in attachment and "Pull Request #" in attachment["title"]:
                return attachment["title"].split("#")[1]
    return None


def continuously_check_reactions(threshold=1):  # Threshold is 1 thumbs-up reaction by default (can be changed)
    while True:
        # load processed PR numbers from the file to avoid processing the same PR multiple times
        # to prevent redundant workflow triggers
        processed_pr_numbers = load_latest_processed_pr_data()
        # extact the latest timestamp from the processed PR numbers
        latest_ts_from_file = max([float(ts) for ts in processed_pr_numbers.values()]) if processed_pr_numbers else None

        # Find the latest PR message in the channel
        latest_pr_message = find_latest_pr_opened_message(SLACK_CHANNEL_ID, latest_ts_from_file)
        # print(latest_pr_message)
        if latest_pr_message:  # If a PR message is found in the channel
            # Extract the PR number from the message
            pr_number = extract_pr_number(latest_pr_message)

            message_ts = latest_pr_message.get("ts")  # timestamp of the message

            # check if the PR is found in messages and not processed already (not in the file)
            if pr_number and pr_number not in processed_pr_numbers:
                # Get the thumbs-up reaction count on the message
                message_id = latest_pr_message.get("ts")  # timestamp of the message
                thumbs_up_count = get_reaction_count(message_id, SLACK_CHANNEL_ID)  # get the reaction count
                print(f"Thumbs-up reaction count: {thumbs_up_count}")
                # if the reaction count is greater than or equal to the threshold, trigger the GitHub workflow
                # this means everyone has approved the PR
                if thumbs_up_count >= threshold:
                    # if PR number is extracted successfully (redundant check but safe)
                    if pr_number and not is_pr_merged(pr_number):  # check if PR is not already merged
                        if is_pr_mergeable(pr_number):
                            trigger_github_workflow(pr_number)
                        if wait_for_pr_to_merge(pr_number):  # wait for PR to be merged
                            if check_pr_merged(pr_number):  # check if merging is completed
                                # print saving PR number and timestamp to the file
                                print("saving PR number and timestamp to the file")
                                save_processed_pr_number(pr_number, message_ts)  # save the PR number to the file
                            else:
                                print(f"PR #{pr_number} merging failed.")
                        else:
                            print(f"PR #{pr_number} is not mergeable or timed out waiting for merge.")
                    else:
                        print(f"PR #{pr_number} is already merged.")
            else:
                print(f"PR number: {pr_number} already processed and on file.")
        else:
            print("No 'Pull Request Opened' message found in the channel.")
        time.sleep(60)  # Check every minute (60 seconds)


if __name__ == "__main__":
    continuously_check_reactions()
