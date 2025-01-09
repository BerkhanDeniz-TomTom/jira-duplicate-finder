from dotenv import load_dotenv
from ..preprocessing.text_processor import TextProcessor
from jira import JIRA
import os
import sys

def test_preprocessing():
    """
   Test preprocessing with a real Jira ticket.
   Usage: python -m src.preprocessing.test_preprocessing <ticket_id>
   Example: python -m src.preprocessing.test_preprocessing NAV-167394
   """

    if len(sys.argv) < 2:
       print("Please provide a ticket ID")
       print("Usage: python -m src.preprocessing.test_preprocessing <ticket_id>")
       print("Example: python -m src.preprocessing.test_preprocessing NAV-167394")
       return

    ticket_id = sys.argv[1]
   
    load_dotenv()

    try:
        jira = JIRA(
            server=os.getenv('JIRA_SERVER'),
            basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_PAT_TOKEN'))
        )

        issue = jira.issue(ticket_id)
        
        processor = TextProcessor()
        
        processed_text = processor.preprocess_ticket(
            title=issue.fields.summary,
            description=issue.fields.description,
            analysis_findings=issue.fields.customfield_10357,
            additional_info=issue.fields.customfield_10356
        )
        
        print("\nOriginal Ticket:")
        print(f"Key: {issue.key}")
        print(f"Title: {issue.fields.summary}")
        print(f"Analysis Findings: {issue.fields.customfield_10357}")
        print(f"Additional Information: {issue.fields.customfield_10356}")
        print(f"Description: {issue.fields.description}")
        print("\nProcessed Text:")
        print(processed_text)

    except Exception as e:
       print(f"Error processing ticket {ticket_id}: {str(e)}")

if __name__ == "__main__":
    test_preprocessing()