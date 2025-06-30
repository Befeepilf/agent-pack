from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core import exceptions
import os
import google.auth
import json
import time

# Get the actual authenticated project ID
#try:
#    credentials, authenticated_project = google.auth.default()
#    project_id = authenticated_project
#    print(f"Using authenticated project: {project_id}")
#except Exception as e:
#    print(f"Authentication failed, using fallback: {e}")


project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "yeply-testing")
location = os.environ.get("ENGINE_LOCATION", "eu")
engine_id = os.environ.get("GOOGLE_VERTEX_ENGINE_ID", "yeply-master-search-intern_1747655638365")

def format_search_result_for_llm(struct_data):
    """Format a search result for LLM consumption as markdown."""
    formatted_parts = []
    try:
        data_text = convert_structured_data_to_text(struct_data)
        formatted_parts.append(f"**Data:**\n{data_text}")
    except:
        formatted_parts.append(f"**Data:** {str(struct_data)}")
    
    return "\n\n".join(formatted_parts)

def convert_structured_data_to_text(struct_data):
    """Convert structured data dictionary to readable text."""
    if not struct_data:
        return ""
    
    try:
        # Extract content directly if available
        content = struct_data.get("content", "")
        if content:
            # Limit content length to avoid processing large texts
            if len(content) > 1000:
                content = content[:1000] + "..."
            return f"**Content:**\n{content}"
        else:
            # Fallback to JSON for other data structures
            json_str = json.dumps(struct_data, ensure_ascii=False, default=str)
            if len(json_str) > 500:
                json_str = json_str[:500] + "..."
            return f"**Data:**\n{json_str}"
    except Exception:
        # Ultimate fallback
        return f"**Data:** {str(struct_data)[:300]}..."

def search_engine(
    search_query: str,
) -> str:
    """
    Search the engine and return formatted results as a markdown string for LLM consumption.
    
    Returns:
        str: Formatted search results as markdown text
    """
    
    try:
        # Create client with optimized settings
        client_options = ClientOptions(
            api_endpoint=f"{location}-discoveryengine.googleapis.com"
        ) if location != "global" else None
        
        client = discoveryengine.SearchServiceClient(client_options=client_options)

        # The full resource name of the search app serving config
        serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

        # Create a request with performance optimizations
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=search_query,
            page_size=5,  # 5 results for faster response
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True,
                    max_snippet_count=1  # Limit snippets to 1 per result
                )
            )
        )

        # Execute search with timeout handling
        page_result = client.search(request)
        
        # Process results with strict limits
        results = []
        result_count = 0
        max_results = 5  # Hard limit on results
        
        for response in page_result:
            if result_count >= max_results:
                break
                
            if response.document.struct_data:
                formatted_result = format_search_result_for_llm(response.document.struct_data)
                if formatted_result:
                    results.append(formatted_result)
                    result_count += 1
        
        # Build output efficiently
        if results:
            output = "# Search Results\n\n"
            for i, result in enumerate(results, 1):
                output += f"## Result {i}\n{result}\n\n---\n\n"
        else:
            output = "# Search Results\n\nNo relevant results found."
        
        return output
                
    except exceptions.ResourceExhausted as e:
        return f"# Search Results\n\nRate limit exceeded. Please try again in a moment."
    except Exception as e:
        elapsed_time = time.time() - start_time
        return f"# Search Results\n\nSearch encountered an error: {str(e)[:100]}..."
