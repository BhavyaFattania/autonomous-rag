from src.models.rag_config import RAGConfig
from src.rag_pipeline.retriever import build_retriever
from src.rag_pipeline.generator import generate_answer
from src.indexer.collection_manager import get_or_build_collection

async def run_pipeline(config: RAGConfig, questions: list[str]) -> tuple[list[str], list[list[str]], float]:
    """
    Run RAG pipeline for a list of questions.
    Returns (answers, contexts, cost_usd)
    """
    await get_or_build_collection(config)
    retriever = await build_retriever(config)
    
    answers = []
    contexts = []
    cost = 0.0 # Handled globally by openrouter.py, but we could return 0.0 or track delta
    
    from src.storage.cost_tracker import get_total
    start_cost = get_total()
    
    for q in questions:
        # Retrieve
        nodes = await retriever.aretrieve(q)
        context = [node.get_content() for node in nodes]
        contexts.append(context)
        
        # Generate
        ans = await generate_answer(q, context)
        answers.append(ans)
        
    end_cost = get_total()
    cost = end_cost - start_cost
        
    return answers, contexts, cost
