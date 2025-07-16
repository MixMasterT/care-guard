import os
from dotenv import load_dotenv
load_dotenv()

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


def get_fhir_entries(patient_id, size=100):
    """
    Retrieve all FHIR medical records for a patient from the 'fhir-medical-records' index.
    Returns a list of documents sorted by 'indexed_at' ascending.
    """
    client = OpenSearch(hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}])
    response = client.search(
        index="fhir-medical-records",
        body={
            "query": {"term": {"patient_id": patient_id}},
            "sort": [{"indexed_at": {"order": "asc"}}],
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


def format_fhir_entries_for_llm(entries):
    """
    Format FHIR entries for LLM. For brevity, summarize each entry by resource type, date (if available), and a key detail.
    """
    lines = []
    for entry in entries:
        resource = entry.get('resource_data', {})
        resource_type = entry.get('resource_type', 'Unknown')
        resource_id = entry.get('resource_id', 'unknown')
        # Try to extract a date if present
        date = resource.get('effectiveDateTime') or resource.get('issued') or resource.get('date') or entry.get('indexed_at', '')
        # Try to extract a summary value
        summary = ''
        if resource_type == 'Observation':
            summary = f"Value: {resource.get('valueQuantity', {}).get('value', '')} {resource.get('valueQuantity', {}).get('unit', '')}".strip()
        elif resource_type == 'Condition':
            summary = f"Code: {resource.get('code', {}).get('text', '')}".strip()
        elif resource_type == 'MedicationRequest':
            summary = f"Medication: {resource.get('medicationCodeableConcept', {}).get('text', '')}".strip()
        elif resource_type == 'Patient':
            summary = f"Name: {resource.get('name', [{}])[0].get('text', '')}".strip()
        # Add a generic fallback if nothing else
        if not summary:
            summary = str(resource.get('id', ''))
        lines.append(f"Resource: {resource_type}, Date: {date}, {summary}")
    return "\n".join(lines)

# --- RAG PROMPT ---
def make_rag_prompt(patient_id, pain_entries, fhir_entries):
    pain_context = format_pain_diary_for_llm(pain_entries)
    fhir_context = format_fhir_entries_for_llm(fhir_entries)
    prompt = (
        f"Patient ID: {patient_id}\n"
        f"Medical History (FHIR):\n{fhir_context}\n\n"
        f"Pain Diary Entries:\n{pain_context}\n\n"
        "Based on the patient's medical history and pain diary entries above, how worried are you about this patient? "
        "Explain your reasoning and provide a worry estimate out of 100, where 100 is very worried and 0 is not worried."
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
    pain_entries = get_pain_diary_entries(patient_id)
    fhir_entries = get_fhir_entries(patient_id)

    if not pain_entries and not fhir_entries:
        print("No pain diary or FHIR entries found for this patient.")
        return

    prompt = make_rag_prompt(patient_id, pain_entries, fhir_entries)
    answer = ask_llm(prompt)
    print("LLM Answer:\n", answer)

if __name__ == "__main__":
    # Example usage
    #patient_id = "4403cbc3-78eb-fbe6-e5c5-bee837f31ea9" #Getting worse
    #patient_id = "f420e6d4-55db-974f-05cb-52d06375b65f" #Getting better
    patient_id = "29244161-9d02-b8b6-20cc-350f53ffe7a1" #Staying the same
    main(patient_id) 