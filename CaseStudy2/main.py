"""
Batch GenSearch report generator.
Loops over a list of tickers, runs a GenSearch query for each, and saves results to markdown
files.
"""
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# The client code here implements authentication and search with status polling
from client import AlphaSenseClient

TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
WORKERS = len(TICKERS)
POLL_INTERVAL = 2.0
OUTPUT_DIR = Path("reports")

def build_prompt(ticker: str) -> str:
    return f"Summarize the latest quarterly revenue growth rate for {ticker}, citing the specific page and number."

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
    return html

def process_single_ticker(ticker: str) -> None:
    """Processes a single ticker."""
    client = AlphaSenseClient()
    client.authenticate()

    print(f"\n[{ticker}] Submitting query...")
    prompt = build_prompt(ticker)

    conv_id = client.start_search(prompt)
    print(f"[{ticker}] Conversation ID: {conv_id}")

    result = None
    while True:
        result = client.poll_conversation(conv_id)
        print(f"[{ticker}] Progress: {result.progress:.0%}")

        if result.progress < 0:
            print(f"[{ticker}] Unexpected progress value, skipping.")
            break

        if result.progress >= 1.0:
            break

        time.sleep(POLL_INTERVAL)

    if result and result.markdown:
        out_path = OUTPUT_DIR / f"{ticker}.md"
        # transform citations
        rendered_content = render_citations_html(result.markdown)

        out_path.write_text(rendered_content, encoding="utf-8")
        print(f"[{ticker}] Saved → {out_path}")
    else:
        error_code = getattr(result, "error", {}).get("code", "UNKNOWN") if result else "NO_RESPONSE"
        if error_code == "NO_DOCS":
            print(
                f"[{ticker}] Warning: Query completed successfully, but no indexed filings matched this entity. Skipping.")
        else:
            print(f"[{ticker}] Warning: No content returned (API Error Code: {error_code}). Skipping.")

def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Use ThreadPoolExecutor to run multiple tickers concurrently to avoid bottleneck from single thread loop
    # max_workers=5 allows all 5 tickers to run simultaneously in the worker thread pool
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(process_single_ticker, ticker) for ticker in TICKERS]

        # Wait for all threads to complete
        for future in as_completed(futures):
            future.result()  # Will raise any unexpected exceptions if a thread crashed

if __name__ == "__main__":
    main()