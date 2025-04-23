from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Generator

from langchain_core.documents import Document as LangChainDocument
from loguru import logger
from tqdm import tqdm
from zenml.steps import step

from apps.brain_ai_assistant.application.rag import (
    get_retriever,
    get_splitter,
)
from apps.brain_ai_assistant.domain import Document


@step
def process_documents_for_rag(
    documents: list[Document],
    collection_name: str,
    processing_batch_size: int,
    processing_max_workers: int,
    chunk_size: int,
) -> None:
    """Process documents by chunking, embedding, and loading into Pinecone.

    Args:
        documents: List of documents to process.
        collection_name: Name to use as Pinecone namespace.
        processing_batch_size: Number of documents to process in each batch.
        processing_max_workers: Maximum number of concurrent processing threads.
        retriever_type: Type of retriever to use for document processing.
        embedding_model_dimension: Dimension of the embedding vectors.
        chunk_size: Size of text chunks for splitting documents.
        mock: Whether to use mock processing. Defaults to False.
        device: Device to run embeddings on ('cpu' or 'cuda'). Defaults to 'cpu'.
    """
    # Get the retriever (configured for Pinecone)
    retriever = get_retriever()
    
    # Get the basic text splitter
    splitter = get_splitter(chunk_size=chunk_size)

    # Convert documents to LangChain format
    langchain_docs = [
        LangChainDocument(
            page_content=doc.content, metadata=doc.metadata.model_dump()
        )
        for doc in documents
        if doc
    ]
    
    # Process documents in batches
    process_docs(
        retriever,
        langchain_docs,
        splitter=splitter,
        namespace=collection_name,  # Use collection_name as namespace in Pinecone
        batch_size=processing_batch_size,
        max_workers=processing_max_workers,
    )


def process_docs(
    retriever: Any,
    docs: list[LangChainDocument],
    splitter: Any,
    namespace: str = "",
    batch_size: int = 4,
    max_workers: int = 2,
) -> list[None]:
    """Process LangChain documents into Pinecone using thread pool.

    Args:
        retriever: Pinecone retriever instance.
        docs: List of LangChain documents to process.
        splitter: Text splitter instance for chunking documents.
        namespace: Namespace to use in Pinecone.
        batch_size: Number of documents to process in each batch.
        max_workers: Maximum number of concurrent threads.

    Returns:
        List of None values representing completed batch processing results.
    """
    batches = list(get_batches(docs, batch_size))
    results = []
    total_docs = len(docs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_batch, retriever, batch, splitter, namespace)
            for batch in batches
        ]

        with tqdm(total=total_docs, desc="Processing documents") as pbar:
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                pbar.update(batch_size)

    return results


def get_batches(
    docs: list[LangChainDocument], batch_size: int
) -> Generator[list[LangChainDocument], None, None]:
    """Return batches of documents to ingest into Pinecone.

    Args:
        docs: List of LangChain documents to batch.
        batch_size: Number of documents in each batch.

    Yields:
        Generator[list[LangChainDocument]]: Batches of documents of size batch_size.
    """
    for i in range(0, len(docs), batch_size):
        yield docs[i : i + batch_size]


def process_batch(
    retriever: Any,
    batch: list[LangChainDocument],
    splitter: Any,
    namespace: str = "",
) -> None:
    """Ingest batches of documents into Pinecone by splitting and embedding.

    Args:
        retriever: Pinecone retriever instance.
        batch: List of documents to ingest in this batch.
        splitter: Text splitter instance for chunking documents.
        namespace: Namespace to use in Pinecone.

    Raises:
        Exception: If there is an error processing the batch of documents.
    """
    try:
        # Split documents into chunks
        split_docs = splitter.split_documents(batch)
        
        # Add documents to vectorstore with namespace
        retriever.index.upsert(
            vectors=[
                {
                    "id": doc.metadata.get("id", f"doc_{i}"),
                    "values": retriever.embeddings.embed_query(doc.page_content),
                    "metadata": {
                        "text": doc.page_content,
                        **doc.metadata
                    },
                    "sparse_values": retriever.sparse_encoder.encode_documents([doc.page_content])[0] if retriever.sparse_encoder else None
                }
                for i, doc in enumerate(split_docs)
            ],
            namespace=namespace
        )

        logger.info(f"Successfully processed {len(batch)} documents to Pinecone namespace '{namespace}'.")
    except Exception as e:
        logger.warning(f"Error processing batch of {len(batch)} documents: {str(e)}")