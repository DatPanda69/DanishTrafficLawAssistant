import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI

#Load GPT-4 API
client = OpenAI(api_key="private API key, removed because it's private :) ")

#Load the multilingual embedding model
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")

#Load traffic laws dataset
with open("danish_traffic_laws_2024.json", "r", encoding="utf-8") as f:
    laws_data = json.load(f)["Færdselsloven_2024"]  # Extracting list of laws

#Extract all relevant text from law document(s)
law_texts = []
law_references = []

def extract_texts(law_entry):
    texts = [law_entry["text"]]
    references = [(law_entry["paragraph"], law_entry["chapter"])]

    # Include subsections
    for subsection in law_entry.get("subsections", []):
        texts.append(subsection["text"])
        references.append((law_entry["paragraph"], law_entry["chapter"]))

    # Include conditions
    for condition in law_entry.get("conditions", []):
        texts.append(condition["text"])
        references.append((law_entry["paragraph"], law_entry["chapter"]))
        for sub in condition.get("subsections", []):
            texts.append(sub["text"])
            references.append((law_entry["paragraph"], law_entry["chapter"]))

    # Include definitions
    for definition in law_entry.get("definitions", []):
        texts.append(f"{definition['term']} {definition['description']}")
        references.append((law_entry["paragraph"], law_entry["chapter"]))

    return texts, references

# Process all law(s)
for law in laws_data:
    texts, references = extract_texts(law)
    law_texts.extend(texts)
    law_references.extend(references)

#Encode all extracted text
law_embeddings = embedding_model.encode(law_texts, convert_to_numpy=True)

#Creating FAISS index for faster searching
index = faiss.IndexFlatL2(law_embeddings.shape[1])
index.add(law_embeddings)


#Function to find most relevant traffic laws
def find_relevant_laws(query, top_k=5):
    query_embedding = embedding_model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(law_texts):  # Checking if index is valid
            paragraph, chapter = law_references[idx]
            results.append(
                {
                    "chapter": chapter,
                    "paragraph": paragraph,
                    "text": law_texts[idx],
                    "score": round(1 - distances[0][i], 2),  # Convert distance to relevance
                }
            )
    return results


# Function to make the ai more human friendly
def ask_gpt4(query, legal_results):
    context = "\n\n".join([f"{res['paragraph']} ({res['chapter']}): {res['text']}" for res in legal_results])

    prompt = f"""
    Du er en dansk færdselsekspert, der besvarer spørgsmål i et letforståeligt og juridisk korrekt sprog.

    🔹 **Spørgsmål:** "{query}"
    
    🔹 **Relevant lovgivning:**  
    {context}

    🔹 **Svar:**  
    - Forklar reglerne klart og præcist, uden overflødig juridisk jargon.  
    - Brug naturlig dansk grammatik og skriv som en menneskelig ekspert ville svare.  
    - Giv en **opdeling** af straffen (fx bøde, fængsel, kørekortfrakendelse) afhængigt af alvorligheden.  
    - **Nævn relevante paragraffer**, men undgå at citere dem direkte – opsummer i stedet hovedreglerne.  
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


# Function to handle user input
def search_traffic_law():
    while True:
        query = input("\nStil dit spørgsmål (eller skriv 'afslut' for at afslutte): ").strip()
        if query.lower() == "afslut":
            print("Tak for i dag!")
            break

        relevant_laws = find_relevant_laws(query, top_k=5)

        if not relevant_laws:
            print("Ingen relevante love blev fundet. Prøv at omformulere dit sprøgsmål.")
            continue

        # using GPT-4 for human explanation
        ai_answer = ask_gpt4(query, relevant_laws)

        # Print response and debug of laws
        print("\n🔎 **AI Svar:**")
        print(f"✅ {ai_answer}\n")

        print("📜 **Relevante Love:**")
        for res in relevant_laws:
            print(f"📌 {res['paragraph']} ({res['chapter']}) *(Relevans: {res['score']})*\n   {res['text']}\n")


# Run the assistant
if __name__ == "__main__":
    print("Velkommen til din danske færdselslov assistent")
    search_traffic_law()
