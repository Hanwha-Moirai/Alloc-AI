from typing import List

from domain.models import SearchResult


class DefaultPromptBuilder:
    def build(self, query: str, contexts: List[SearchResult]) -> str:
        context_text = "\n\n".join(f"[{item.doc_id}] {item.text}" for item in contexts)
        return (
            "Use the following context to answer the question. "
            "Cite sources by doc id.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {query}\nAnswer:"
        )
