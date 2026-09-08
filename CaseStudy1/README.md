This doc is for Case Study 1: Build a GenSearch-Powered Workflow.

**What you built and why you picked it**

A daily monitor script which runs the same auto GenSearch query to track any macroeconomic and competitive risks that businesses reported in recent filings. This project was chosen because it provides immediate, actionable business value. By tracking these factors, this would offer a layer of protection, as an organization would be able to indentify minor risks before they escalate. Thereby allowing businesses to respond quickly to market shifts and mitigate potential impacts before they become too severe.

**How to run it (env vars, dependencies, example command)**

`Env Vars:
ALPHASENSE_API_KEY=your_api_key
ALPHASENSE_CLIENT_ID=your_client_id_here
ALPHASENSE_CLIENT_SECRET=your_client_secret_here
ALPHASENSE_EMAIL=your_email_here
ALPHASENSE_PASSWORD=your_password_here`

Dependencies:
`certifi            2026.7.22
charset-normalizer 3.5.1
idna               3.19
pip                26.2.1
python-dotenv      1.2.3
requests           2.34.2
setuptools         82.0.0
urllib3            2.7.0`

Example Command:
-Ensure the environment variables are set up in the root of your project (`.env file`)
-install dependencies (`pip install -r requirements.txt`)

-Run script (`python main.py`)

**One or two design decisions you made and the trade-offs (e.g., why you picked
auto over thinkLonger, why you polled vs. streamed, how you handled the
citation format)**

_Auto over thinkLonger:_ I used auto over thinkLonger because this monitoring script provides quick, high-level summaries of daily risk factors. The primary trade-off here is speed versus analytical depth. While thinkLonger, deepResearch would evaluate more sources and return a more in-depth analysis, this would significantly increase the API response latency. Since the script is designed to give quick, actionable data on risk items in the market, auto GenSearch provides the right balance of speed and sufficient detail. 

_Exit After Execution over Continuously Background Loop:_ I decided to have the script exit immediately after completing execution rather than continuously running in the background via a prolonged sleep loop `time.sleep(86400)`. The primary trade-off here is manual execution versus continuous automation. Since this is a local environment prototype, keeping a persistent background process introduces too many silent risks and failings if there is an API timeout or a network drop crashes the script. By designing a single-run script, this preserves local system resources, any failings are seen immediately, and allows the user to manually trigger the daily check reliably.

**One thing that surprised you, broke, or didn't work the way you expected — and how you debugged it**

After completing my script, I was reviewing it and realized I didn't have any parsing/rendering for the citations in the markdown files. I anticipated this causing UX issues when the user went to view the markdown file as it would show unrendered citation strings instead of clean, clickable UI references which would degrade the UX and readability of the reports.

After reviewing AlphaSense's Dev Portal Doc, specifically the working with responses doc: https://developer.alpha-sense.com/agent-api/response-parsing
I added the regex patterns to my script using a custom `render_citations` function and had the markdowns be parsed right before writing them onto the `STATE_FILE`. This allows the reports to be read easier by the user.

**If you had another week, what you'd improve or harden for production use**

_Expand Trend Analysis:_ Increase the duration of time to get a better picture of what changed since the last risk tracking query. By comparing an entire week's worth of output and compare it to the most recent response, businesses would be even more empowered to act on reliable data from their latest risk tracking query. 

This would paint a more accurate picture of risks in the market as well as show risks trends escalating within the market. Any organization would be better protected using this script as they would be able to properly act with reliable, accurate data and protect themselves from these increasing risks in the market.

_Production Hardening:_ To make this script more enterprise-ready, I would move it from a local execution environment to a managed cloud scheduler (AWS Lambda triggered by EventBridge). I would also add error handling to catch API timeouts or rate limits to ensure quicker troubleshooting/debugging in the event anything breaks in the script. Lastly, I would transition from saving the state in a local file to a structured database (AWS DynamoDB, RDS) to ensure the historical comparisons are completely reliable and have high availability for users.

======================================================================================================================

**BONUS/STRETCH**

**Runbook for Auth Failure (Python)**

Severity: High. It blocks the entire script from running.

Symptoms: Receive a `403` status error when attempting to connect to Alpha Sense Auth API. Example:
`requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: https://api.alpha-sense.com/auth`

Root Cause: Authentication credentials are either incorrect, expired, or incorporated incorrectly in the script via the environment variables such as: API keys, client IDs, secrets, usernames, email, or passwords.

Fix: 
1. Verify the current environment variables in your local `.env` file and confirm they are all correct with no typos or trialing spaces.
Example:
`# env vars
API_KEY       = os.environ["ALPHASENSE_API_KEY"]
CLIENT_ID     = os.environ["ALPHASENSE_CLIENT_ID"]
CLIENT_SECRET = os.environ["ALPHASENSE_CLIENT_SECRET"]
EMAIL         = os.environ["ALPHASENSE_EMAIL"]
PASSWORD      = os.environ["ALPHASENSE_PASSWORD"]`

2. Check Dotenv initialization: ensure the script executes `load_dotenv()` before attempting to read environment variables via `os.environ[] ` 
3. Test Credentials: If variables are correct, verify with account administrator that API access permissions and user access are active. 
4. Rerun script. A successful authentication will now bypass the `403` error and give the following output: `Authenticated successfully. Access token created.`

**Add filters (companies, date ranges, industries) and explain what
the filter changed.**

By adding a `filters` variable to the script, the queries were now able to query the risks for Apple, Microsoft and Google in the past 24 hours by using the parameters `companies`, `date`, and `"preset":  "LAST_24_HOURS"`. This allowed the script to pull specific risk information over those companies. Thereby allowing the user to make better informed decisions based upon the risks the companies have listed.
