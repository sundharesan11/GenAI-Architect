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
Answer the question based on the context provided, in a concise manner, in markdown and using bullet points if needed.

Context:
{context}

Question:
{question}

Answer:
"""

prompt = ChatPromptTemplate.from_template(prompt_template)

retriever = vector_store.as_retriever()


def format_docs_as_string(docs):
    """Convert list of documents to a single string for the prompt."""
    return "\n\n".join([doc.page_content for doc in docs])


def get_context_and_raw_docs(query):
    """Retrieve docs and return both the formatted context string and raw docs."""
    docs = retriever.invoke(query)
    context_string = format_docs_as_string(docs)
    docs_array = [doc.page_content for doc in docs]
    return {"context_string": context_string, "docs_array": docs_array}


def create_chain():
    chain = (
        RunnableParallel(
            {
                "context_data": lambda x: get_context_and_raw_docs(x),
                "question": RunnablePassthrough()
            }
        )
        | RunnableParallel(
            {
                "response": (
                    {
                        "context": lambda x: x["context_data"]["context_string"], 
                        "question": itemgetter("question")
                    } 
                    | prompt 
                    | model
                ),
                "docs": lambda x: x["context_data"]["docs_array"], 
            }
        )
    )
    return chain


def get_answer_and_docs(question: str):
    chain = create_chain()
    
    response = chain.invoke(question)
    
    answer = response["response"].content
    docs = response["docs"]

    return {
        "Answer": answer,
        "Documents": docs 
    }