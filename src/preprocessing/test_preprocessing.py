from dotenv import load_dotenv
from ..preprocessing.text_processor import TextProcessor
from jira import JIRA
import os

def test_preprocessing():
    """Test preprocessing with a real Jira ticket."""

    load_dotenv()

    jira = JIRA(
        server=os.getenv('JIRA_SERVER'),
        basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_PAT_TOKEN'))
    )

    ticket_id = "HCP3-21607" #"NAV-167394"  


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

if __name__ == "__main__":
    test_preprocessing()