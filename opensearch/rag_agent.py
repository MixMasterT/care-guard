import os
from opensearchpy import OpenSearch
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import time
from utils.logging_utils import log_llm_metadata

# --- CONFIGURATION ---
OPENSEARCH_HOST = os.environ.get("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.environ.get("OPENSEARCH_PORT", 9200))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # Set this in your environment

# --- RETRIEVAL ---
def get_pain_diary_entries(patient_id, size=100):
    client = OpenSearch(hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}])
    response = client.search(
        index="pain-diaries",
        body={
            "query": {"term": {"patient_id": patient_id}},
            "sort": [{"date": {"order": "asc"}}],
            "size": size
        }
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]

# --- FORMAT FOR LLM ---
def format_pain_diary_for_llm(entries):
    lines = []
    for entry in entries:
        lines.append(f"Date: {entry['date']}, Pain Level: {entry['pain_level']}, Notes: {entry.get('notes', '')}")
    return "\n".join(lines)

# --- RAG PROMPT ---
def make_rag_prompt(patient_id, entries):
    context = format_pain_diary_for_llm(entries)
    prompt = (
        f"Patient ID: {patient_id}\n"
        f"Pain Diary Entries:\n{context}\n\n"
        "Based on the above pain diary entries, is this patient's pain getting worse over time? "
        "Please explain your reasoning."
    )
    return prompt

# --- LLM CALL ---
def ask_llm(prompt, model="gpt-4"):
    client = OpenAI(api_key=OPENAI_API_KEY)
    messages: list[ChatCompletionMessageParam] = [
        {"role": "user", "content": prompt}
    ]
    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    elapsed = time.time() - start
    answer = response.choices[0].message.content
    # Try to get token usage if available
    prompt_tokens = getattr(response.usage, 'prompt_tokens', 0) if hasattr(response, 'usage') else 0
    completion_tokens = getattr(response.usage, 'completion_tokens', 0) if hasattr(response, 'usage') else 0
    # Log the LLM call
    log_llm_metadata(
        provider="openai",
        model=model,
        messages=messages,
        response=answer,
        elapsed=elapsed,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens
    )
    return answer

# --- MAIN AGENT LOGIC ---
def main(patient_id):
    entries = get_pain_diary_entries(patient_id)
    if not entries:
        print("No pain diary entries found for this patient.")
        return
    prompt = make_rag_prompt(patient_id, entries)
    answer = ask_llm(prompt)
    print("LLM Answer:\n", answer)

if __name__ == "__main__":
    # Example usage
    patient_id = "4403cbc3-78eb-fbe6-e5c5-bee837f31ea9" #Getting worse
    #patient_id = "f420e6d4-55db-974f-05cb-52d06375b65f" #Getting better
    #patient_id = "29244161-9d02-b8b6-20cc-350f53ffe7a1" #Staying the same
    main(patient_id) 