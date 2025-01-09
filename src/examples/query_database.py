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

    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("1. Search by ticket ID:")
        print("   python query_database.py --ticket NAV-12345 [database_folder]")
        print("2. Search by text description:")
        print("   python query_database.py --text \"Displays incorrect route guidance\" [database_folder]")
        print("\nFormat for text description:")
        print("[Action verb] + [Core behavior] + [Regional pattern if systematic]")
        print("\nExamples:")
        print("- \"Calculates routes through blocked roads in Korea region\"")
        print("- \"Announces incorrect exit numbers at roundabouts\"")
        print("- \"Displays wrong lane guidance during navigation\"")
        print("\nNote: If database_folder is not provided, latest will be used")
        return
    
    # Parse search type
    search_type = sys.argv[1]
    if search_type not in ['--ticket', '--text']:
        print("Error: First argument must be either --ticket or --text")
        return

    # Get query
    if len(sys.argv) < 3:
        print("Error: Please provide ticket ID or text description")
        return
    
    query = sys.argv[2]

    # Get database path from command line argument or use latest
    if len(sys.argv) > 3:
        db_name = sys.argv[3]
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

    try:
        finder = JiraDuplicateFinder(
            jira_server=os.getenv('JIRA_SERVER'),
            jira_email=os.getenv('JIRA_EMAIL'),
            jira_api_token=os.getenv('JIRA_PAT_TOKEN')
        )

        print("Loading database...")
        finder.load_database(db_path)
        print(f"Loaded {len(finder.bugs_data)} bugs")

        if search_type == '--ticket':
            # Initialize Jira client
            jira = JIRA(
                server=os.getenv('JIRA_SERVER'),
                basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_PAT_TOKEN'))
            )

            issue = jira.issue(query)

            text_processor = TextProcessor()

            processed_query = text_processor.preprocess_ticket(
                title=issue.fields.summary or '',
                description=issue.fields.description or '',
                analysis_findings=getattr(issue.fields, 'customfield_10357', None) or '',
                additional_info=getattr(issue.fields, 'customfield_10356', None) or ''
            )

            print(f"Input ticket ID: {query}")
            print(f"Title: {issue.fields.summary}")

        else:
            processed_query = query
            print("\nInput text:")

        print(f"Processed summary: {processed_query}")
        print("\nSearching for similar bugs...")

        duplicates = finder.find_duplicates(
            processed_query,
            query_ticket_id=query if search_type == '--ticket' else None, 
            num_similar=5,
            similarity_threshold=0.7
        )

        if not duplicates:
            print("\nNo similar bugs found.")
            return
        
        print(f"\nFound {len(duplicates)} potential duplicates:")
        for dup in duplicates:
            print(f"\nBug {dup['key']} (Similarity: {dup['similarity_score']})")
            print(f"Title: {dup['summary']}")
            print(f"Processed Summary: {dup['processed_text']}")  # 
            print(f"Status: {dup['status']}")
            print(f"Created: {dup['created']}")
            print(f"Text length: {dup['text_length']} characters")

    except Exception as e:
        error_msg = f"Error processing {'ticket' if search_type == '--ticket' else 'text'} {query}: {str(e)}"
        print(error_msg)
        
if __name__ == "__main__":
    main()