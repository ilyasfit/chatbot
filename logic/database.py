from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from langchain.schema import Document

import qdrant_client
from qdrant_client.http.models import SearchRequest
import os
import uuid


knowledge_collection = os.getenv("KNOWLEDGE_COLLECTION_NAME")
img_collection = os.getenv("IMAGE_COLLECTION_NAME")

embeddings = OpenAIEmbeddings()

client = qdrant_client.QdrantClient(
    os.getenv("QDRANT_HOST"),
    port=6333,
    api_key=os.getenv("QDRANT_API_KEY")
)


def get_documents(collection_name):
    # Erstellen Sie einen Dummy-Vector mit der gleichen Dimension wie Ihre Embeddings
    dummy_vector = [0] * 1536

    get_collection(collection_name=collection_name)

    # Führen Sie eine Suchanfrage mit dem Dummy-Vector durch
    response = client.search(
        collection_name=collection_name,
        query_vector=dummy_vector,
        limit=50,  # Anzahl der abzurufenden Dokumente, passen Sie dies nach Bedarf an
        with_payload=True  # Stellen Sie sicher, dass die Payload-Daten zurückgegeben werden
    )

    # Extrahieren Sie die Dokumente direkt aus der Antwort
    documents = []
    for hit in response:
        doc = hit.payload
        doc['id'] = hit.id  # Fügen Sie die ID zum Dokument hinzu
        documents.append(doc) 

    try:
        return documents
    except Exception as e:
        print(f"ERROR: {e}")
        return ""


def search_documents(collection_name, query, limit=5):
    """
    Führt eine Ähnlichkeitssuche in der angegebenen Collection durch.
    
    :param collection_name: Name der Qdrant-Collection.
    :param query: Suchanfrage als Text.
    :param limit: Maximale Anzahl der zurückzugebenden Dokumente.
    :return: Liste der gefundenen Dokumente.
    """
    # Konvertiere die Suchanfrage in einen Vektor
    query_vector = embeddings.embed_query(query)

    # Führe die Similarity Search durch
    response = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        with_payload=True  # Stellen Sie sicher, dass die Payload-Daten zurückgegeben werden
    )

    # Extrahiere die Dokumente aus der Antwort
    documents = []
    for hit in response:
        doc = hit.payload
        doc['id'] = hit.id  # Füge die ID zum Dokument hinzu
        documents.append(doc)

    return documents


def update_document(collection_name, document_id, new_content):
    """
    Aktualisiert ein Dokument im Vectorstore.

    :param collection_name: Name der Qdrant-Collection.
    :param document_id: Die ID des zu aktualisierenden Dokuments.
    :param new_content: Der neue Inhalt des Dokuments.
    """
    # Konvertiere den neuen Inhalt in einen Vektor
    new_vector = embeddings.embed_query(new_content)

    # Aktualisiere das Dokument im Vectorstore
    client.upsert(
        collection_name=collection_name,
        points=[{
            "id": document_id,
            "vector": new_vector,
            "payload": {"page_content": new_content}
        }]
    )


def update_image_document(collection_name, document_id, new_keywords, new_img_link):
    # Konvertiere die neuen Keywords in einen Vektor
    new_vector = embeddings.embed_query(new_keywords)

    # Aktualisiere das Dokument im Vectorstore
    client.upsert(
        collection_name=collection_name,
        points=[{
            "id": document_id,
            "vector": new_vector,
            "payload": {"page_content": new_keywords, "metadata": {"img_link": new_img_link}}
        }]
    )


def save_image(img_link, keywords):
    print("Save Image to Vectorstore")
    print("IMG COLLECTION NAME: ", img_collection)
    existing_collections = client.get_collections()
    print("Existing Collections: ", existing_collections)

    # Create vectorstore
    vectorstore = Qdrant(
        client=client,
        collection_name=img_collection,
        embeddings=embeddings
    )

    # check if collection exists
    get_collection(img_collection)

    # Generieren Sie eine eindeutige ID für das Bild
    img_id = str(generate_uuid())

    # Verarbeiten Sie die Keywords und erstellen Sie ein Document-Objekt
    vector = embeddings.embed_query(keywords)

    document = Document(
        page_content=keywords,  # Verwenden Sie die Keywords als page_content
        metadata={"img_link": img_link}   # Fügen Sie den Bildlink als Metadata hinzu
    )
    vectorstore.add_documents([document], ids=[img_id])
    

def search_image(query):
    print("Starting Similarity Search for: ", query)
    # Konvertiere die Suchanfrage in einen Vektor
    query_vector = embeddings.embed_query(query)

    # Führe die Similarity Search durch
    hits = client.search(
        collection_name=img_collection,
        query_vector=query_vector,
        limit=5
    )

    for hit in hits:
        print("Link: ", hit.payload['metadata']['img_link'])
        print("       Score: ", hit.score)

    # print("Results: ", hits)

    # img_link = []
    # for hit in hits:
    #     print("Payload: ", hit.payload)
    #     if(hit.score >= 0.8):
    #         print("Link: ", hit.payload['metadata']['img_link'])
    #         print("Score: ", hit.score)
    #         img_link.append(hit.payload['metadata']['img_link'])

    # Filtere die Treffer mit einem Score über 0.8
    filtered_hits = [hit for hit in hits if hit.score >= 0.861]

    # Sortiere die gefilterten Treffer nach Score in absteigender Reihenfolge
    sorted_hits = sorted(filtered_hits, key=lambda hit: hit.score, reverse=True)

    # Beschränke die Liste auf die ersten drei Elemente
    top_hits = sorted_hits[:5]

    for hit in top_hits:
        print("Top Hit: ", hit.score)

    # Extrahiere die Links aus den Top-Treffern
    img_links = [hit.payload['metadata']['img_link'] for hit in top_hits]
    
    return img_links


def save_knowledge(text_chunks):
    # vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)

    # check if collection exists
    get_collection(knowledge_collection)

    # define vectorstore
    vectorstore = get_vectorstore(knowledge_collection)
    print("saving documents in knowledge")
    # save chunks in vectorstore
    vectorstore.add_texts(text_chunks)
    print("SAVED!")

    return vectorstore
 

def get_vectorstore(collection_name):
    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings
    )

    return vectorstore


def get_collection(collection_name):
    try:
        print("TRYING")
        client.get_collection(collection_name=collection_name)
        print("Collection exists: ", collection_name)

    except Exception:
        print("Creating collection called ", collection_name)
        vectors_config = qdrant_client.http.models.VectorParams(
            size=1536, # dimensions of embeddings (opneai = 1536)
            distance=qdrant_client.http.models.Distance.COSINE
        )
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )
        print("Collection created: ", client.get_collection(collection_name=collection_name))





def save_single_document(content):
    # Generieren Sie eine eindeutige ID für das Dokument
    doc_id = str(generate_uuid())

    # Verarbeiten Sie den Inhalt und erstellen Sie ein Document-Objekt
    vector = embeddings.embed_query(content)

    document = Document(
        page_content=content,  # Verwenden Sie den gesamten Inhalt als page_content
    )

    # Speichern des Dokuments im Vectorstore
    vectorstore = get_vectorstore(knowledge_collection)
    vectorstore.add_documents([document], ids=[doc_id])

    print(f"Dokument {doc_id} erfolgreich hinzugefügt.")


def generate_uuid():
    return uuid.uuid4()
