from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core import exceptions
import os
import google.auth
import json

# Get the actual authenticated project ID
try:
    credentials, authenticated_project = google.auth.default()
    project_id = authenticated_project
    print(f"Using authenticated project: {project_id}")
except Exception as e:
    print(f"Authentication failed, using fallback: {e}")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "yeply-testing")

location = os.environ.get("ENGINE_LOCATION", "eu")
engine_id = os.environ.get("GOOGLE_VERTEX_ENGINE_ID", "yeply-master-search-intern_1747655638365")

def check_authentication():
    """Check if authentication is working."""
    try:
        credentials, project = google.auth.default()
        print(f"Authentication successful")
        print(f"Authenticated project: {project}")
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False

def format_search_result_for_llm(struct_data):
    """Format a search result for LLM consumption as markdown."""
    formatted_parts = []
    try:
        data_text = convert_structured_data_to_text(struct_data)
        formatted_parts.append(f"**Data:**\n{data_text}")
    except:
        formatted_parts.append(f"**Data:** {str(struct_data)}")
    
    return "\n\n".join(formatted_parts)

def convert_structured_data_to_text(data_dict):
    """Convert structured data dictionary to readable text."""
    if not data_dict:
        return ""
    
    text_parts = []
    text = ""
    content = data_dict.get("content", "")
    if content:
        text_parts = [*text_parts, f"**Content:**\n{content}"]
        text += content
    else:
        text_parts = [*text_parts, f"**Content:**\n{json.dumps(data_dict)}"]
        text += json.dumps(data_dict)
    
    return text

def search_engine(
    search_query: str,
) -> str:
    """
    Search the engine and return formatted results as a markdown string for LLM consumption.
    
    Returns:
        str: Formatted search results as markdown text
    """
        
    try:
            client_options = ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com") if location != "global" else None
            # Create a client
            client = discoveryengine.SearchServiceClient(client_options=client_options)

            # The full resource name of the search app serving config
            serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"
            
            print(f"Serving Config: {serving_config}")

            # Create a request with snippets enabled for better LLM consumption
            request = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=search_query,
                page_size=10,
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True
                    )
                )
            )

            page_result = client.search(request)
            
            for response in page_result:
                if response.document.struct_data:
                    formatted_result = format_search_result_for_llm(response.document.struct_data)
                    return formatted_result
                else:
                    print("No structured data found")
                
            return "No structured data found"
                
    except Exception as e:
        return f"Unexpected Error: {e}"