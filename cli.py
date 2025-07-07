# cli.py

from typer import Typer, Option
from papers.fetcher import search_pubmed_ids, fetch_pubmed_details
import pandas as pd

app = Typer()

@app.command()
def fetch(
    query: str = Option(..., "--query", "-q", help="PubMed search query"),
    file: str = Option(None, "--file", "-f", help="CSV output file"),
    debug: bool = Option(False, "--debug", "-d", help="Enable debug output")
):
    if debug:
        print(f"Querying PubMed for: {query}")

    ids = search_pubmed_ids(query)
    if debug:
        print(f"Found PubMed IDs: {ids}")

    papers = fetch_pubmed_details(ids)

    if debug:
        print(f"Filtered Papers: {papers}")

    if not papers:
        print("No non-academic authors found in any of the retrieved papers.")
        return

    df = pd.DataFrame(papers)
    if file:
        df.to_csv(file, index=False)
        print(f"Saved to {file}")
    else:
        print(df.to_string(index=False))

if __name__ == "__main__":
    app()
