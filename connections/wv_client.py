import os
import weaviate

_wv_client = None


def get_weaviate_client():
    """
    Global singleton Weaviate client (one per Python process)
    Compatible with weaviate-client >= 4.x
    """
    global _wv_client
    if _wv_client is not None:
        return _wv_client
    url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    _wv_client = weaviate.connect_to_local(
        host=url.replace("http://", "").replace("https://", "").split(":")[0],
        port=int(url.split(":")[-1]) if ":" in url else 8080,
        grpc_port=50051,
        headers={
            "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY"),
        },
    )
    return _wv_client

