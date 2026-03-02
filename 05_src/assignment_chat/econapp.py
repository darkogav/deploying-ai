# app.py

import os, csv, requests, json, chromadb
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
from openai import OpenAI
from prompts import HELPME, GUARDRAILS

# add secrets from the pwd of dsi top level 
load_dotenv("../../05_src/.secrets")

API_GATEWAY_KEY = os.getenv("API_GATEWAY_KEY")
if not API_GATEWAY_KEY:
    raise ValueError("API_GATEWAY_KEY not found. Check your ../../05_src/.secrets file.")

# load openai 
openai_client = OpenAI(
    base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    api_key="any value",  # required by SDK; ignored by your gateway
    default_headers={"x-api-key": API_GATEWAY_KEY},
)


# chromadb here
DB_PATH = "./chroma_db"
COLLECTION_NAME = "research_fields"
CSV_PATH = "./data.csv"

# defind the csv cols used for data
RESEARCH_COLS = [
    "research_field1",
    "research_field2",
    "research_field3",
    "research_field4",
    "research_field5",
    "research_field6",
]

# make docs from rows
def row_to_document(r):
    parts = []
    for c in RESEARCH_COLS:
        v = r.get(c)
        if v is not None and str(v).strip():
            parts.append(str(v).strip())
    return " | ".join(parts)

# create a chroma db collection and presist
def init_or_load_collection():
  
    client = chromadb.PersistentClient(path=DB_PATH)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"description": "People and research fields"},
    )

    # If collection is empty, import CSV
    if collection.count() == 0:
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

        ids = []
        documents = []
        metadatas = []
        with open(CSV_PATH, newline="") as f:
            reader = csv.DictReader(f)
            if "name" not in reader.fieldnames:
                raise ValueError('CSV must include a "name" column')
            for i, row in enumerate(reader):
                doc = row_to_document(row)
                if len(doc) > 0:
                    ids.append(f"id_{i}")
                    documents.append(doc)
                    metadatas.append({"name": row["name"]})

        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    return collection

# establish a semantic search functionality to allow searching for 
# faculty who specialize in specific research fields
def semantic_search(collection, query, k=8):
    res = collection.query(query_texts=[query], n_results=k)

    hits = []
    for i in range(len(res["ids"][0])):
        hits.append({
            "name": res["metadatas"][0][i].get("name", "Unknown"),
            "research_fields": res["documents"][0][i],
            "distance": float(res["distances"][0][i]),
        })
    return hits

# make a block for content.
def format_hits_as_context(hits, limit=10):
    lines = []
    for h in hits[:limit]:
        lines.append(f"- {h['name']}: {h['research_fields']}")
    return "\n".join(lines)


# connect to free openalex api to get citations
def openalex_citations(name):
    url = "https://api.openalex.org/authors"
    params = {"search": name, "per-page": 5}

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    results = data.get("results", [])
    if not results:
        return f"I can't find an entry in OpenAlex for '{name}'."

    top = results[0]
    display_name = top.get("display_name", name)
    
    works_count = top.get("works_count")
    
    cited_by = top.get("cited_by_count")
    
    author_id = top.get("id", "")
    if isinstance(author_id, str) and "/" in author_id:
        author_id = author_id.rsplit("/", 1)[-1]

    # get citations for user search 
    parts = [f"Citations found for: {display_name}."]

    # get total citations found.
    if works_count is not None:
        parts.append(f"Works indexed: {works_count}.")

    # get total times cited? (is this useful?)
    if cited_by is not None:
        parts.append(f"Citations count: {cited_by}.")

    # not not aithor add space
    if not author_id:
        return " ".join(parts)

    # formating citations 
    works_url = "https://api.openalex.org/works"
    works_params = {"filter": f"author.id:{author_id}", "per-page": 10}
    wr = requests.get(works_url, params=works_params, timeout=20)
    wr.raise_for_status()
    works_data = wr.json()
    work_list = works_data.get("results", [])

    # return results from openalex json to display
    if work_list:
        parts.append("\n\nPapers (title, year, co-authors):")
        for w in work_list:
            title = w.get("title") or w.get("display_name") or "(no title)"
            year = w.get("publication_year") or "n.d."
            authorships = w.get("authorships") or []
            co_authors = [a.get("author", {}).get("display_name", "") for a in authorships if a.get("author")]
            co_authors = [c for c in co_authors if c]
            co_str = ", ".join(co_authors) if co_authors else "—"
            parts.append(f"\n• {title} ({year}). Co-authors: {co_str}")

    return " ".join(parts)



# use openai on results specific to hits
def answer_with_openai(user_question, hits):
    if not hits:
        return "I can't answer that. Please ask again using the correct format."

    context = format_hits_as_context(hits, limit=10)

# add guard raise and limit answers to only the data in the csv file. 
    resp = openai_client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": GUARDRAILS},
            {"role": "user", "content": f"Question: {user_question}\n\nDataset Context:\n{context}"},
        ],
    )
    return resp.output_text



# the ai chat handler.
def chat_handler(collection, user_message, history, state):
    msg = (user_message or "").strip()
    state = state or {}

    if not msg:
        return "Ask me something 🙂\n\n" + HELPME, state

    if msg.lower().strip().startswith("citations"):
        rest = msg.strip()[9:].lstrip()
        if rest.lower().startswith("for"):
            name = rest[3:].strip()
        elif len(rest) > 0 and rest[0] == ":":
            name = rest[1:].strip()
        else:
            name = rest.strip()
        if name:
            try:
                return openalex_citations(name), state
            except Exception as e:
                return f"OpenAlex citation error: {e}", state

    if msg.lower().strip().startswith("search"):
        idx = msg.find(":")
        if idx != -1:
            q = msg[idx + 1:].strip()
            if q:
                hits = semantic_search(collection, q, k=10)
                try:
                    return answer_with_openai(q, hits), state
                except Exception as e:
                    return "There was an error. My matches are:\n\n" + format_hits_as_context(hits, 10), state

    if msg.lower().strip().startswith("how many faculty"):
        field = msg[15:].strip()
        if field.lower().startswith("in "):
            field = field[3:].strip()
        if field:
            hits = semantic_search(collection, field, k=25)
            try:
                return answer_with_openai(msg, hits), state
            except Exception as e:
                return f"Dump error: {e}", state

    hits = semantic_search(collection, msg, k=8)
    try:
        return answer_with_openai(msg, hits), state
    except Exception as e:
        return "Dump error. Matched:\n\n" + format_hits_as_context(hits, 8), state