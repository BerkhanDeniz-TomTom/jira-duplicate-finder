import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from jira_duplicate_finder.duplicate_finder import JiraDuplicateFinder

def main():
    load_dotenv()
    
    # Initialize finder with Azure OpenAI
    finder = JiraDuplicateFinder(
        jira_server=os.getenv('JIRA_SERVER'),
        jira_email=os.getenv('JIRA_EMAIL'),
        jira_api_token=os.getenv('JIRA_PAT_TOKEN')
    )
    
    # Example JQL filter
    jql_filter = 'project in ("Audi HCP3", Navigation) AND issuetype = Bug AND Customer in (Audi_HCP3, Audi_OCI) AND ("External Reference" is not EMPTY OR "Customer ID" is not EMPTY) AND created > startOfMonth(-6)'
    
    print(f"Fetching bugs with filter: {jql_filter}")
    bugs_df = finder.fetch_bugs(jql_filter)
    print(f"Found {len(bugs_df)} bugs")
    
    print("Building vector store...")
    finder.build_vector_store(bugs_df)
    
    print("Saving database...")
    finder.save_database("./bug_database")
    print("Database saved successfully!")

if __name__ == "__main__":
    main()