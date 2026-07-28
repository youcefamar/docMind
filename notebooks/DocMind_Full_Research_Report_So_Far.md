# DocMind RAG Research Report
## End-to-End Local Retrieval-Augmented Generation Benchmark — Final Research v1 Results

**Project:** DocMind  
**Research stage covered:** corpus preparation → extraction → chunking → gold benchmark → embedding comparison → retrieval comparison → evidence-aware metrics → hybrid retrieval → reranking → frozen-context generation benchmark → four-LLM comparison.  
**Current status:** Research v1 is complete. The frozen stack was evaluated on the 12-question TEST set and the four no-answer questions. Arabic, table, OCR, and larger-benchmark validation remain future feature work.

---

# 1. Executive Summary

DocMind is a local/open-source Retrieval-Augmented Generation (RAG) research project designed to answer questions over messy, heterogeneous company-like documents. The current cleaned corpus contains **44 files** across PDF, PPTX, and DOCX formats, with a strong French/English focus and a longer-term target of French/English/Arabic support.

The research intentionally separated retrieval from generation so that each component could be evaluated scientifically rather than tuning an opaque end-to-end pipeline.

The main experimental stages completed so far are:

1. Corpus cleanup and extraction.
2. Token-aware chunking at three sizes.
3. Gold question/evidence creation.
4. Gold-evidence coverage validation.
5. DEV/TEST split.
6. BM25 sparse retrieval baseline.
7. Dense retrieval with three embedding models.
8. Hybrid Dense + BM25 retrieval with Reciprocal Rank Fusion.
9. Evidence-unit-aware retrieval metrics.
10. Cross-encoder reranking.
11. Frozen top-5 contexts for generator comparison.
12. Four local generative LLM benchmarks.
13. Quality, multilingual, citation, speed, and VRAM analysis.

The strongest **retrieval embedding** tested was:

> **Qwen3-Embedding-0.6B**

The accuracy-oriented retrieval pipeline frozen for generation was:

> **Medium chunks (~320 tokens) → Qwen3-Embedding-0.6B → Dense + BM25 → RRF → BGE-reranker-v2-m3 → top 5**

The strongest generative LLM on the **46-question DEV generation benchmark** was:

> **Qwen3-4B-Instruct-2507**

Its automatic quality score was **0.7173**, and it won **34 of 46 DEV questions** in the automatic per-question comparison.

The current quality-first DocMind stack is therefore:

```text
Documents
   ↓
PDF / PPTX / DOCX extraction
   ↓
Medium token-aware chunks (~320 tokens, overlap 48)
   ↓
Qwen3-Embedding-0.6B
   ↓
Dense retrieval
   +
BM25 lexical retrieval
   ↓
Reciprocal Rank Fusion
   ↓
BGE-reranker-v2-m3
   ↓
Top-5 evidence
   ↓
Qwen3-4B-Instruct-2507
   ↓
Grounded answer with inline [S#] citations
```

For an efficiency-first deployment, **Phi-4-mini** is the most attractive tested alternative because it had the lowest average latency, highest throughput, and lowest observed peak VRAM.

---

# 2. Research Goal

DocMind is not simply a “chat with PDF” demo. The goal is to experimentally identify a strong locally deployable RAG architecture for heterogeneous real documents.

The intended system should eventually handle:

- PDF
- PPTX
- DOCX
- XLSX / table-heavy files in a dedicated experiment
- long documents
- short slide decks
- formulas
- structured and semi-structured text
- noisy extraction
- English
- French
- Arabic
- no-answer questions
- multi-evidence questions
- local VRAM / latency limits

The project deliberately postponed fine-tuning. The first goal was to determine how strong a carefully engineered retrieval, reranking, and prompting stack could become using existing open models.

---

# 3. Core Experimental Principles

## 3.1 Retrieval and generation are separate problems

The RAG pipeline was treated as:

```text
Question
  ↓
Retriever
  ↓
Evidence
  ↓
Generator
  ↓
Answer
```

A bad final answer can come from either:

### Retrieval failure

The correct evidence never reaches the LLM.

### Generation failure

The correct evidence is present, but the LLM fails to use it correctly.

Because of this, retrieval was optimized before comparing generative LLMs.

## 3.2 Change one variable at a time

Examples:

- Embedding models were compared on the same corpus and gold set.
- Chunk sizes were compared using the same questions.
- LLMs received the exact same frozen top-5 contexts.
- The grounded-answer instructions were kept semantically equivalent across models.
- Generation was deterministic with `do_sample=False`.
- A common 4-bit local-inference methodology was used where possible.

## 3.3 DEV is for selection; TEST is for final evaluation

The answerable benchmark was split into:

```text
DEV  = 46
TEST = 12
```

There were also:

```text
4 no-answer questions
```

DEV was used to choose the retrieval and generator configurations. TEST was intentionally kept outside the main model-selection loop.

---

# 4. Clean Research Corpus

The cleaned corpus contains exactly **44 files**.

## 4.1 PDF files

