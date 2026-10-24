# Maharashtra OBC Education Chatbot Dataset

Dataset research date: 2026-10-18

## Files

- `maharashtra_obc_chatbot_knowledgebase_expanded.csv`: unified RAG corpus containing scheme entries, FAQ answer chunks, workflow guides, glossary chunks and source-directory entries.
- `maharashtra_obc_schemes_expanded.csv`: scheme records only, retaining every original field from the supplied 25-row CSV and adding normalized chatbot metadata.
- `maharashtra_obc_chatbot_source_register.csv`: deduplicated source register merged from the attached Excel workbook and sources reviewed for enrichment.
- `maharashtra_obc_seat_capacity_register.csv`: capacity-specific view. It deliberately separates scholarship awards, course slots, hostel facility counts and historical coaching intake figures.

## Suggested RAG ingestion

1. Use `retrieval_text` as the embedding/chunk text for the unified knowledgebase.
2. Keep `knowledge_id`, `record_type`, `category`, `scheme_id`, `state_or_scope_normalized`, `source_quality`, `data_status_normalized`, `seat_capacity_status`, `official_scheme_source_normalized`, `research_date` and `validity_notes` as metadata.
3. Prefer `record_type=scheme` for eligibility/benefit questions; include `faq`, `guide`, `glossary` and `source_directory` entries for natural question phrasing and application navigation.
4. When answering, include the official URL. When the source says `historical`, `needs verification`, or `not verified`, explicitly state that the current status/number is unconfirmed.
5. Do not sum unlike values. Scholarship slots, coaching intakes, hostel facility counts/beneficiaries and college admission-reservation seats are different metrics.
6. For voice support, detect language and answer in the user's language. The source text is predominantly English, with multilingual search hints for English, Hindi, Marathi, Gujarati, Tamil, Telugu and Bengali. Use multilingual embeddings and translate the grounded answer at response time; retain scheme names, amounts and links faithfully.
7. Before any live application advice, check the official portal/notice for current cycle, deadline and rules. Do not promise eligibility or approval.

## Data-quality notes

- The original 25 scheme records are preserved. Additional official department programmes and FAQs have been appended.
- Every scheme is assigned a confidence/source-quality status. Some historical and third-party records are intentionally retained for discovery but marked provisional.
- Fields can be blank for FAQ or portal records where scheme-specific metadata does not apply.
- This dataset is a retrieval aid, not an official determination of a student's eligibility.
