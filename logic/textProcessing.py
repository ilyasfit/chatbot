from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter

def get_pdf_text(pdf_docs):
    text = "" # init variable

    # loop pdfs
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf) # init reader object
        for page in pdf_reader.pages: 
            print(page)
            text += page.extract_text() # extract text from all pages
    return text # get single string with all the content


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text) # return a list
    return chunks