1. `1. Introduction.pdf`
2. `10. HMM.pdf`
3. `11. DTW.pdf`
4. `2. Concepts fondamentaux.pdf`
5. `3. Regression.pdf`
6. `4. Regression Logistique.pdf`
7. `5. Non-paramtriques-KNN.pdf`
8. `6. Naive Bayes.pdf`
9. `7. Clustering - part2.pdf`
10. `7. Clustering-part1.pdf`
11. `8. ANN-part1.pdf`
12. `8. ANN-part2.pdf`
13. `9. SVM.pdf`
14. `Ch1_Algbre1-2021-2022.pdf`
15. `Ch2_Algbre1-2021-2022.pdf`
16. `Chap5_cours_Analyse1.pdf`
17. `Cours_Data_ScienceComplet.pdf`
18. `Data Science Examen de Remplacement.pdf`
19. `Examen Final (Corrig).pdf`
20. `L1_MI_TD0_analyse2_21.pdf`
21. `L1_MI_TD1_analyse2_21.pdf`
22. `L1_MI_TD2_Analyse2_21.pdf`
23. `Rattrapage Data Science IA.pdf`
24. `Software Processes and Agile Practices.pdf`
25. `Solution Data Science Examen (1) (1).pdf`
26. `Sujet_corrige_CC_Analyse-1_21-22.pdf`
27. `TD N2-DM-25-26.pdf`
28. `frequents-sequence-2026-P1.pdf`

## 4.2 PowerPoint files

29. `AI and Biases.pptx`
30. `Academic writing.pptx`
31. `An introduction to Cognitive Science.pptx`
32. `Artificial Intelligence - An Overview.pptx`
33. `Cloud Computing Enhancing AI.pptx`
34. `Ethical AI.pptx`
35. `Intelligence Theory and Brain Properties.pptx`
36. `Machine Learning.pptx`
37. `RNN.pptx`
38. `Transformers.pptx`

## 4.3 Word files

39. `BMC I2E final1 (1).docx`
40. `Cc_Logique_Mathematique_2015-2016.docx`
41. `TP-N2-2023-2024.docx`
42. `controle-systeme-1-2019.docx`
43. `controle-systeme-2020.docx`
44. `controle-tp-finale-2016.docx`

Exact filenames were preserved because they are used as gold `document_id` / `doc_id` values.

---

# 5. Notebook / Research Architecture

The work was organized conceptually as:

## Notebook 01 — Corpus and extraction

- validate the 44-file allow-list
- extract PDF/PPTX/DOCX content
- retain source metadata
- audit extraction

## Notebook 02 — Retrieval benchmark

- token-aware chunking
- gold validation
- evidence coverage gate
- BM25
- dense retrieval
- hybrid RRF
- embedding comparison
- chunk-size comparison
- evidence-aware metrics
- reranking
- freeze winning retrieval contexts

## Notebook 03 — Grounded answer benchmark

- load frozen contexts
- run local generative LLMs
- measure quality proxies
- measure citations/language behavior
- measure latency / tokens per second / VRAM
- compare models question by question

Planned later experiments:

## Notebook 04 — Table representation

Dedicated comparison of table serializations instead of mixing table decisions into normal text retrieval.

## Notebook 05 — OCR stress test

Dedicated evaluation of scanned/noisy documents.

---

# 6. Extraction Pipeline

## 6.1 PDF extraction

PDF pages were extracted with PyMuPDF using page text extraction. Pages were retained independently so evidence could point to an exact page.

Metadata included:

- `doc_id`
- `file_type`
- `block_type`
- `location_type`
- `location_value`
- `char_count`
- `text_hash`

Typical evidence location:

```text
document_id = 3. Regression.pdf
location_type = page
location_value = 7
```

## 6.2 PPTX extraction

PowerPoint extraction operated slide by slide and included visible text shapes and tables when present.

Typical evidence location:

```text
location_type = slide
location_value = N
```

Slides contributed many benchmark questions from:

- Machine Learning
- AI and Biases
- Ethical AI
- RNN
- Transformers
- Artificial Intelligence - An Overview
- Cloud Computing Enhancing AI

## 6.3 DOCX extraction

Word extraction included:

- paragraphs
- tables

The initial implementation is coarser than the PDF/PPTX location model for normal paragraph text. Paragraph-level DOCX addressing is a reasonable future improvement.

## 6.4 Extraction artifacts

Produced artifacts included:

```text
docmind_clean_extracted_blocks.json
docmind_extraction_audit.csv
```

---

# 7. Chunking Experiment

Three token-aware chunking configurations were compared rather than choosing an arbitrary size.

The tokenizer used for the chunk-length function was based on:

> `intfloat/multilingual-e5-large`

Chunking used a recursive character splitter with tokenizer-aware length calculation.

## 7.1 Small

```text
target = 192 tokens
overlap = 32 tokens
chunks = 1546
```

## 7.2 Medium

```text
target = 320 tokens
overlap = 48 tokens
chunks = 1210
```

## 7.3 Large

```text
target = 448 tokens
overlap = 64 tokens
chunks = 1092
```

The experiment was designed to expose the trade-off:

```text
smaller chunks
→ more precise passages
→ higher risk of evidence fragmentation

larger chunks
→ more local context
→ higher risk of irrelevant text/noise
```

Chunk exports included:

```text
docmind_chunks_small.json
docmind_chunks_medium.json
docmind_chunks_large.json
```

---

# 8. Gold Benchmark

The starter gold benchmark contains:

```text
62 total questions
58 answerable
4 no-answer
```

Current answerable language coverage:

- French
- English

Current important gap:

- Arabic is not meaningfully represented yet.

The 58 answerable questions were split into:

```text
DEV  = 46
TEST = 12
```

Gold annotations point to passage-level evidence using:

- exact document ID
- exact page/slide location
- evidence anchor text

The benchmark covers topics such as:

