from typing import List

from domain.models import SearchResult


def filter_results(results: List[SearchResult], allowed_doc_ids: List[str]) -> List[SearchResult]:
    if not allowed_doc_ids:
        return results
    allowed = set(allowed_doc_ids)
    return [item for item in results if item.doc_id in allowed]
