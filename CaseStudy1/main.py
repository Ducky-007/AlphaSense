import os
import re
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# file to store the state between runs
STATE_FILE = Path("last-run.json")

# env vars
API_KEY       = os.environ["ALPHASENSE_API_KEY"]
CLIENT_ID     = os.environ["ALPHASENSE_CLIENT_ID"]
CLIENT_SECRET = os.environ["ALPHASENSE_CLIENT_SECRET"]
EMAIL         = os.environ["ALPHASENSE_EMAIL"]
PASSWORD      = os.environ["ALPHASENSE_PASSWORD"]

AUTH_URL       = "https://api.alpha-sense.com/auth"
GRAPHQL_URL    = "https://api.alpha-sense.com/gql"

def render_citations(markdown: str) -> str:
    """Convert raw GenSearch citations in markdown to clickable HTML links."""
    # Short name format: [[38 • S1/A]](url)
    html = re.sub(
        r'\[\[(\d+)\s*•\s*([^\]]+)\]\]\((https?://[^\)]+)\)',
        r'<a href="\3" target="_blank" rel="noopener noreferrer" class="citation" title="Source \1: \2">[\1 • \2]</a>',
        markdown
    )
    # Number-only format: [[311]](url)
    html = re.sub(
        r'\[\[(\d+)\]\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener noreferrer" class="citation" title="Source \1">[\1]</a>',
        html
    )
    # Full metadata format: [[312] S1/A • Roblox Corp...]
    html = re.sub(
        r'\[\[(\d+)\]\s*([^\]]*)\]\((https?://[^\)]+)\)',
        r'<a href="\3" target="_blank" rel="noopener noreferrer" class="citation" title="\2">[\1]</a>',
        html
    )
    return html

# for running and polling GenSearch
def run_gensearch(prompt, headers, filters=None):
    """Submits GenSearch auto query and polls until complete, returning the markdown."""

    #adds filters list
    inp_data = {"prompt": prompt}
    if filters:
        inp_data["filters"] = filters

    # Submit the query
    mutation = """
    mutation GenSearch($input: GenSearchInput!) {
      genSearch {
        auto(input: $input) {
          id
        }
      }
    }
    """
    search_response = requests.post(
        GRAPHQL_URL,
        headers=headers,
        json={"query": mutation, "variables": {"input": inp_data}},
    )
    search_response.raise_for_status()
    conversation_id = search_response.json()["data"]["genSearch"]["auto"]["id"]

    # Poll for the answer
    poll_query = """
    query Query($conversationId: String!) {
      genSearch {
        conversation(id: $conversationId) {
          markdown
          progress
          error { code }
        }
      }
    }
    """

    while True:
        poll_response = requests.post(
            GRAPHQL_URL,
            headers=headers,
            json={"query": poll_query, "variables": {"conversationId": conversation_id}},
        )
        poll_response.raise_for_status()

        conversation = poll_response.json()["data"]["genSearch"]["conversation"]
        progress = conversation["progress"]

        if conversation.get("error"):
            raise RuntimeError(f"GenSearch error: {conversation['error']['code']}")

        if progress >= 1.0:
            return conversation["markdown"]

        time.sleep(2)

if __name__ == "__main__":
    # auth
    auth_response = requests.post(
        AUTH_URL,
        headers={"x-api-key": API_KEY, "Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "password",
            "username": EMAIL,
            "password": PASSWORD,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    auth_response.raise_for_status()
    access_token = auth_response.json()["access_token"]
    print("Authenticated successfully.\n Access token created.\n")

    # use access token for GQL headers
    gql_headers = {
        "x-api-key": API_KEY,
        "clientid": CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # check for prev run
    prev_markdown = None
    if STATE_FILE.exists():
        prev_data = json.loads(STATE_FILE.read_text())
        prev_markdown = prev_data.get("markdown")
        print("Found previous run data. Will compare against today's results.\n")
    else:
        print("No previous run data found. This must be the first run.\n")

    # adds filters
    my_filters = {
        "companies": {
            "include": ["AAPL", "MSFT", "GOOGL"]
        },
        "date": {
            "preset": "LAST_24_HOURS"
        }
    }

    # run today's query
    print("Fetching today's risk data...")
    today_prompt = "what competitive risks have businesses reported in recent filings?"
    today_markdown = run_gensearch(today_prompt, gql_headers, filters=my_filters)

    # compare data if previous data exists
    if prev_markdown:
        print("Analyzing changes since last run...")

        # pass BOTH prev and today's markdown into a fresh prompt for analysis
        # else just print today's markdown
        compare_prompt = (
            "Compare the market risks identified in the 'Previous Report' with the 'Today Report'. "
            "Identify what specific risks escalated, decreased, or are newly reported.\n\n"
            f"--- PREVIOUS REPORT ---\n{prev_markdown}\n\n"
            f"--- TODAY REPORT ---\n{today_markdown}"
        )

        compare_res = run_gensearch(compare_prompt, gql_headers)
        rendered_content = render_citations(compare_res)
        print("\n" + "=" * 60)
        print("RISK TREND ANALYSIS (DAY_TO_DAY CHANGES)")
        print("=" * 60)
        print(rendered_content)
    else:
        # for baseline markdown
        today_rendered_content = render_citations(today_markdown)
        print("\n" + "=" * 60)
        print("TODAY'S RISK REPORT (BASELINE)")
        print("=" * 60)
        print(today_rendered_content)

    # save today's state for tomorrow
    # saving today's raw markdown for clean historical data
    STATE_FILE.write_text(json.dumps({"markdown": today_markdown}))
    print("State saved. Ready for the next run.")