- supervised learning
- regression
- logistic regression
- KNN
- clustering
- Naive Bayes
- SVM
- neural networks
- HMM
- DTW
- general machine learning
- AI bias
- ethical AI
- RNNs
- Transformers
- AI overview
- cloud computing
- Big Data

---

# 9. The q057 Evidence-Fragmentation Case

A major methodological improvement came from question `q057`:

> `Quels sont les trois V du Big Data définis dans le cours de Data Science ?`

Source:

```text
Cours_Data_ScienceComplet.pdf
page 109
```

Required information:

- Volume
- Vitesse
- Variété

The diagnostic showed:

## Small chunks

The required concepts were distributed across multiple chunks.

## Medium chunks

The evidence was distributed across two chunks.

## Large chunks

All three concepts could occur together in one chunk.

This was not an extraction error. It was real chunk-induced evidence fragmentation.

The gold annotation was therefore changed from one evidence item requiring all three terms in one chunk to three evidence units:

```text
Evidence unit 1 → Volume
Evidence unit 2 → Vitesse
Evidence unit 3 → Variété
```

After this fix:

```text
small  = 58/58 gold evidence coverage
medium = 58/58 gold evidence coverage
large  = 58/58 gold evidence coverage
```

This ensured all chunk configurations had a fair opportunity to retrieve all gold evidence.

---

# 10. Evidence-Aware Retrieval Metrics

A second methodological improvement was recognizing that overlapping chunks should not be treated as independent required facts.

If one evidence span matches several overlapping chunk IDs, naïvely counting all of those chunk IDs in a Recall denominator can distort chunk-size comparisons.

The benchmark therefore introduced evidence-unit metrics.

## 10.1 EvidenceRecall@K

Conceptually:

```text
# required evidence units represented in top K
---------------------------------------------
# total required evidence units
```

## 10.2 CompleteEvidence@K

Per question:

```text
1 = all required evidence units appear in top K
0 = at least one required evidence unit is missing
```

For RAG, `CompleteEvidence@5` is especially useful because it answers:

> Does the generator receive everything necessary to answer the question inside its top-5 context?

---

# 11. Embedding Models Tested

Three multilingual/open embedding models were compared.

## 11.1 BGE-M3

```text
BAAI/bge-m3
embedding dimension = 1024
```

## 11.2 multilingual-E5-large

```text
intfloat/multilingual-e5-large
embedding dimension = 1024
```

E5-style prefixes were used:

```text
query:
passage:
```

## 11.3 Qwen3-Embedding-0.6B

```text
Qwen/Qwen3-Embedding-0.6B
embedding dimension = 1024
```

Embeddings were normalized and cached for reuse.

---

# 12. Document Embedding Runs

Nine document-embedding combinations were generated:

```text
3 embedding models × 3 chunk sizes
```

## BGE-M3

| Chunk | Shape | Approx. embedding stage |
|---|---:|---:|
| small | 1546 × 1024 | ~9 s |
| medium | 1210 × 1024 | ~8 s |
| large | 1092 × 1024 | ~9 s |

## multilingual-E5-large

| Chunk | Shape | Approx. embedding stage |
|---|---:|---:|
| small | 1546 × 1024 | ~8 s |
| medium | 1210 × 1024 | ~9 s |
| large | 1092 × 1024 | ~9 s |

A model-loading warning involving `position_ids` appeared for E5, but the embeddings were produced successfully.

## Qwen3-Embedding-0.6B

| Chunk | Shape | Approx. embedding stage |
|---|---:|---:|
| small | 1546 × 1024 | ~34 s |
| medium | 1210 × 1024 | ~38 s |
| large | 1092 × 1024 | ~40 s |

Qwen embedding creation was slower in this environment, but its retrieval quality was the strongest.

---

# 13. Retrieval Engines

## 13.1 BM25

BM25 was used as the lexical/sparse baseline.

Simple Unicode tokenization was used:

```python
re.findall(r"\w+", text.lower(), re.UNICODE)
```

BM25 provides a useful baseline for:

- exact wording
- terminology
- numbers
- lexical overlap
- identifiers

## 13.2 Dense retrieval

Dense retrieval used normalized embeddings and:

```text
FAISS IndexFlatIP
```

Because the corpus is small, exact flat search is appropriate and avoids unnecessary ANN approximation error.

## 13.3 Hybrid retrieval

Dense and BM25 rankings were fused using Reciprocal Rank Fusion:

```text
score += 1 / (rrf_k + rank)
```

with:

```text
rrf_k = 60
```

---

# 14. Full Initial 21-Configuration DEV Retrieval Leaderboard

The experiment contained:

```text
3 BM25 baselines
+
3 chunk sizes × 3 embedding models × 2 retrieval modes
=
21 configurations
```

