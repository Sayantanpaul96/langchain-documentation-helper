import asyncio
import os
import ssl
from typing import Any, Dict, List

import certifi

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_tavily import TavilyCrawl, TavilyExtract, TavilyMap
from langchain_ollama import OllamaEmbeddings

from logger import (Colors, log_error, log_header, log_info, log_success, log_warning)

load_dotenv()

#Configure SSL context to use certifi package
ssl_context = ssl.create_default_context(cafile=certifi.where())
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

#embedding defination
embeddings = OllamaEmbeddings(model=os.environ['OLLAMA_EMBEDDING_MODEL'])

#vector Store Initilization
vector_store = PineconeVectorStore(index_name=os.environ['PINECONE_INDEX_NAME'], embedding=embeddings)

#tavily initialization
tavily_extract = TavilyExtract()
tavily_map = TavilyMap(max_depth=5, max_breadth=20, max_pages=1000)
tavily_crawl = TavilyCrawl()

async def index_documents_async(documents: List[Document], batch_size: int = 50):
    """Process documents in batches async"""
    log_header("Vecotr storage phase")
    log_info(
        f">> Vecotrtore Indexing: Perparing to add {len(documents)} documents to vector store"
    )

    #batch creation
    batches = [
        documents[i: i + batch_size] for i in range(0, len(documents), batch_size)
    ]

    log_info(
        f">> Vector Store Indexing: Spliting into {len(batches)} batches of {batch_size} documents each"
    )

    # Process the batches concurrently
    async def add_batch(batch: List[Document], batch_num: int):
        try:
            await vector_store.aadd_documents(batch)
            log_success(
                f">> Vector Store Indexing: Susseccfully added batch {batch_num}/{len(batches)} ({len(batch)}) docuemnts"
            )
        except Exception as e:
            log_error(f">> Vector Store Indexing: Failed to add batch {batch_num} - {e}")
            return False
        return True

    tasks = [add_batch(batch, i+1) for i, batch in enumerate(batches)]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    #Count successful batches
    successful = sum(1 for res in results if res is True)

    if successful == len(batches):
        log_success(
            f">> VectorStore Indexing: All batches processed successfully ({successful}/{len(batches)})"
        )
    else:
        log_warning(
            f">> Vector Store Indexing: Processed {successful}/{len(batches)} batches successfully"
        )

async def main():
    """Main async function to orcestrate the entire process"""

    log_header("DOCUMENTATION INGESTION PIPELINE")

    log_info(
        ">>> TavilyCrawl: Starting to Crawl Documentation from https://python.langchain.com",
        Colors.PURPLE
    )

    # tavily crawl - gives me only the urls of the pages
    # A few notes:
    # there was previously 2 more Tavily Invokations that were used
    # tavily map and tavily extract but tavily crawl covers most of the scenarios.
    # the usage of each - read the docs for more info :D
    crawl_result = tavily_crawl.invoke({
        "url": "https://python.langchain.com",
        "max_depth" : 2, # information for how many urls you want to see. more gives more latency
        "extract_depth": "advanced",
        # "instructions": "content on ai agent" # when we use ai agents this is very useful this
        # filters out only the pages that have infromation on ai_agents. Kind of like a filter
    })

    # Handle different possible response structures from TavilyCrawl
    if isinstance(crawl_result, dict) and 'results' in crawl_result:
        urls = [result['url'] for result in crawl_result['results']]
    elif isinstance(crawl_result, list):
        # If it's already a list of results
        urls = [result['url'] for result in crawl_result]
    else:
        # Fallback: assume it's a dict with url directly or handle error
        log_error(f"Unexpected crawl result structure: {type(crawl_result)}")
        raise ValueError("Unable to extract URLs from crawl result")

    log_info(
        f">>> TavilyCrawl: Found {len(urls)} URLs to extract content from"
    )

    # Extract content from URLs in batches of 20 (TavilyExtract limit)
    all_extract_results = []
    batch_size = 20
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i:i + batch_size]
        log_info(f">>> TavilyExtract: Processing batch {i//batch_size + 1}/{(len(urls) + batch_size - 1)//batch_size} ({len(batch_urls)} URLs)")

        extract_result = tavily_extract.invoke({
            "urls": batch_urls,
            "extract_depth": "advanced"
        })

        # Handle different possible response structures from TavilyExtract
        if isinstance(extract_result, dict) and 'results' in extract_result:
            batch_results = extract_result['results']
        elif isinstance(extract_result, list):
            # If it's already a list of results
            batch_results = extract_result
        else:
            # Fallback: assume it's a dict with the data directly or handle error
            log_error(f"Unexpected extract result structure: {type(extract_result)}")
            raise ValueError("Unable to extract results from extract response")

        all_extract_results.extend(batch_results)

    extract_results = all_extract_results

    # Create documents from extracted content
    all_docs = [
        Document(page_content=result['raw_content'], metadata={"source": result['url']})
        for result in extract_results
    ]

    log_success(
        f"Tavily Crawl: Successfully crawled {len(all_docs)} URLs from documentation site"
    )

    # chunking
    # total tokens ----> message in message out
    # contexts are token heavy no wonder so reserve and chunk
    # based on that. cause if input (query + context) is too much
    # there will be wastage if the context is not correctly chunked
    # also not make it too small or else the semantic meanings will be lost

    # rule of thumbs:
    # reserve the number of tokens for context lets say 2000 then 4 context is 500 tokens per chunk
    # not make it too small or else the semantic meanings will be lost
    # so balance based on the situation :D

    log_header("DOcument chunking Phase")

    log_info(
        f">>> Text Splitter: Processing {len(all_docs)} documents with 4000 chunks size and overlap of upto 200"
    )
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)

    splitted_docs = text_splitter.split_documents(all_docs)

    log_success(
        f"Text Splitter: Created {len(splitted_docs)} chunks from {len(all_docs)} documents"
    )

    #process documents async
    await index_documents_async(splitted_docs, batch_size=500)

    log_header("PIPELINE COMPLETED")
    log_success("Documentation ingestion pipeline finished successfully")
    log_info(">> Summary:", Colors.RED)
    log_info(f"     >> Documents extracted: {len(all_docs)}")
    log_info(f"     >> Chunks Created: {len(splitted_docs)}")


if __name__ == "__main__":
    asyncio.run(main())