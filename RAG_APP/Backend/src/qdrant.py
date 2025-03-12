from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant


from qdrant_client import QdrantClient, models
from decouple import config

qdrant_client = QdrantClient(
    url=config("QDRANT_URL"),
    api_key=config("QDRANT_API_KEY")

)

collection_name = "website_content"


def create_collection(collection_name: str):
        
    existing_collections = [c.name for c in qdrant_client.get_collections().collections]

    if collection_name not in existing_collections:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "size": 1536,  # Dimension of embeddings
                "distance": "Cosine"
            }
        )
        print(f"Collection '{collection_name}' created successfully.")
    else:
        print(f"Collection '{collection_name}' already exists. Skipping creation.")



    
vector_store = Qdrant(
    client=qdrant_client,
    collection_name=collection_name,
    embeddings=OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=config("OPENAI_API_KEY")
    )
)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20, length_function=len)

def upload_website_to_collection(url: str):
    loader = WebBaseLoader(url)
    docs = loader.load_and_split(text_splitter)
    for doc in docs:
        doc.metadata["source"] = url
    vector_store.add_documents(docs)
    return (f"Documents uploaded to collection {collection_name} successfully")


# create_collection(collection_name=collection_name)
# upload_website_to_collection(collection_name=collection_name, url = "https://mark-riedl.medium.com/a-very-gentle-introduction-to-large-language-models-without-the-hype-5f67941fa59e")