| Rank | Chunk | Embedding | Retriever | Latency ms | Recall@1 | Recall@3 | Recall@5 | MRR@10 | nDCG@10 |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | medium | qwen3_06b | dense | 0.128 | 0.7717 | 0.9783 | 1.0000 | 0.8703 | 0.9031 |
| 2 | large | qwen3_06b | dense | 0.114 | 0.7717 | 0.9674 | 0.9891 | 0.8703 | 0.8991 |
| 3 | small | qwen3_06b | dense | 0.118 | 0.7011 | 0.9457 | 0.9891 | 0.8359 | 0.8685 |
| 4 | medium | e5_large | dense | 0.125 | 0.7283 | 0.9022 | 0.9674 | 0.8377 | 0.8687 |
| 5 | large | e5_large | dense | 0.114 | 0.7283 | 0.9022 | 0.9674 | 0.8377 | 0.8687 |
| 6 | medium | qwen3_06b | hybrid | 4.381 | 0.8587 | 0.9348 | 0.9565 | 0.8993 | 0.9117 |
| 7 | large | bge_m3 | hybrid | 3.834 | 0.8152 | 0.9239 | 0.9565 | 0.8812 | 0.8976 |
| 8 | medium | bge_m3 | hybrid | 4.374 | 0.8152 | 0.9130 | 0.9565 | 0.8757 | 0.8941 |
| 9 | large | e5_large | hybrid | 3.832 | 0.7935 | 0.9239 | 0.9565 | 0.8667 | 0.8861 |
| 10 | medium | bge_m3 | dense | 0.120 | 0.6848 | 0.9022 | 0.9565 | 0.8136 | 0.8566 |
| 11 | large | qwen3_06b | hybrid | 3.836 | 0.8587 | 0.9239 | 0.9457 | 0.9029 | 0.9126 |
| 12 | large | bge_m3 | dense | 0.112 | 0.6848 | 0.9022 | 0.9457 | 0.8136 | 0.8562 |
| 13 | small | e5_large | dense | 0.133 | 0.7228 | 0.8750 | 0.9402 | 0.8299 | 0.8564 |
| 14 | small | bge_m3 | dense | 0.140 | 0.7011 | 0.8750 | 0.9402 | 0.8187 | 0.8554 |
| 15 | medium | e5_large | hybrid | 4.377 | 0.7935 | 0.9239 | 0.9348 | 0.8659 | 0.8860 |
| 16 | small | qwen3_06b | hybrid | 5.664 | 0.8315 | 0.8967 | 0.9239 | 0.8864 | 0.8981 |
| 17 | small | bge_m3 | hybrid | 5.689 | 0.7880 | 0.8750 | 0.9239 | 0.8540 | 0.8721 |
| 18 | medium | none | BM25 | 4.215 | 0.7283 | 0.7935 | 0.9130 | 0.7993 | 0.8334 |
| 19 | small | e5_large | hybrid | 5.676 | 0.7880 | 0.8750 | 0.9022 | 0.8555 | 0.8702 |
| 20 | large | none | BM25 | 3.687 | 0.7283 | 0.8152 | 0.9022 | 0.8058 | 0.8379 |
| 21 | small | none | BM25 | 5.512 | 0.7011 | 0.7663 | 0.8967 | 0.7768 | 0.7994 |

The clear raw retrieval result was:

> **Qwen3-Embedding-0.6B + medium chunks + dense retrieval** was the strongest initial DEV configuration on Recall@5.

---

# 15. Corrected Complete-Evidence Results

After switching to evidence-aware evaluation, the main pattern became clearer.

The three Qwen dense chunk configurations all reached:

```text
CompleteEvidence@5 = 1.0000
```

Key corrected results included:

| Configuration | CompleteEvidence@5 |
|---|---:|
| medium + Qwen dense | **1.0000** |
| large + Qwen dense | **1.0000** |
| small + Qwen dense | **1.0000** |
| large + E5 dense | 0.9783 |
| medium + E5 dense | 0.9565 |
| medium + Qwen hybrid | 0.9565 |
| large + BGE hybrid | 0.9565 |
| medium + BGE hybrid | 0.9565 |
| large + E5 hybrid | 0.9565 |
| medium + BGE dense | 0.9565 |
| large + Qwen hybrid | 0.9565 |
| large + BGE dense | 0.9565 |
| small + E5 dense | 0.9348 |
| small + BGE dense | 0.9348 |
| medium + E5 hybrid | 0.9348 |
| small + Qwen hybrid | 0.9348 |
| small + BGE hybrid | 0.9348 |
| medium BM25 | 0.9130 |
| small + E5 hybrid | 0.9130 |
| large BM25 | 0.9130 |
| small BM25 | 0.8913 |

Important finding:

> Hybrid retrieval often improved early ranking, but dense Qwen retrieval was extremely reliable at preserving complete evidence inside top 5.

---

# 16. Cross-Encoder Reranking

The selected reranker was:

> **BAAI/bge-reranker-v2-m3**

An initial `FlagReranker` path stalled during multi-device initialization. The implementation was replaced by direct Transformers sequence-classification inference on one explicit GPU.

Each finalist reranked:

```text
46 questions × top 30 candidates
= 1380 query-passage pairs
```

Typical reranking run times for one finalist were roughly 9–14 seconds in the observed Kaggle session.

---

# 17. Reranking Finalists and Trade-Off

Four retrieval finalists were compared before/after reranking.

| Chunk | Retriever | Version | EvidenceRecall@1 | EvidenceRecall@3 | EvidenceRecall@5 | CompleteEvidence@5 |
|---|---|---|---:|---:|---:|---:|
| medium | dense | Base | 0.7754 | **0.9783** | **1.0000** | **1.0000** |
| medium | dense | Reranked | **0.9058** | 0.9348 | 0.9783 | 0.9783 |
| large | dense | Base | 0.7826 | **0.9783** | **1.0000** | **1.0000** |
| large | dense | Reranked | 0.8913 | 0.9348 | 0.9783 | 0.9783 |
| small | dense | Base | 0.7101 | 0.9565 | **1.0000** | **1.0000** |
| small | dense | Reranked | 0.8841 | 0.9348 | 0.9783 | 0.9783 |
| medium | hybrid | Base | 0.8623 | 0.9348 | 0.9565 | 0.9565 |
| medium | hybrid | Reranked | **0.8841** | 0.9348 | **1.0000** | **1.0000** |

