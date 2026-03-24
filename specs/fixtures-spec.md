# Test Fixtures Specification

## Purpose
Define deterministic fixture datasets and expected outcomes for ingestion and retrieval validation.

## Fixture Set A: Basic Policy Corpus
Location:
- tests/fixtures/corpus_a/

Files:
1. policy.txt
2. faq.txt
3. handbook.pdf
4. ignore.png (unsupported file, should be skipped)

Content requirements:
1. policy.txt includes refund policy sentence with unique keyword sequence.
2. faq.txt includes cancellation policy with distinct wording.
3. handbook.pdf includes shipping and support details.

Expected ingestion outcomes:
1. Supported files processed: 3
2. Unsupported files skipped: 1
3. Extraction failures: 0
4. Chunks generated: deterministic count stored in fixture lock file

## Fixture Set B: Edge-Case Text
Location:
- tests/fixtures/corpus_b/

Files:
1. long_paragraphs.txt
2. unicode_mixed.txt
3. short_lines.txt

Expected outcomes:
1. Chunking handles long text within token policy.
2. Normalization preserves semantic text meaning.
3. Deterministic chunk IDs remain stable across runs.

## Golden Retrieval Cases

## Case R-001
Input:
- query: "What is the refund window?"
- corpus: corpus_a
- top_k: 5

Expected:
1. Top result source id corresponds to policy document chunk.
2. Returned sources include refund policy chunk.
3. Retrieval ordering matches approved golden file.

## Case R-002
Input:
- query: "How can I contact support?"
- corpus: corpus_a
- top_k: 5

Expected:
1. Support-related chunk appears in top results.
2. Context builder includes support snippet under token budget.

## Case R-003
Input:
- query: "Cancellation conditions"
- corpus: corpus_a
- top_k: 3

Expected:
1. FAQ cancellation chunk ranked highest.
2. Sources response includes correct metadata path.

## Golden Files
Location:
- tests/fixtures/golden/

Required files:
1. ingestion_corpus_a_summary.json
2. retrieval_r001.json
3. retrieval_r002.json
4. retrieval_r003.json
5. debug_payload_r001.json

## Golden File Rules
1. Golden updates require explicit reviewer approval.
2. Golden files are updated only when behavior change is intended.
3. PR must include reason for golden update.

## Determinism Controls for Fixture Tests
1. Fixed retrieval parameters (top_k, thresholds).
2. Fixed chunking configuration.
3. Stable sort key for equal-score tie breaks.
4. Stable metadata serialization order where applicable.

## Minimal Fixture Lock Metadata
Each corpus includes lock file fixture.lock.json with:
1. chunk_size_tokens
2. chunk_overlap_tokens
3. embedding_model
4. vector_dimension
5. expected_chunk_count
6. corpus_checksum

## Acceptance for Fixture Framework
1. Fixture tests run in CI without external non-deterministic dependencies.
2. Failures clearly identify which case drifted.
3. Fixture data is small enough for fast local execution.
