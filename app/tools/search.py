import logging
import os
from dataclasses import dataclass

from google.api_core import exceptions
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.discoveryengine_v1.services.search_service import SearchServiceClient
from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict
from proto.marshal.collections.maps import MapComposite

logger = logging.getLogger(__name__)

# Get the actual authenticated project ID
# try:
#    credentials, authenticated_project = google.auth.default()
#    project_id = authenticated_project
#    print(f"Using authenticated project: {project_id}")
# except Exception as e:
#    print(f"Authentication failed, using fallback: {e}")


project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "yeply-testing")
location = os.environ.get("ENGINE_LOCATION", "eu")
engine_id = os.environ.get(
    "GOOGLE_VERTEX_ENGINE_ID", "yeply-master-search-intern_1747655638365"
)


@dataclass
class DataStore:
    id: str
    name: str


DATA_STORES = [
    DataStore(
        id="technical-docs_1751366705621",
        name="Technical Docs for Bikes",
    ),
    DataStore(
        id="bike-histories_1751381211957",
        name="Work order and Damage report histories of bikes",
    ),
    DataStore(
        id="slack-messages_1747059296012",
        name="Slack messages from internal technical channels",
    ),
    DataStore(
        id="yeplypedia_1751380874456",
        name="Internal Yeplypedia knowledge base (wiki-like)",
    ),
    DataStore(
        id="erp-software-system_1751387305393",
        name="Documentation on how to use our ERP software system",
    ),
]


def search_technical_docs(search_query: str) -> str:
    """
    Searches for technical bike documentation

    Args:
        search_query: Important keywords to search for
    """
    return search_engine(search_query, DATA_STORES[0])


def search_bike_histories(search_query: str) -> str:
    """
    Searches work order and damage report histories of bikes

    Args:
        search_query: Important keywords to search for
    """
    return search_engine(search_query, DATA_STORES[1])


def search_slack_messages(search_query: str) -> str:
    """
    Searches for messages from internal technical channels

    Args:
        search_query: Important keywords to search for
    """
    return search_engine(search_query, DATA_STORES[2])


def search_yeplypedia(search_query: str) -> str:
    """
    Searches for information in the internal Yeplypedia knowledge base.
    It contains various information about company processes, procedures, tutorials, customer-specific information, etc.

    Args:
        search_query: Important keywords to search for
    """
    return search_engine(search_query, DATA_STORES[3])


def search_erp_software_system(search_query: str) -> str:
    """
    Searches for information on how to use our ERP software system, including Ops tool, Vantool, B2B portal (My-Business) and B2C portal (My-Yeply), and general information about the software system.

    Args:
        search_query: Important keywords to search for
    """
    return search_engine(search_query, DATA_STORES[4])


def search_engine(search_query: str, data_store: DataStore) -> str:
    """
    Search the engine and return formatted results as a markdown string for LLM consumption.

    Returns:
        str: Formatted search results as markdown text
    """

    try:
        client_options = (
            ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
            if location != "global"
            else None
        )

        client = SearchServiceClient(client_options=client_options)

        serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=search_query,
            page_size=8,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True,
                    max_snippet_count=1,  # Limit snippets to 1 per result
                )
            ),
            data_store_specs=[
                discoveryengine.SearchRequest.DataStoreSpec(
                    data_store=f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store.id}"
                )
            ],
            params={
                "user_country_code": "nl",
            },
        )

        # Execute search with timeout handling
        page_result = client.search(request)

        results = []
        result_count = 0
        max_results = 5

        for response in page_result:
            if result_count >= max_results:
                break

            if response.document.struct_data:
                formatted_result = format_search_result_for_llm(
                    response.document.struct_data
                )
                if formatted_result:
                    results.append(formatted_result)
                    result_count += 1

        if results:
            output = ""
            for i, result in enumerate(results, 1):
                output += f"## Result {i}\n{result}\n\n---\n\n"
        else:
            output = "No relevant results found."

        return f"# Search Results for '{data_store.name}'\n\n{output}"

    except exceptions.ResourceExhausted:
        return "Rate limit exceeded. Please try again in a moment."
    # except Exception as e:
    #     return f"Search encountered an error: {str(e)[:100]}..."


def format_search_result_for_llm(struct_data: struct_pb2.Struct | MapComposite) -> str:
    data = struct_data_to_dict(struct_data)
    logger.info(f"Formatting search result: {data}")

    # content = data.get("content", "")
    # if content:
    #     return f"**Content:**\n{content}"

    # Don't use json.dumps as the data might contain non-serializable objects like proto.marshal.collections.repeated.RepeatedComposite
    raw_data = str(data)
    return f"**Data:**\n{raw_data}"


def struct_data_to_dict(struct_data: struct_pb2.Struct | MapComposite) -> dict:
    if isinstance(struct_data, MapComposite):
        return dict(struct_data)
    if isinstance(struct_data, struct_pb2.Struct):
        return MessageToDict(struct_data)
    raise ValueError(f"Unsupported type: {type(struct_data)}")