This exposed …2804 tokens truncated…2 French

| Model | Correctness | Groundedness | Quality | Language compliance |
|---|---:|---:|---:|---:|
| Granite-3.3-2B | 0.5658 | 0.4974 | 0.6113 | 0.6667 |
| Phi-4-mini | 0.4904 | 0.4942 | 0.5436 | 0.8000 |
| **Qwen3-4B** | **0.6478** | **0.6558** | **0.7036** | **1.0000** |
| xLAM-7B | 0.5513 | 0.5843 | 0.4887 | 0.3333 |

This is one of the most important DocMind findings.

Qwen's French behavior was clearly stronger than the alternatives, especially because it combined:

```text
French correctness proxy   = 0.6478
French groundedness        = 0.6558
French quality             = 0.7036
French language compliance = 1.0000
```

xLAM's French language compliance of `0.3333` is particularly unsuitable for this French-heavy benchmark.

---

# 31. Performance by Question Type

DEV question-type distribution:

```text
comparison = 1
conceptual = 9
definition = 10
fact       = 26
```

## 31.1 Comparison

| Model | Correctness | Groundedness | Quality |
|---|---:|---:|---:|
| Granite | 0.7095 | 0.6947 | 0.7524 |
| Phi | 0.7602 | 0.5485 | 0.7441 |
| Qwen | 0.7085 | 0.7610 | **0.7638** |
| xLAM | **0.8244** | **0.7734** | 0.6570 |

Only one comparison question exists, so this category is too small for a strong conclusion.

## 31.2 Conceptual

| Model | Correctness | Groundedness | Quality |
|---|---:|---:|---:|
| Granite | 0.5418 | 0.5772 | 0.6142 |
| Phi | 0.5788 | 0.6211 | 0.6279 |
| **Qwen** | **0.6456** | **0.7004** | **0.7003** |
| xLAM | 0.5377 | 0.5498 | 0.5196 |

Qwen is strongest on conceptual questions.

## 31.3 Definition

| Model | Correctness | Groundedness | Quality |
|---|---:|---:|---:|
| Granite | 0.6860 | 0.6004 | 0.7277 |
| Phi | 0.7211 | 0.6781 | 0.7628 |
| **Qwen** | **0.7452** | **0.7335** | **0.7833** |
| xLAM | 0.7282 | 0.6575 | 0.6681 |

Qwen also wins definitions.

## 31.4 Fact

| Model | Correctness | Groundedness | Quality |
|---|---:|---:|---:|
| Granite | 0.5717 | 0.4864 | 0.6089 |
| Phi | 0.4719 | 0.4581 | 0.5223 |
| **Qwen** | **0.6292** | **0.6683** | **0.6960** |
| xLAM | 0.5715 | 0.6368 | 0.4853 |

Fact questions are the largest category, and Qwen wins clearly.

---

# 32. Top 10 Model Disagreements

| Question | Granite | Phi | Qwen | xLAM | Range |
|---|---:|---:|---:|---:|---:|
| q058 | 0.680551 | 0.001382 | **0.852714** | 0.537973 | 0.851332 |
| q008 | 0.635192 | 0.785873 | **0.838337** | 0.000000 | 0.838337 |
| q012 | 0.639141 | 0.000000 | **0.836014** | 0.532347 | 0.836014 |
| q020 | 0.620585 | 0.000000 | **0.720616** | 0.484772 | 0.720616 |
| q003 | 0.617045 | 0.009240 | **0.676785** | 0.545722 | 0.667545 |
| q005 | 0.698159 | 0.675849 | **0.787686** | 0.211154 | 0.576532 |
| q032 | 0.373167 | 0.037731 | **0.555398** | 0.307783 | 0.517666 |
| q010 | 0.376658 | 0.052685 | **0.535243** | 0.361737 | 0.482558 |
| q018 | 0.770322 | 0.875938 | **0.897414** | 0.439884 | 0.457529 |
| q007 | 0.638230 | 0.753489 | **0.808273** | 0.403677 | 0.404597 |

These are especially valuable manual-review cases.

Extremely low scores such as ~0 for some Phi/xLAM questions may reflect:

- genuine answer failure
- wrong-language response
- missing citations
- formatting behavior
- sensitivity/limitations of the embedding-based evaluator

They should not be interpreted blindly.

---

# 33. Efficiency Results

## 33.1 Average latency

| Model | Avg latency |
|---|---:|
| **Phi-4-mini** | **5.556 s/question** |
| xLAM-7B | 6.361 s/question |
| Qwen3-4B | 8.675 s/question |
| Granite-3.3-2B | 11.262 s/question |

Winner:

> **Phi-4-mini**

## 33.2 Generation throughput

| Model | Tokens/s |
|---|---:|
| **Phi-4-mini** | **11.58** |
| Granite-3.3-2B | 9.34 |
| xLAM-7B | 9.05 |
| Qwen3-4B | 8.52 |

Winner:

> **Phi-4-mini**

## 33.3 Peak observed VRAM

| Model | Peak VRAM |
|---|---:|
| **Phi-4-mini** | **1.90 GB** |
| Granite-3.3-2B | 1.91 GB |
| Qwen3-4B | 3.21 GB |
| xLAM-7B | 3.49 GB |

Winner:

> **Phi-4-mini**

---

# 34. Quality vs Efficiency Decision

The research produced two legitimate deployment profiles.

