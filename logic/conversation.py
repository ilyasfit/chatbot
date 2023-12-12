from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory # memory
from langchain.chains import ConversationalRetrievalChain # allows chatting with context incl. memory
from logic.database import get_vectorstore, knowledge_collection


def get_conversation_chain():
    vectorstore = get_vectorstore(knowledge_collection)
    llm = ChatOpenAI(temperature=0.2)
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain 


def process_question(question):
    conversation_chain = get_conversation_chain()
    # define prompt
    prompt = f"""
    Du bist ein in Rente gegangener Marketmaker mit einem enormen Wissensschatz und ausgereifter Weisheit über Trading Analysis. 
    Du beantwortest kontextgenau, präzise, strukturiert und leicht nachvollziehbar 
    (als wenn du einem 10 jährigen antwortest) Fragen auf deutscher Sprache.\n\n
    Bitte überliefere die kontextgenauste und passenste Antwort zur Frage des Benutzers.
    Die Frage: {question}
    """

    response = conversation_chain({'question': prompt})
    return response

    

