from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core import exceptions
import os
import google.auth

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
    
    for key, value in data_dict.items():
        if isinstance(value, dict):
            # Recursively handle nested dictionaries
            nested_text = convert_structured_data_to_text(value)
            text_parts.append(f"{key}:\n{nested_text}")
        elif isinstance(value, list):
            # Handle lists
            if value:
                if isinstance(value[0], dict):
                    # List of dictionaries
                    list_items = []
                    for i, item in enumerate(value):
                        item_text = convert_structured_data_to_text(item)
                        list_items.append(f"  {i+1}. {item_text}")
                    text_parts.append(f"{key}:\n" + "\n".join(list_items))
                else:
                    # Simple list
                    text_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                text_parts.append(f"{key}: (empty list)")
        else:
            # Simple value
            text_parts.append(f"{key}: {value}")
    
    return "\n".join(text_parts)

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

            # Collect all results from all pages
            all_formatted_results = []
            total_results = 0
            
            for response in page_result:
                if response.document.struct_data:
                    formatted_result = format_search_result_for_llm(response.document.struct_data)
                    all_formatted_results.append(formatted_result)
                else:
                    print("No structured data found")
                
            
            if all_formatted_results:
                # Combine all results into a single markdown string
                markdown_output = f"# Search Results for: {search_query}\n\n"
                markdown_output += f"**Total Results Found:** {total_results}\n\n"
                markdown_output += "---\n\n"
                
                for i, formatted_result in enumerate(all_formatted_results):
                    markdown_output += f"## Result {i+1}\n\n{formatted_result}\n\n---\n\n"
                
                print(f"Successfully formatted {total_results} results for LLM")
                return markdown_output
            else:
                return f"# Search Results for: {search_query}\n\nNo results found."
                
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")


if __name__ == "__main__":
    markdown_results = search_engine("i am sick what do i do")
    
    print("\n=== Final Markdown Output for LLM ===")
    print(markdown_results)