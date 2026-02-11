import weaviate
import os

def search(query,limit=5):
    client= weaviate.Client(
        url=os.getenv("WEAVIATE_URL"),
    )
    try:
        if client.is_ready():
            result = client.query.get("Document", ["content", "source",'url']) \
                .with_near_text({
                    "concepts": [query]
                }) \
                .with_limit(limit) \
                .do()
        return result    
    except Exception as e:
        print(f"Ошибка: {e}")
