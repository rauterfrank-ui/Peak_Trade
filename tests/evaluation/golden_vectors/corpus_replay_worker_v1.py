"""Cross-process corpus validation worker (BWP-7)."""

from __future__ import annotations

import json

from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
from tests.evaluation.golden_vectors.corpus_fixtures_v1 import FIXTURE_CORPUS_REF


def main() -> None:
    reg = VectorCorpusRegistryV1.default()
    result = reg.validate(FIXTURE_CORPUS_REF)
    print(
        json.dumps(
            {
                "corpus_identity_digest": result.corpus_identity_digest,
                "registry_order": list(result.registry_order),
            }
        )
    )


if __name__ == "__main__":
    main()
