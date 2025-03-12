from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.runnables import RunnableParallel
from operator import itemgetter
from decouple import config

from src.qdrant import vector_store


model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=config("OPENAI_API_KEY")
)

prompt_template = """
Answer the question based on the context provided, in a concise manner and using bullet points if needed.

Context:
{context}

Question:
{question}

Answer:
"""

prompt = ChatPromptTemplate.from_template(prompt_template)

retriever = vector_store.as_retriever()


def extract_text(docs):
    return "\n\n".join([doc.page_content for doc in docs])

def get_context(query):
    docs = retriever.invoke(query)
    return extract_text(docs)


def create_chain():

    chain = (
        RunnableParallel(
            {
                "context": lambda x: get_context(x),
                "question": RunnablePassthrough()
            }
        )
        | RunnableParallel(
            {
                "response": prompt | model,
                "context": itemgetter("context")
            }
        )
    )
    return chain


def get_answer_and_docs(question: str):
    chain = create_chain()
    
    response = chain.invoke(question)
    
    answer = response["response"].content
    context = response["context"]

    return {
        "answer": answer,
        "context": context
    }
