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
    
    def preprocess_ticket(
        self,
        title: str,
        description: str,
        analysis_findings: str = None,
        additional_info: str = None
    ) -> str:
        """
        Preprocess ticket for similarity search using standardized format.
        Returns a concise, structured summary suitable for embeddings.
        """
        prompt = f"""Create a standardized summary for similarity matching.

Follow these steps:
1. Identify the core technical problem
2. Extract any specific error messages or identifiers in quotes
3. Include location or timing ONLY if they are part of the pattern
4. Create a 2-3 sentence summary that captures:
- What is happening (main technical issue)
- When relevant: where/when it occurs (pattern)
- When relevant: specific identifiers or error messages

Guidelines:
- Focus on patterns rather than specific instances
- Include coordinates or locations only if they help identify similar issues
- Keep technical details only if they help match similar problems
- Avoid words like 'bug', 'issue', 'problem'
- Ensure summary is under 100 words
- Use consistent terminology for similar concepts

Example Good Summaries:
- "Login authentication fails with 'Invalid Token' message after password reset"
- "Voice navigation provides incorrect exit number at roundabouts in Korea region"
- "Route calculation repeatedly loses charging plan during long-distance planning"

Ticket Information:
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