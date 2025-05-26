import weaviate
import os

# Connect to the Weaviate instance
# Create the client
url1=os.getenv("WEAVIATE_URL")

print(url1)
print('ssssssssssssssssss')
client = weaviate.Client(
    url=url1,
    startup_period=15
)

# Test the connection
if client.is_ready():
    print("Connected to Weaviate successfully!")
else:
    print("Failed to connect to Weaviate.")


def search(query):
    result = client.query.get("Document", ["content", "source"]) \
        .with_near_text({
            "concepts": [query]
        }) \
        .with_limit(3) \
        .do()

    chunks = result["data"]["Get"]["PDFChunk"]

print(search('что такое Заявка?'))    