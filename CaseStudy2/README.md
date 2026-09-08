This doc is for Case Study 2: Diagnosing a Broken Client Integration
 

**It hangs forever**

Diagnosis: High confidence. Caused by logic error in the polling loop condition: `if result.progress > 1.0: break`
Because the progress field will never go over 1.0, the condition `1.0 > 1.0` will always be False. The script skips the break statement and loops infinitely.

Fix: Update the condition to include 1.0 so it can catch and break when progress reaches completion:
`if result.progress >= 1.0:
    break`

**the citations are broken.**

Diagnosis: Very Confident. The client isn't rendering the citations. I'm not seeing the Regex pattern in the client's script so it isn't rendering the citations. 

Fix: The client needs to implement the Regex expressions to extract citations from GenSearch markdown responses. Add a `render_citations_html` function that calls these regex pattern and call the function right before writing the markdown to the out_path file so the markdowns will now contain rendered citations with clean, clickable HTML links.

**it's slower than the docs say it should be**

Diagnosis: Very Confident. Polling overhead from each ticker. The polling occurs for each ticker in a single-threaded loop with the polling interval being 2 seconds. There is no API performance lag but simply an effect of serial polling each ticker that is causing bottle necking as it polls through every ticker in the `TICKERS` list.

Fix: Use concurrent requests so the client can poll multiple tickers simultaneously rather than waiting on a single-threaded loop. `ThreadPoolExecutor` is a great way to run multiple tickers simultaneously. Add a `process_single_ticker` function then call the `ThreadPoolExecutor` as executor to run all tickers at once.

**The answers are wrong**

Diagnosis: Confident. Classifying this as LLM behavior rather than an API bug. The client's prompt "Summarize the latest financial performance and analyst outlook for {ticker}." is very open-ended and broad. This can lead to generic summaries that may not match the data points the client is expecting to get.

Fix: Update the prompt so it's more specific to a data point the client is wanting from the query. Like a specific KPI or business metric (example: "Summarize the latest quarterly revenue growth rate for {ticker}, citing the specific page and number."). Another option if the client is wanting the answer to be more detailed, then they should use `thinkLonger` or `deepResearch` mode instead of `auto` for their queries.

**it works for some tickers but not others**

Diagnosis: Confident. Ruled out that the client likely has an invalid, mistyped, unsupported ticker in their list, or a company without indexed filings in the content library. The API returns a NO_DOC error code and sets the markdown field to null as it isn't generated. The current script only says no content returned, skipping if a ticker contains the `NO_DOC` error.

Fix: Update the else block error log for the markdowns so it tells the client why a ticker failed. `current else block:
print(f"[{ticker}] No content returned, skipping.")`

update the else block to:

    `else:
        error_code = getattr(result, "error", {}).get("code", "UNKNOWN") if result else "NO_RESPONSE"
        if error_code == "NO_DOCS":
            print(
                f"[{ticker}] Warning: Query completed successfully, but no indexed filings matched this entity. Skipping.")
        else:
            print(f"[{ticker}] Warning: No content returned (API Error Code: {error_code}). Skipping.")`

**EMAIL TO CLIENT**

Hello,

Thank you for reaching out to AlphaSense support. I'm sorry to hear you're experiencing issues using our GenSearch. I want you to know I've thoroughly investigated your issues so they can be resolved as quickly and efficiently as possible!

See below this paragraph as I go through each of the issues you listed and what you can do to resolve them. I've attached the updated script. After reading the resolutions, please let me know if you have any questions or need further clarifications.

**It hangs forever.** 
This is due to a logic error in your script with the polling loop. The polling value will never go over `1.0`, and currently you have the loop logic set for `if result.progress > 1.0: break`
this will always be False and so the loop will never break. To resolve this issue, update the if block to: 
`if result.progress >= 1.0:
    break`

**the citations are broken.**
Because the raw markdown citations weren't being rendered before being written to your disk, your UI were displaying raw link strings. I integrated the official regex patterns from our documentation to transform them into clean, clickable HTML links. Here is the link to that documentation: https://developer.alpha-sense.com/agent-api/response-parsing#rendering-citations

**it's slower than the docs say it should be**
This is due to a single-threaded loop for each ticker. Thus, creating a massive sequential bottleneck when processing each ticker. I've refactored your script to include `ThreadPoolExecutor`, allowing however many tickers are in the `TICKERS` list to run concurrently. Please note that if too many tickers are in the list this may cause the queries to run slow. I would recommend keeping `max_workers` set to 5-10 if the `TICKERS` list scales up to dozens or more.

