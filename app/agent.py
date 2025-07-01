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
from jinja2 import Template
from langchain_google_vertexai import VertexAIEmbeddings

from app.retrievers import get_compressor, get_retriever
from app.tools.search import (
    search_bike_histories,
    search_slack_messages,
    search_technical_docs,
    search_yeplypedia,
)

EMBEDDING_MODEL = "gemini-embedding-001"
LLM_LOCATION = "global"
LOCATION = "europe-west1"
LLM = "gemini-2.5-pro"

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
    max_documents=TOP_K,
)

compressor = get_compressor(
    project_id=project_id,
)

# Load the system instruction from the instructions folder
with open("app/instructions/system.jinja", "r") as f:
    template = Template(f.read())
instruction = template.render()


root_agent = Agent(
    name="root_agent",
    model=LLM,
    instruction=instruction,
    tools=[
        search_technical_docs,
        search_bike_histories,
        search_slack_messages,
        search_yeplypedia,
    ],
)
