# Jira Duplicate Bug Finder

A tool to identify potential duplicate Jira bugs using semantic similarity with Langchain.

## Setup

1. Create and activate virtual environment:
```
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up environment variables:

Copy `.env.example` to `.env`:
  ```bash
  cp .env.example .env
  ```

Edit `.env` with your credentials:

Get your OpenAI personal access token from https://developer.api.chatgpt.tomtom-global.com/profile and add it to the `.env` file as follows:
```
AZURE_OPENAI_API_KEY="secret"
```

Get your JIRA personal access token from https://id.atlassian.com/manage-profile/security/api-tokens and add it to the `.env` file as follows:
```
JIRA_EMAIL="bob.thebuilder@yeswecan.com"
JIRA_PAT_TOKEN="your JIRA PAT"
```

## Usage

1. Create the initial database:
```
python src/examples/create_database.py
```
This will create a timestamped database folder under `bug_database/`

2. Search for duplicates:

```
# Use latest database
python src/examples/query_database.py HCP3-21607

# Use specific database folder
python src/examples/query_database.py HCP3-21607 db_20240417_001722
```

3. Analyze database similarities:
```
# Use latest database
python src/examples/analyze_database.py

# Use specific database folder
python src/examples/analyze_database.py db_20240417_001722
```