**The answers are wrong**
This is due to your prompt not being specific enough to the data you are expecting. I would advise to update the prompt to a specific KPI or metric you are expecting to receive from the tickers. In the updated script, I've inputted an example of this. If you are expecting more detailed answers then I would advise switching your mode from `auto` to `thinkLonger` or `deepResearch`. Please know that this will increase the time it takes to poll each ticker in your query.

**it works for some tickers but not others**
For tickers with no indexed filings for your query, the API returns a `NO_DOCS` error and sets the markdown to null. Your original script failed silently, but the API request was successful, there were just no indexed files that matched your query for that ticker. I've added explicit error-code logging so you can know instantly why a ticker was skipped. 

=====================================================================================================================

BONUS/STRETCH

**Runbook for broken citations**

Issue Name: Broken or Unreadable Citations
Severity: Medium (Non-fatal to code execution but lessens UX for clients and report understanding)
Applies To: Integrations using GenSearch API where markdown responses are unreadable in client's UI as they were written directly to files before being rendered.

**Symptoms & Impact**
Symptoms: Users or automated reports display raw markdown citation strings (`e.g., [[38 • 10-K]](https://research.alpha-sense.com?docid=...)`) as plain text instead of clickable UI elements or hyperlinks.

Impact: End-users cannot easily navigate to source documents from the generated files or web interface.

**Root Cause**
GenSearch API returns responses in structured markdown containing inline citation hyperlinks. If a client's script saves result to the markdown directly to disk without rendering, standard text renderers fail to display them as interactive elements.

**Step-by-Step Resolution / Fix**
To resolve this, the application must process the raw markdown string with regex patterns to convert them into clickable HTML links right before writing the output.

Implementation Guide (Python)
Add the official regex patterns from AlphaSense's documentation page: https://developer.alpha-sense.com/agent-api/response-parsing#rendering-citations

EXAMPLE

`def render_citations_html(markdown: str) -> str:
    """Convert GenSearch citation syntax to HTML anchor tags using Regex Patterns from AlphaSense."""
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
    return html`

**Applying the Fix in Your File Write Loop**

Ensure `render_citations_html()` is called on `result`
markdown before writing to output destination

`EXAMPLE
    `if result and result.markdown:
        out_path = OUTPUT_DIR / f"{ticker}.md"
        # transform citations
        rendered_content = render_citations_html(result.markdown)`

        out_path.write_text(rendered_content, encoding="utf-8")
        print(f"[{ticker}] Saved → {out_path}")

`# citation rendering function
def render_citations_html(markdown: str) -> str:
    """Convert GenSearch citation to clickable HTML links using Regex Patterns from AlphaSense."""
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
    return html`

**Verification**
1. Run sample query against any ticker.
2. Open the generated `.md` or `.html` report file.
3. Verify the citation brackets are now active and clickable links pointing to research.alpha-sense.com with the correct docid and page parameters.

**Suggest a change to our docs or developer experience that would have prevented this
ticket from being filed in the first place.**

Enhance NO_DOCS Error Transparency & Client-Side Guidance
The Problem: When the GenSearch returns an empty result due to missing files or indexes not existing, the API returns a `200 OK` response accompanied by a nested error object `"code", "NO_DOCS"` while setting the markdown to `null`. To developers building quick scripts or integrations a `200 OK` response with a null body can be easily mistaken for a server-side bug, leading to unnecessary support tickets.

Proposed Fix: Update the AlphaSense developer Quick Start documentation to include what the `NO_DOCS` error is and how it makes markdowns `null`. Instead of having the scrpit fail silently or treating `NO_DOCS` like a generic error, the documentation should include specficially checking for the error in the polling loop so the error can be explained to the user to better understand it.
EXAMPLE:
`if result and result.markdown:
    # Save markdown logic
else:
    error_code = getattr(result, "error", {}).get("code", "UNKNOWN") if result else "NO_RESPONSE"
    if error_code == "NO_DOCS":
        print(f"[{ticker}] Warning: Query completed successfully, but no indexed filings matched this entity. Skipping.")
    else:
        print(f"[{ticker}] Warning: No content returned (API Error Code: {error_code}). Skipping.")`
In the Quick Start documentation, add a clear note explaining the `NO_DOCS` error doesn't mean the API request failed or was broken, it simply means that the API request was successful but their were no indexed files to match the query.