## Quality-first profile

Use:

> **Qwen3-4B**

because it had:

- best aggregate quality
- best groundedness
- best French behavior
- strong citation behavior
- perfect measured language compliance
- 34/46 automatic wins

## Efficiency-first profile

Use:

> **Phi-4-mini**

because it had:

- lowest latency
- highest throughput
- lowest peak VRAM

The trade-off is lower answer quality, especially on French/fact questions.

---

# 35. Current Recommended DocMind Architecture

## Extraction

```text
PDF  → page-level extraction
PPTX → slide-level extraction
DOCX → paragraph/table extraction
```

## Chunking

```text
medium
~320 tokens
48-token overlap
```

## Embedding

```text
Qwen/Qwen3-Embedding-0.6B
```

## Sparse retrieval

```text
BM25
```

## Dense retrieval

```text
normalized embeddings
FAISS IndexFlatIP
```

## Fusion

```text
Reciprocal Rank Fusion
rrf_k = 60
```

## Reranking

```text
BAAI/bge-reranker-v2-m3
top 30 candidates reranked
```

## Generator context

```text
top 5 chunks
```

## Generator

```text
Qwen/Qwen3-4B-Instruct-2507
4-bit local inference
```

## Response behavior

```text
source-grounded
same-language answer
inline [S#] citations
deterministic decoding
```

---

# 36. Main Artifacts Produced

## Extraction

```text
docmind_clean_extracted_blocks.json
docmind_extraction_audit.csv
```

## Chunking

```text
docmind_chunks_small.json
docmind_chunks_medium.json
docmind_chunks_large.json
```

## Gold benchmark

```text
rag_gold_questions.json
rag_gold_questions_starter_v1.json
```

## Frozen DEV generation benchmark

```text
docmind_generation_dev_frozen.json
```

## Retrieval results

```text
dev_retrieval_summary.csv
dev__<chunk>__<model>__<retriever>.csv
```

## Generation outputs

```text
qwen3_4b__dev_generations.json
phi4_mini__dev_generations.json
granite_2b__dev_generations.json
xlam_7b__dev_generations.json
```

## Generation report outputs

```text
generation_model_summary.csv
generation_comparison_per_question.csv
generation_language_summary.csv
generation_question_type_summary.csv
generation_question_wins.csv
generation_model_summary.json
DOCMIND_GENERATION_BENCHMARK_REPORT.md
```

---

# 37. Plots Produced

Generation benchmark plots:

```text
01_generation_quality_metrics.png
02_automatic_quality_score.png
03_average_latency.png
04_tokens_per_second.png
05_peak_vram.png
06_quality_vs_latency.png
07_quality_vs_vram.png
```

Retrieval-analysis plots designed during the experiment included:

- Recall@5 leaderboard
- Recall@1 / Recall@3 / Recall@5 comparison
- dense embedding-model × chunk-size heatmap
- hybrid-minus-dense delta
- Recall@5 vs MRR@10
- retrieval quality vs retrieval-only latency
- language breakdown
- question-type breakdown

---

# 38. Strongest Findings So Far

## Retrieval finding 1

> **Qwen3-Embedding-0.6B was the best tested embedding model on this corpus/DEV benchmark.**

## Retrieval finding 2

> **Medium chunks (~320 tokens) were the strongest overall chunking compromise.**

## Retrieval finding 3

> **Evidence-aware evaluation is necessary when comparing chunk sizes.**

The q057 Big Data example demonstrated why one “gold chunk” is not always a scientifically correct representation of required evidence.

## Retrieval finding 4

> **Hybrid retrieval does not automatically dominate dense retrieval.**

Hybrid improved some early ranks but sometimes hurt top-5 complete evidence before reranking.

## Retrieval finding 5

> **Cross-encoder reranking strongly improves rank #1 but can hurt multi-evidence coverage if used carelessly.**

## Retrieval finding 6

> **Medium Qwen hybrid + BGE reranker achieved a strong combination of top-1 ranking and complete top-5 evidence on DEV.**

## Generation finding 1

> **Qwen3-4B is the strongest overall tested generator on DEV.**

## Generation finding 2

> **Phi-4-mini is the strongest efficiency-oriented alternative.**

## Generation finding 3

> **French behavior materially changes the generator ranking.**

An English-only benchmark would have hidden important weaknesses.

## Generation finding 4

> **xLAM's action/agent strengths did not translate into superior multilingual grounded QA under this setup.**

---

# 39. What Has Been Demonstrated vs What Has Not

## Demonstrated within this benchmark

- Qwen3-Embedding-0.6B is the best tested embedding model on DEV.
- Medium chunking is a strong choice for this corpus.
- BM25 alone is weaker than the best dense/hybrid approaches.
- Evidence-unit scoring is more scientifically appropriate than naïve overlapping chunk-ID recall.
- Reranking improves early ordering but can change evidence coverage.
- Qwen3-4B is the strongest tested generator on the 46-question DEV set.
- Phi-4-mini is the best tested efficiency option.
- Qwen has the strongest French behavior among the four tested generators.

## Not demonstrated

This work does **not** prove that:

- Qwen3-4B is universally the best RAG generator.
- Qwen3-Embedding-0.6B is universally the best multilingual embedding model.
- 320-token chunks are optimal for every corpus.
- hybrid + reranking always beats dense retrieval.
- the automatic quality score equals true human factual correctness.
- the system is robust for Arabic.
- the system is robust for OCR-heavy scanned documents.
- the system is robust for table/spreadsheet-heavy QA.
- the system has been validated on a large public benchmark.

