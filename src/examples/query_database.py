import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from jira_duplicate_finder.duplicate_finder import JiraDuplicateFinder

def get_latest_database(base_dir: str = "./bug_database") -> str:
    """Get the most recent database directory."""
    if not os.path.exists(base_dir):
        raise ValueError("No database directory found")
        
    databases = [d for d in os.listdir(base_dir) if d.startswith('db_')]
    if not databases:
        raise ValueError("No databases found")
        
    return os.path.join(base_dir, sorted(databases, reverse=True)[0])

def main():
    load_dotenv()

    # Get database path from command line argument or use latest
    if len(sys.argv) > 1:
        db_name = sys.argv[1]
        db_path = os.path.join("./bug_database", db_name)
        if not os.path.exists(db_path):
            print(f"Error: Database '{db_path}' not found")
            return
    else:
        try:
            db_path = get_latest_database()
            print(f"\nUsing latest database: {db_path}")
        except ValueError as e:
            print(f"Error: {e}")
            return
    
    finder = JiraDuplicateFinder(
        jira_server=os.getenv('JIRA_SERVER'),
        jira_email=os.getenv('JIRA_EMAIL'),
        jira_api_token=os.getenv('JIRA_PAT_TOKEN')
    )
    
    print("Loading database...")
    finder.load_database(db_path)
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
            # print(f"Text length: {dup['text_length']} characters")

if __name__ == "__main__":
    main()