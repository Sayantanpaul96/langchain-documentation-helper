import os
from typing import Any, Dict

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import ToolMessage, HumanMessage
from langchain_pinecone import PineconeVectorStore
from langchain.tools import tool
from langchain_ollama import OllamaEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.chat_models import init_chat_model

load_dotenv()

embeddings = OllamaEmbeddings(model=os.environ["OLLAMA_EMBEDDING_MODEL"])

vector_store = PineconeVectorStore(
    index_name=os.environ["PINECONE_INDEX_NAME"],
    embedding=embeddings
)

model = init_chat_model(
        model=os.environ["FCC_MODEL"],
        model_provider="anthropic",
        api_key=os.environ["FCC_API_KEY"],
        base_url="http://localhost:8082",
        temperature=0,  # Set to 0 for deterministic outputs
    )

@tool(response_format="content_and_artifact")
def retrive_context(query: str):
    """Retrive all the infomration that the use quries for langchain"""
    retrive_docs = vector_store.as_retriever().invoke(query, k=4)

    serialized = "\n\n".join(
        (f"Source: {doc.metadata.get('source', 'Unknown')} \n\n Content: {doc.page_content}")
        for doc in retrive_docs
    )

    # return the seralized content with the raw documentation
    # serialized is used for the LLM
    # retrive_docs is used for the application logic doesnt go to the LLM
    # thats why we seelct content_and_artifact as the tool.
    # content goes to the LLM and artifacts goes to the application layer
    return serialized, retrive_docs

def run_llm(query: str) -> Dict[str, Any]:
    """
        Run the RAG pipeline to answer a query using retrieved documentation

        Args:
            query: The user's question

        Returns:
            Dictionary Containing:
                -   answer: The generated Answer
                -   context: List of retrieved documents

    """

    # create an agent with the retrival tools

    system_prompt = (
        "You are a helpful AI assisatant that answers questions about Langchain documentation."
        "You have access to a tool that retrieves relivant documentation. "
        "Use the tool to find the relevant information before answering questions."
        "Always cite the sources you use in your answers."
        "If you cannot find the answer in the retrived documents say so."
    )

    agent = create_agent(model, tools=[retrive_context], system_prompt=system_prompt)

    message = [
        HumanMessage(
            content=query
        )
    ]

    #Invoke the agent
    response = agent.invoke({
        "messages": message
    })

    #Extract the answer from the last AI message
    answer = response['messages'][-1].content

    #extract the context documents form the ToolMessage artifacts
    context_docs = []
    for message in response["messages"]:
        #check if it is a ToolMessage with aritfacts
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            # the artifact should contain the list of Document objects
            if isinstance(message.artifact, list):
                context_docs.extend(message.artifact)

    return {
        "answer": answer,
        "context": context_docs
    }

def main():
    result = run_llm(query="What are streaming in langchain?")
    print(result)

if __name__ == "__main__":
    main()