All current conclusions are conditional on this corpus, benchmark, extraction, chunking, prompt, and environment.

---

# 40. Important Current Limitations

## 40.1 Benchmark size

The generator comparison uses only:

> **46 answerable DEV questions**

This is very useful for engineering/model selection but still small for publication-level claims.

## 40.2 Held-out TEST

The frozen stack was evaluated exactly once on the 12-question answerable TEST split without retuning.

Final TEST retrieval results:

- EvidenceRecall@1: **0.7500**
- EvidenceRecall@3: **1.0000**
- EvidenceRecall@5: **1.0000**
- CompleteEvidence@5: **1.0000**

Qwen3-4B generation on the frozen TEST contexts achieved an automatic quality score of **0.7220**, compared with **0.7173** on DEV. This is a small held-out result, not a claim of universal generalization.

## 40.3 No-answer behavior

All four no-answer questions produced the safe refusal:

> “Not found in the provided documents.”

Observed results:

- refusal accuracy: **4/4**
- false-answer rate: **0/4**
- citation count: **0/4**
- unsupported-citation rate: **0/4**

The two French no-answer questions received the English refusal sentence, so they are marked as language-policy limitations. The prompt currently requires both an exact English refusal and same-language answers, which creates a conflict.

## 40.4 Arabic

Arabic is part of the project goal but is not meaningfully represented in the current gold benchmark.

## 40.5 DOCX coverage

The corpus contains Word files, but the starter gold questions are much more concentrated on PDF/PPTX content.

## 40.6 Table-specific QA

Table-heavy retrieval and generation still deserve a separate representation experiment.

## 40.7 OCR

Scanned/noisy-document OCR failure modes have not been systematically stress-tested.

## 40.8 Automatic evaluator limitations

The evaluator is itself a model.

It can:

- reward paraphrases
- miss subtle contradictions
- be sensitive to language/style
- miss an incorrect number in an otherwise similar answer
- give reasonable similarity to partially correct text

Therefore automatic metrics are best used for ranking and triage, not as the sole final truth.

---

# 41. Current Winner Summary

## Retrieval embedding winner

> **Qwen3-Embedding-0.6B**

## Chunk configuration winner

> **Medium — ~320 tokens, overlap 48**

## Accuracy-oriented retrieval pipeline

> **Qwen dense + BM25 + RRF + BGE-reranker-v2-m3**

## Simpler retrieval pipeline

> **Qwen dense only**

## Generative quality winner

> **Qwen3-4B-Instruct-2507**

## Efficiency winner

> **Phi-4-mini**

## Current complete quality-first DocMind stack

```text
PDF / PPTX / DOCX
        ↓
structured extraction
        ↓
320-token chunks
48-token overlap
        ↓
Qwen3-Embedding-0.6B
        ↓
dense FAISS retrieval
        +
BM25
        ↓
RRF fusion
        ↓
BGE-reranker-v2-m3
        ↓
top-5 evidence
        ↓
Qwen3-4B-Instruct-2507
        ↓
same-language grounded answer
with inline source citations
```

---

# 42. Future Research and Feature Work

Research v1 is closed. The following items are intentionally deferred and should be implemented and evaluated as independent product features:

## XLSX and table QA

- Add spreadsheet ingestion and table-aware retrieval.
- Compare Markdown tables, row-wise serialization, schema-plus-row chunks, and structured DuckDB/text-to-SQL where aggregation requires it.
- Do not make text-to-SQL mandatory for every spreadsheet question.

## OCR and scanned documents

- Add OCR as a separate extraction capability.
- Test image-only PDFs, low-resolution scans, rotated pages, French scans, Arabic scans, and scanned tables.
- Keep OCR evaluation separate from retrieval and generation evaluation.

## Arabic support

- Add dedicated Arabic extraction and retrieval/generation questions.
- Test RTL extraction, Unicode normalization, Arabic-to-Arabic retrieval, Arabic-to-French retrieval, French-to-Arabic retrieval, and mixed-language queries.
- Do not claim full Arabic support before these tests pass.

## Harder and larger gold benchmark

- Add more answerable and no-answer questions.
- Add multi-evidence, multi-document, near-duplicate, lexical-mismatch, spelling-error, and harder-distractor cases.
- Use expanded benchmarks to validate new features rather than delay product integration.

## Stronger judging and deployment validation

- Combine deterministic checks, manual review, disagreement inspection, and an independent judge where useful.
- Profile the integrated system on the target CPU laptop; Kaggle GPU timings are not laptop measurements.

# 43. Final Project Status

Completed:

```text
Corpus cleanup                     ✅
44-file allow-list                 ✅
PDF extraction                     ✅
PPTX extraction                    ✅
DOCX extraction                    ✅
Extraction audit                   ✅
Token-aware chunking               ✅
3 chunk-size experiment            ✅
Gold question benchmark            ✅
Evidence coverage validation       ✅
q057 multi-evidence correction     ✅
DEV / TEST split                   ✅
BM25 baseline                      ✅
Dense retrieval                    ✅
Hybrid RRF retrieval               ✅
BGE-M3 embeddings                  ✅
multilingual-E5 embeddings         ✅
Qwen3 embeddings                   ✅
EvidenceRecall metrics             ✅
CompleteEvidence@5                 ✅
Cross-encoder reranking            ✅
Frozen top-5 generation contexts   ✅
Qwen3-4B generation                ✅
Phi-4-mini generation              ✅
Granite-3.3-2B generation          ✅
xLAM-7B generation                 ✅
Efficiency comparison              ✅
French / English breakdown         ✅
Question-type breakdown            ✅
Automatic generation scoring       ✅
Question-by-question wins          ✅
Benchmark plots                    ✅
Shareable generation report        ✅
```

