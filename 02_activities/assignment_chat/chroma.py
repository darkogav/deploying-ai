import os
from dotenv import load_dotenv
# Load env so OPENAI_API_KEY is set
#load_dotenv(os.getcwd() + "/05_src/.secrets")
#load_dotenv(os.getcwd() + "/05_src/.secrets", override=True)
#key = os.environ.get("OPENAI_API_KEY", "")
#print("Key ends with:", key[-4:] if len(key) >= 4 else "?")


import pandas as pd
from chromadb.utils import embedding_functions
import chromadb, os
#from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
#import os
#from openai import OpenAI
#client = OpenAI()

# print(os.getcwd() + "/05_src/.secrets")
# Load env so OPENAI_API_KEY is set
#load_dotenv(os.getcwd() + "/05_src/.secrets")

# Client and embedding function
#client = chromadb.PersistentClient(path="./chroma_db")  # or EphemeralClient() for in-memory
#ef = OpenAIEmbeddingFunction()

client = chromadb.Client()

sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="research_fields",
    embedding_function=sentence_transformer_ef,
    metadata={"description": "People and research fields"}
)

# Build one document per row: only research fields (so query matches only those)
def row_to_document(r):
    parts = [str(r[c]) for c in research_cols if pd.notna(r[c]) and str(r[c]).strip()]
    return " | ".join(parts) if parts else ""

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
df = pd.read_csv('./data.csv')

pd.set_option('display.max_columns', None)

research_cols = ["research_field1", "research_field2", "research_field3", "research_field4", "research_field5", "research_field6"]


df["_doc"] = df.apply(row_to_document, axis=1)
# Drop rows with no research text so we don't embed empty strings
df_emb = df[df["_doc"].str.len() > 0].copy()

ids = [f"id_{i}" for i in df_emb.index]
documents = df_emb["_doc"].tolist()
metadatas = [{"name": row["name"]} for _, row in df_emb.iterrows()]

collection.add(ids=ids, documents=documents, metadatas=metadatas)

print("Loaded", len(documents), "documents into Chroma.")

results = collection.query(
    query_texts=["Theory"],
    n_results=5
)

#print(results)

for i in range(len(results["ids"][0])):
    print("Name:", results["metadatas"][0][i]["name"])
    print("Research Fields:", results["documents"][0][i])
    print("Distance:", results["distances"][0][i])
    print("-" * 40)