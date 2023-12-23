from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from logic.database import save_single_document
import streamlit as st


def process_pdf_file(file):
    text = "" # init variable

    # loop pdfs
    pdf_reader = PdfReader(file) # init reader object
    for page in pdf_reader.pages: 
        print(page)
        text += page.extract_text() # extract text from all pages
    return text # get single string with all the content


def process_txt_file(file):
    # Konvertieren des hochgeladenen Files in einen String
    # loader = TextLoader(file)
    # documents = loader.load()
    # print("TXT-String: ", documents)
    # return documents  # Gibt den gesamten Text als String zurück

    text = file.getvalue().decode("utf-8")
    print("CONTENT: ", text)
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text) # return a list
    return chunks


def process_files(files):
    text = ""
    for file in files:
        if file.type == "application/pdf":
            # Verarbeiten der PDF-Datei
            raw_text = process_pdf_file(file)
        elif file.type == "text/plain":
            # Verarbeiten der TXT-Datei
            raw_text = process_txt_file(file)
        else:
            st.error("Unsupported file type")
            raise ValueError("Unsupported file type")
        
        text += raw_text

    # Splitten des Textes in Chunks
    chunks = get_text_chunks(text)
    print("Chunks: ", chunks)
    return chunks


def save_knowledge_from_files(files):
    for file in files:
        if file.type == "application/pdf":
            # Verarbeiten der PDF-Datei
            raw_text = process_pdf_file(file)
            # Speichern des gesamten PDF-Inhalts als ein Dokument
            save_single_document(raw_text)
        elif file.type == "text/plain":
            # Verarbeiten der TXT-Datei
            raw_text = process_txt_file(file)
            # Speichern des gesamten TXT-Inhalts als ein Dokument
            save_single_document(raw_text)
        else:
            st.error("Unsupported file type")
            raise ValueError("Unsupported file type")