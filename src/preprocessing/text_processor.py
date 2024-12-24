from openai import AzureOpenAI
from typing import Optional
import os
from dotenv import load_dotenv

class TextProcessor:
    def __init__(
        self,
        client: Optional[AzureOpenAI] = None,
        model: Optional[str] = None
    ):
        load_dotenv()

        self.client = client or AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-10-21",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.model = model or 'dep-gpt-4o'
    
    def preprocess_ticket(self, title: str, description: str, analysis_findings: str = None, additional_info: str = None) -> str:
        """Preprocess ticket using GPT."""
        prompt = f"""Extract and summarize the core technical problem from this ticket.
Provide a concise summary that:
- Focuses on the actual problem, not auxiliary information
- Prioritizes information from Analysis Findings if available
- Includes specific locations or coordinates in quotes if mentioned
- Includes specific timing in quotes if relevant
- Avoids using words like 'bug' or 'issue' or 'summary'
- Excludes technical details unless they're part of the core problem

Title: {title}"""

        if analysis_findings:
            prompt += f"\nAnalysis Findings: {analysis_findings}"
            
        if additional_info:
            prompt += f"\nAdditional Information: {additional_info}"
            
        prompt += f"\nDescription: {description}"

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return completion.choices[0].message.content