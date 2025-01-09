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
            # Input validation and cleaning
            if not title or not description:
                raise ValueError("Title and description are required")

            # Clean inputs
            title = title.strip() if title else ""
            description = description.strip() if description else ""
            analysis_findings = analysis_findings.strip() if analysis_findings else ""
            additional_info = additional_info.strip() if additional_info else ""

            system_prompt = """You are a technical expert specializing in standardizing bug descriptions for similarity matching.
    Your task is to create concise, standardized summaries that:
    1. Start with an action verb (displays, shows, calculates, etc.)
    2. Focus on the core technical behavior
    3. Include regional patterns only if systematic
    4. Avoid implementation details, coordinates, or version numbers
    5. Use present tense and clear technical language"""

            user_prompt = f"""Create a standardized summary focusing ONLY on the core technical behavior.

    Format Rules:
    [Action verb] + [Core behavior] + [Regional pattern if systematic]

    Guidelines:
    - Focus ONLY on the repeatable technical behavior
    - DO NOT include:
        * Specific coordinates
        * Software versions
        * Test counts
        * Individual instances
        * Implementation details
    - Use simple present tense
    - Maximum 2 sentences
    - Only include region if the issue is region-specific

    Good Examples:
    - "Calculates routes through blocked roads in Korea region"
    - "Rejects valid city name 'Ingolstadt' while accepting other destinations"
    - "Announces incorrect exit numbers at roundabouts in Japan"
    - "Loses charging plan during long-distance route calculations"

    Bad Examples:
    - "Route calculation fails at coordinates 37.529, 126.884" (too specific)
    - "Issue occurs in version VR41_2_A13E_HCP3" (version not needed)
    - "Problem happens 3/3 times" (test count not needed)
    - "Multiple routing problems in the area" (too vague)

    Ticket Information:
    Title: {title}"""

            if analysis_findings:
                user_prompt += f"\nAnalysis Findings: {analysis_findings}"
                
            if additional_info:
                user_prompt += f"\nAdditional Information: {additional_info}"
                
            user_prompt += f"\nDescription: {description}"

            completion = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return completion.choices[0].message.content