Research v1 closeout completed:

```text
Locked 12-question TEST retrieval          ✅
Locked 12-question TEST generation         ✅
Four no-answer generations                 ✅
Manual no-answer review                    ✅
Final research report update               ✅
```

Future feature work:

```text
Arabic benchmark                         future
Table-specific benchmark                  future
OCR stress test                           future
Larger publication-grade gold set          future
Local CPU deployment profiling             next product milestone
```


---

# 44. Bottom Line

The frozen research v1 stack is:

> **Qwen3-Embedding-0.6B + medium chunks + hybrid retrieval + BGE reranking + Qwen3-4B generation**

The frozen stack achieved **1.0000 CompleteEvidence@5** on the 12-question TEST retrieval evaluation and **0.7220** automatic generation quality on the frozen TEST contexts.

For a lower-resource deployment, the strongest current alternative is:

> **Qwen3 retrieval pipeline + Phi-4-mini generation**

The current evidence strongly supports **Qwen3-4B as DocMind's quality-first generator** because it combines:

- highest overall automatic quality
- highest groundedness
- strong semantic correctness
- strong source citation behavior
- perfect measured language compliance
- strongest French performance
- 34 of 46 question wins

At the same time, the project has also produced an important engineering conclusion:

> There is no single “best model” independent of deployment goals. Qwen is the quality winner; Phi is the efficiency winner.

---

# Appendix A — Key Numerical Results at a Glance

## Benchmark structure

```text
Corpus files                     44
Gold questions                   62
Answerable                       58
No-answer                         4
DEV answerable                   46
TEST answerable                  12
```

## Chunk counts

```text
Small                            1546
Medium                           1210
Large                            1092
```

## Gold evidence coverage after correction

```text
Small                            58/58
Medium                           58/58
Large                            58/58
```

## Selected retrieval pipeline on DEV

```text
medium + Qwen3 embedding + hybrid + BGE reranker

EvidenceRecall@1       0.8841
EvidenceRecall@3       0.9348
EvidenceRecall@5       1.0000
CompleteEvidence@5     1.0000
```

## Locked TEST validation

```text
TEST retrieval questions          12
EvidenceRecall@1                  0.7500
EvidenceRecall@3                  1.0000
EvidenceRecall@5                  1.0000
CompleteEvidence@5                1.0000

TEST Qwen3-4B quality             0.7220
TEST semantic correctness         0.6696
TEST groundedness                 0.6507
TEST citation presence            1.0000
TEST citation validity            1.0000
TEST citation support             0.7428
TEST average latency              7.784 s
TEST average throughput           8.573 tokens/s
```

## No-answer validation

```text
No-answer questions                4
Correct refusals                   4/4
False answers                      0/4
Unsupported citations              0/4
French refusal-language issues     2/4
```

## Generation benchmark

```text
DEV generation questions          46
Models tested                      4
Evaluation rows                  184
Unique evaluator texts           848
```

## Automatic generation quality

```text
Qwen3-4B             0.7173
Granite-3.3-2B       0.6389
Phi-4-mini           0.6000
xLAM-7B              0.5354
```

## Question wins

```text
Qwen3-4B             34
Phi-4-mini            10
Granite-3.3-2B         1
xLAM-7B                1
```

## Efficiency

```text
Fastest model:
Phi-4-mini
5.556 s/question

Highest throughput:
Phi-4-mini
11.58 tokens/s

Lowest observed peak VRAM:
Phi-4-mini
1.90 GB

Best overall quality:
Qwen3-4B
0.7173
```

---

# Appendix B — Reproducibility Checklist

A faithful reproduction should preserve:

- the same 44-file corpus
- the same document filenames / IDs
- the same extracted text
- the same extraction metadata
- the same token-aware chunk sizes and overlaps
- the same gold JSON
- the same evidence-unit interpretation
- the same DEV/TEST IDs
- the same embedding normalization
- the same FAISS similarity method
- the same BM25 tokenization
- the same RRF constant
- the same reranker and top-N candidate count
- the same frozen top-5 contexts
- the same prompt semantics
- deterministic generation
- the same quantization methodology where possible
- the same evaluator model
- the same automatic quality weights

Any material change should be recorded as a new experiment rather than silently merged with this benchmark.

---

# Appendix C — Methodological Cautions

1. **Retrieval latency numbers in the original leaderboard are retrieval-only**, not full user-query latency including query embedding.
2. **Automatic semantic correctness is a proxy**, not an exact-match factual score.
3. **Citation support is semantic**, not a formal entailment test.
4. **Language detection can make mistakes**, especially on short answers.
5. **Question-type categories are imbalanced**, especially the single comparison question.
6. **The benchmark is French-heavy**, which is useful for DocMind but means aggregate metrics reflect that distribution.
7. **xLAM required different chat-role serialization**, even though the semantic instructions were preserved.
8. **4-bit inference memory and checkpoint download size are different quantities.**
9. **The LLM leaderboard compares four models on DEV; the frozen Qwen3-4B result was additionally evaluated on the 12-question TEST split.**
10. **No-answer behavior was evaluated on four questions; Arabic, OCR, and table-specific robustness remain future work.**

---

**End of report.**


