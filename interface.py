from dotenv import load_dotenv
load_dotenv()
import os

import streamlit as st
from logic.database import get_documents, save_knowledge, save_image, search_documents, update_document, update_image_document
from logic.textProcessing import get_pdf_text, get_text_chunks

def load_documents(collection_name):
    # Überprüfen, ob die Dokumente bereits im session_state gespeichert sind
    if f'documents_{collection_name}' not in st.session_state:
        # Wenn nicht, laden Sie die Dokumente und speichern Sie sie im session_state
        st.session_state[f'documents_{collection_name}'] = get_documents(collection_name)
    return st.session_state[f'documents_{collection_name}']



# Funktion zum Erstellen des Knowledge-Tabs
def knowledge_tab():
    st.header("Knowledge Database")
    st.session_state['current_tab'] = 'Knowledge'

    # Suchleiste
    search_query = st.text_input("Knowledge Database durchsuchen")
    
    # Liste der Vektoren
    st.subheader("Dokumente")

    if search_query:
        search_results = search_documents(os.getenv("KNOWLEDGE_COLLECTION_NAME"), search_query)
        display_documents(search_results)
    else:
        documents = load_documents(os.getenv("KNOWLEDGE_COLLECTION_NAME"))
        display_documents(documents=documents)

    # Pagination
    # if st.button("Load More", key="load_more_knowledge"):
    #     st.session_state['current_page_knowledge'] += 1
    #     documents = load_documents(st.session_state['current_page_knowledge'], os.getenv("KNOWLEDGE_COLLECTION_NAME"))
    #     display_documents(documents)

# Funktion zum Erstellen des Images-Tabs
def images_tab():
    st.header("Image Database")
    st.session_state['current_tab'] = 'Images'

    # Suchleiste
    search_query = st.text_input("Search in Image Database")

    # Liste der Vektoren
    st.subheader("Dokumente")
    documents = get_documents(os.getenv("IMAGE_COLLECTION_NAME"))

    if search_query:
        search_results = search_documents(os.getenv("IMAGE_COLLECTION_NAME"), search_query)
        display_image_documents(search_results)
    else:
        documents = load_documents(os.getenv("IMAGE_COLLECTION_NAME"))
        display_image_documents(documents=documents)


    # Pagination
    # if st.button("Load More", key="load_more_images"):
    #     # Hier kommt die Logik zum Nachladen weiterer Vektoren
    #     pass


def display_image_documents(documents):
    for i, doc in enumerate(documents):
        with st.expander(" ".join(doc.get("page_content", "").split())):
            img_link = doc.get("metadata", {}).get("img_link", "")
            if img_link:
                st.image(img_link, caption="Image Preview", width=300)
                
            editable_keywords = st.text_input("Keywords", value=" ".join(doc.get("page_content", "").split()), key=f"keywords_{i}")
            editable_img_link = st.text_input("Image Link", value=doc.get("metadata", {}).get("img_link", ""), key=f"img_link_{i}")

            if st.button("Speichern", key=f"save_img_{i}"):
                # Logik zum Speichern der Änderungen
                update_image_document(os.getenv("IMAGE_COLLECTION_NAME"), doc["id"], editable_keywords, editable_img_link)
                st.success("Änderungen gespeichert!")

            # TODO: DELETE hinzufügen
            # if st.button("Löschen", key=f"delete_img_{i}"):
            #     # delete_document(os.getenv("IMAGE_COLLECTION_NAME"), doc["id"])
            #     st.success("Dokument gelöscht!")


def display_documents(documents):
    for i, doc in enumerate(documents):
        with st.expander(f"Dokument {i + 1}"):
            editable_text = st.text_area("Inhalt", value=doc.get("page_content", ""), height=300, key=f"text_{i}")
            if st.button("Speichern", key=f"save_{i}"):
                # Logik zum Speichern der Änderungen
                update_document(os.getenv("KNOWLEDGE_COLLECTION_NAME"), doc["id"], editable_text)
                st.success("Änderungen gespeichert!")

            # TODO: DELETE hinzufügen
            # if st.button("Löschen", key=f"delete_{i}"):
            #     # Logik zum Löschen des Dokuments
            #     st.success("Dokument gelöscht!")


def main():
    # Radio-Buttons zur Auswahl des Tabs
    tab_choice = st.sidebar.radio("Tab auswählen", ["Knowledge", "Images"])

    if 'current_page_knowledge' not in st.session_state:
        st.session_state['current_page_knowledge'] = 0

    if tab_choice == "Knowledge":
        knowledge_tab()
        st.sidebar.header("Knowledge hinzufügen")
        # Sidebar-Inhalte für Knowledge Tab
        pdf_docs = st.sidebar.file_uploader("Upload PDFs", accept_multiple_files=True)
        if st.sidebar.button("Prozessieren und hochladen"):
            with st.spinner("Prozessieren..."): # Animation
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)

                # get text chunks
                text_chunks = get_text_chunks(raw_text) # will return a list

                # create vector store
                st.session_state.vectorstore = save_knowledge(text_chunks)
                
                st.rerun()
            



    elif tab_choice == "Images":
        images_tab()
        st.sidebar.header("Image hinzufügen")
        # Sidebar-Inhalte für Images Tab
        img_link = st.sidebar.text_input("Image Link")
        keywords = st.sidebar.text_input("Keywords")
        if st.sidebar.button("Prozessieren und hochladen"):
            if img_link and keywords:
                with st.spinner("Prozessieren..."): # Animation
                    save_image(img_link, keywords)
                st.sidebar.success("Bild erfolgreich hinzugefügt!")
                st.rerun()
            else:
                st.sidebar.error("Bitte geben Sie sowohl einen Bildlink als auch Keywords ein.")

if __name__ == "__main__":
    main()