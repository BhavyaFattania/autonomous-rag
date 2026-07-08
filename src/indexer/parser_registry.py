"""Node parser factory and configuration encoding.

Maps parser type + config to parser instances and deterministic cache keys.
"""

from llama_index.core.node_parser import (
    HierarchicalNodeParser,
    SemanticDoubleMergingSplitterNodeParser,
    SemanticSplitterNodeParser,
    SentenceSplitter,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)

from src.models.rag_config import RAGConfig


def parser_slug(config: RAGConfig) -> str:
    """Encode parser type and config as cache-safe string slug."""
    parts = [
        config.node_parser.replace("_", "-"),
        str(config.chunk_size),
        str(config.chunk_overlap),
    ]
    if config.node_parser == "sentence_window":
        parts.append(f"w{config.window_size}")
    if config.node_parser in {"semantic", "semantic_double"}:
        parts.append(f"t{config.semantic_threshold}")
        parts.append(f"b{config.semantic_buffer_size}")
    return "_".join(parts)


def build_node_parser(config: RAGConfig, embed_model=None):
    """Factory: instantiate node parser based on config type and parameters."""
    if config.node_parser == "sentence":
        return SentenceSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
    if config.node_parser == "token":
        return TokenTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
    if config.node_parser == "sentence_window":
        return SentenceWindowNodeParser.from_defaults(
            window_size=config.window_size or 3,
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )
    if config.node_parser == "semantic":
        return SemanticSplitterNodeParser.from_defaults(
            embed_model=embed_model,
            breakpoint_percentile_threshold=config.semantic_threshold or 95,
            buffer_size=config.semantic_buffer_size or 1,
        )
    if config.node_parser == "semantic_double":
        return SemanticDoubleMergingSplitterNodeParser.from_defaults(
            embed_model=embed_model,
            initial_threshold=(config.semantic_threshold or 95) / 100,
            appending_threshold=0.8,
            merging_threshold=0.8,
            max_chunk_size=config.chunk_size,
            merging_range=config.semantic_buffer_size or 1,
        )
    if config.node_parser == "hierarchical":
        chunk_sizes = _hierarchical_chunk_sizes(config.chunk_size)
        return HierarchicalNodeParser.from_defaults(
            chunk_sizes=chunk_sizes,
            chunk_overlap=config.chunk_overlap,
        )
    raise ValueError(f"Unknown node_parser: {config.node_parser}")


def _hierarchical_chunk_sizes(leaf_size: int) -> list[int]:
    """Generate hierarchical chunk size levels; leaf_size is smallest."""
    sizes = [2048, 1024, leaf_size]
    unique = sorted({size for size in sizes if size >= 128}, reverse=True)
    return unique if unique else [2048, 512, 128]
