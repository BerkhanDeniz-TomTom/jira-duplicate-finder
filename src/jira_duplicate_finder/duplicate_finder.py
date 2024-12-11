from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from jira import JIRA
import pandas as pd
import os
from dotenv import load_dotenv
import pickle
from typing import List, Dict, Optional, Union, Any
from datetime import datetime

class JiraDuplicateFinder:
    """A class to find duplicate Jira bugs using semantic similarity with Azure OpenAI."""
    
    def __init__(
        self,
        jira_server: str,
        jira_email: str,
        jira_api_token: str,
        azure_deployment: str = "dep-embed-ada",
        azure_api_version: str = "2024-10-21",
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
        model: str = "text-embedding-ada-002"
    ):
        """
        Initialize the JiraDuplicateFinder with Azure OpenAI.
        
        Args:
            jira_server: URL of the Jira server
            jira_email: Jira account email
            jira_api_token: Jira API token
            azure_deployment: Azure OpenAI deployment name
            azure_api_version: Azure OpenAI API version
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            model: Azure OpenAI model name
        """
        # Initialize Azure OpenAI embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            model=model,
            azure_deployment=azure_deployment,
            openai_api_version=azure_api_version,
            chunk_size=chunk_size
        )

        self.chunk_size = chunk_size 
        
        # Initialize text splitter for long descriptions
        self.text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        
        # Initialize Jira client
        self.jira = JIRA(
            server=jira_server,
            basic_auth=(jira_email, jira_api_token)
        )
        
        self.vector_store = None
        self.bugs_data = None
        self.last_update = None

    def get_all_issues(self, jql_filter, max_results=5000):
        start_at = 0
        all_issues = []
        
        while True:
            # Get issues in chunks
            chunk = self.jira.search_issues(
                jql_filter,
                maxResults=100,  # Process in smaller chunks
                startAt=start_at,
                fields='summary,description,created,updated,status,labels,priority'
            )
            
            if not chunk:
                break
                
            all_issues.extend(chunk)
            
            # If we've received fewer issues than requested, we're done
            if len(chunk) < 100 or len(all_issues) >= max_results:
                break
                
            start_at += len(chunk)
        
        return all_issues[:max_results]  # Ensure we don't exceed max_results

    def fetch_bugs(
        self,
        jql_filter: str,
        max_results: int = 5000
    ) -> pd.DataFrame:
        """
        Fetch bugs from Jira using a JQL filter.
        
        Args:
            jql_filter: JQL query to filter issues
            max_results: Maximum number of bugs to fetch
            
        Returns:
            DataFrame containing bug information
        """
        issues = self.get_all_issues(jql_filter, max_results)
        
        bugs_data = []
        for issue in issues:
            combined_text = f"Title: {issue.fields.summary}\n\n"
            if issue.fields.description:
                combined_text += f"Description: {issue.fields.description}"
                
            bugs_data.append({
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': issue.fields.description or '',
                'created': issue.fields.created,
                'updated': issue.fields.updated,
                'status': str(issue.fields.status),
                'priority': str(issue.fields.priority),
                'labels': [str(label) for label in issue.fields.labels],
                'text': combined_text
            })
            
        self.bugs_data = pd.DataFrame(bugs_data)
        self.last_update = datetime.now()
        return self.bugs_data
    
    def build_vector_store(
        self,
        bugs_df: Optional[pd.DataFrame] = None,
        force_rebuild: bool = False
    ) -> None:
        """
        Create vector store from bug descriptions.
        """
        if bugs_df is not None:
            self.bugs_data = bugs_df
            
        if self.bugs_data is None:
            raise ValueError("No bug data provided. Either call fetch_bugs first or provide bugs_df")
        
        if self.vector_store is not None and not force_rebuild:
            return
            
        texts = self.bugs_data['text'].tolist()
        metadata = self.bugs_data.to_dict('records')
        
        # Split long texts if needed
        if any(len(text) > self.chunk_size for text in texts):
            processed_texts = []
            processed_metadata = []
            for text, meta in zip(texts, metadata):
                splits = self.text_splitter.split_text(text)
                processed_texts.extend(splits)
                processed_metadata.extend([meta] * len(splits))
            texts = processed_texts
            metadata = processed_metadata
        
        self.vector_store = FAISS.from_texts(
            texts,
            self.embeddings,
            metadatas=metadata
        )

    def save_database(
        self,
        directory: str = "./bug_database"
    ) -> None:
        """
        Save the vector store and bug data to disk.
        """
        if self.vector_store is None or self.bugs_data is None:
            raise ValueError("No database to save. Build vector store first")
        
        if len(self.bugs_data) == 0:
            raise ValueError("No bug data to save")
            
        os.makedirs(directory, exist_ok=True)
        
        # Save vector store
        self.vector_store.save_local(directory)

        print(f"Current working directory: {os.getcwd()}")
        print(f"Saving database to: {os.path.abspath(directory)}")
        
        # Save bugs data and metadata
        metadata = {
            'bugs_data': self.bugs_data,
            'last_update': self.last_update
        }
        with open(os.path.join(directory, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

    def load_database(
        self,
        directory: str = "./bug_database"
    ) -> None:
        """
        Load the vector store and bug data from disk.
        """
        if not os.path.exists(directory):
            raise ValueError(f"Database directory {directory} does not exist")
            
        # Load vector store
        self.vector_store = FAISS.load_local(directory, self.embeddings, allow_dangerous_deserialization=True)
        
        # Load bugs data and metadata
        with open(os.path.join(directory, 'metadata.pkl'), 'rb') as f:
            metadata = pickle.load(f)
            self.bugs_data = metadata['bugs_data']
            self.last_update = metadata.get('last_update')

    def find_duplicates(
        self,
        query_text: str,
        num_similar: int = 5,
        similarity_threshold: float = 0.85,
        status_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find potentially duplicate bugs based on semantic similarity.
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Call build_vector_store first")
            
        search_kwargs = {}
        if status_filter:
            search_kwargs['filter'] = {'status': {'$in': status_filter}}
            
        similar_bugs = self.vector_store.similarity_search_with_score(
            query_text,
            k=num_similar,
            **search_kwargs
        )
        
        potential_duplicates = []
        for doc, score in similar_bugs:
            similarity = 1 - score
            if similarity >= similarity_threshold:
                duplicate_info = {
                    'key': doc.metadata['key'],
                    'summary': doc.metadata['summary'],
                    'status': doc.metadata['status'],
                    'priority': doc.metadata['priority'],
                    'created': doc.metadata['created'],
                    'updated': doc.metadata['updated'],
                    'labels': doc.metadata['labels'],
                    'similarity_score': f"{similarity:.2%}"
                }
                potential_duplicates.append(duplicate_info)
                
        return potential_duplicates