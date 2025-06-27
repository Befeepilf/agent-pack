# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="arg-type"
import os

import google
import vertexai
from google.adk.agents import Agent
from langchain_google_vertexai import VertexAIEmbeddings

from app.retrievers import get_compressor, get_retriever
from app.templates import format_docs

EMBEDDING_MODEL = "text-embedding-005"
LLM_LOCATION = "global"
LOCATION = "europe-west1"
LLM = "gemini-2.5-flash"

credentials, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", LLM_LOCATION)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

vertexai.init(project=project_id, location=LOCATION)
embedding = VertexAIEmbeddings(
    project=project_id, location=LOCATION, model_name=EMBEDDING_MODEL
)


EMBEDDING_COLUMN = "embedding"
TOP_K = 5

data_store_region = os.getenv("DATA_STORE_REGION", "eu")
data_store_id = os.getenv("DATA_STORE_ID", "agent-123-datastore")

retriever = get_retriever(
    project_id=project_id,
    data_store_id=data_store_id,
    data_store_region=data_store_region,
    embedding=embedding,
    embedding_column=EMBEDDING_COLUMN,
    max_documents=10,
)

compressor = get_compressor(
    project_id=project_id,
)

def search_data_tool(query: str) -> str:
    """
    Useful for retrieving relevant documents based on a query.
    Use this when you need additional information to answer a question.

    Args:
        query (str): The user's question or search query.
    
    Returns:
        str: Formatted string containing relevant document content retrieved and ranked based on the query.
    """
    try:
        # Use the retriever to fetch relevant documents based on the query
        retrieved = search_engine(query)
        # Format retrieved documents into a consistent structure for LLM consumption
        #formatted_docs = format_docs.format(docs=retrieved_docs)
        return retrieved
    except Exception as e:
        return f"Calling retrieval tool with query:\n\n{query}\n\nraised the following error:\n\n{type(e)}: {e}"
    

# Load the system instruction from the instructions folder  
env = Environment(loader=FileSystemLoader("app/instructions"))
template = env.get_template("system.jinja")
instruction = template.render()

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    instruction=instruction,
    tools=[retrieve_docs],
)
