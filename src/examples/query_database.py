import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from jira import JIRA


# Add src to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from jira_duplicate_finder.duplicate_finder import JiraDuplicateFinder
from preprocessing.text_processor import TextProcessor

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

    # Check if ticket ID is provided
    if len(sys.argv) < 2:
        print("Usage: python query_database.py <ticket_id> [database_folder]")
        print("Example: python query_database.py NAV-12345 db_20240417_001722")
        print("If database_folder is not provided, latest will be used")
        return
    
    ticket_id = sys.argv[1]

    # Get database path from command line argument or use latest
    if len(sys.argv) > 2:
        db_name = sys.argv[2]
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
        
    # Initialize Jira client
    jira = JIRA(
        server=os.getenv('JIRA_SERVER'),
        basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_PAT_TOKEN'))
    )

    try:
        issue = jira.issue(ticket_id)

        text_processor = TextProcessor()

        processed_query = text_processor.preprocess_ticket(
            title=issue.fields.summary or '',
            description=issue.fields.description or '',
            analysis_findings=getattr(issue.fields, 'customfield_10357', None) or '',
            additional_info=getattr(issue.fields, 'customfield_10356', None) or ''
        )

        finder = JiraDuplicateFinder(
            jira_server=os.getenv('JIRA_SERVER'),
            jira_email=os.getenv('JIRA_EMAIL'),
            jira_api_token=os.getenv('JIRA_PAT_TOKEN')
        )

        print("Loading database...")
        finder.load_database(db_path)
        print(f"Loaded {len(finder.bugs_data)} bugs")

        print("\nSearching for similar bugs...")
        print(f"Input ticket: {ticket_id}")
        print(f"Title: {issue.fields.summary}")
        print(f"Processed summary: {processed_query}")

        duplicates = finder.find_duplicates(
            processed_query,
            num_similar=5,
            similarity_threshold=0.5
        )

        if not duplicates:
            print("\nNo similar bugs found.")
            return
        
        print(f"\nFound {len(duplicates)} potential duplicates:")
        for dup in duplicates:
            print(f"\nBug {dup['key']} (Similarity: {dup['similarity_score']})")
            print(f"Summary: {dup['summary']}")
            print(f"Status: {dup['status']}")
            print(f"Created: {dup['created']}")
            # print(f"Text length: {dup['text_length']} characters")

    except Exception as e:
        print(f"Error processing ticket {ticket_id}: {str(e)}")
        
if __name__ == "__main__":
    main()