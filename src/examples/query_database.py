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
    
    finder = JiraDuplicateFinder(
        jira_server=os.getenv('JIRA_SERVER'),
        jira_email=os.getenv('JIRA_EMAIL'),
        jira_api_token=os.getenv('JIRA_PAT_TOKEN')
    )
    
    print("Loading database...")
    finder.load_database("./bug_database")
    print(f"Loaded {len(finder.bugs_data)} bugs")
    
    while True:
        print("\nEnter bug description (or 'quit' to exit):")
        query = input("> ")
        
        if query.lower() == 'quit':
            break
            
        print("\nSearching for similar bugs...")
        duplicates = finder.find_duplicates(
            query,
            num_similar=5,
            similarity_threshold=0.5
        )
        
        if not duplicates:
            print("No similar bugs found.")
            continue
            
        print(f"\nFound {len(duplicates)} potential duplicates:")
        for dup in duplicates:
            print(f"\nBug {dup['key']} (Similarity: {dup['similarity_score']})")
            print(f"Summary: {dup['summary']}")
            print(f"Status: {dup['status']}")
            print(f"Created: {dup['created']}")

if __name__ == "__main__":
    main()