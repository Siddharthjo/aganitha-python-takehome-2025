# papers/fetcher.py

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
import re

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded"
}

def is_non_academic(affiliation: str) -> bool:
    if not affiliation:
        return False
    academic_keywords = ['university', 'college', 'institute', 'school', 'hospital', 'department', 'center', '.edu', '.ac', '.org']
    company_keywords = ['inc', 'ltd', 'llc', 'corp', 'biotech', 'pharma', 'therapeutics', 'laboratories']
    affiliation_lower = affiliation.lower()
    if any(word in affiliation_lower for word in academic_keywords):
        return False
    return any(word in affiliation_lower for word in company_keywords)

def search_pubmed_ids(query: str, max_results=20) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results
    }
    response = requests.get(PUBMED_SEARCH_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json().get("esearchresult", {}).get("idlist", [])

def fetch_pubmed_details(pubmed_ids: List[str]) -> List[Dict]:
    ids_str = ",".join(pubmed_ids)
    params = {
        "db": "pubmed",
        "id": ids_str,
        "retmode": "xml"
    }
    response = requests.get(PUBMED_FETCH_URL, headers=HEADERS, params=params)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        paper_data = {
            "PubmedID": "",
            "Title": "",
            "Publication Date": "",
            "Non-academic Author(s)": [],
            "Company Affiliation(s)": [],
            "Corresponding Author Email": ""
        }

        # ID
        paper_data["PubmedID"] = article.findtext(".//PMID")

        # Title
        paper_data["Title"] = article.findtext(".//ArticleTitle")

        # Publication Date
        pub_date = article.find(".//PubDate")
        if pub_date is not None:
            year = pub_date.findtext("Year") or "N/A"
            month = pub_date.findtext("Month") or ""
            paper_data["Publication Date"] = f"{month} {year}"

        # Authors
        for author in article.findall(".//Author"):
            affil = author.findtext(".//AffiliationInfo/Affiliation")
            lastname = author.findtext("LastName") or ""
            forename = author.findtext("ForeName") or ""
            name = f"{forename} {lastname}".strip()

            if is_non_academic(affil):
                paper_data["Non-academic Author(s)"].append(name)
                paper_data["Company Affiliation(s)"].append(affil)

            email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", affil or "")
            if email_match and not paper_data["Corresponding Author Email"]:
                paper_data["Corresponding Author Email"] = email_match.group()

        if paper_data["Non-academic Author(s)"]:
            papers.append(paper_data)

    return papers
