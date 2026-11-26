# CHANGELOG — OpenVEF Planning v1.3.7 CANDIDATE (from v1.3.6)

**v1.3.7 CANDIDATE, not audited.** Built by `proposals/v1.3.7/build_candidate.py` from `baseline/OpenVEF_Planning_v1_3_6/`
(read-only, unchanged) under owner decision D-024 (Krishika). Rationale for every correction, with the
conflicting v1.3.6 text and the alternatives rejected: `proposals/v1.3.7/CORRECTIONS-v1.3.7-candidate.md`.

- Every edit replaces text inside one line; no line moves, so line citations are the same in both packs.
- `correction` = C1–C16; `A1`, `A2` = numbered amendments; `S` = a stale reference fixed (D-025 item 3;
  `line` `name` = a file renamed); `label` = the in-file candidate label; `derived` = a hash or byte length
  that follows mechanically from another edit. Old and new text are the replaced part of the line, unless
  `line` is `all` (whole-file replacement).
- **Kept on purpose (not stale):** references that record history — the v1.3.6 change log, build, correction
  and audit records (Files 03, 48, 50, 56, 57, 58, 63 and the audit transcripts), and statements of what
  v1.3.6 did — and the owners' records (Files 16, 23), which describe owner decisions on v1.3.6 and are not
  rewritten for a candidate the owners have not approved.
- The 61 `archive_*` entries of `27_SHA256SUMS.txt` are not in the extracted baseline and are not in this copy.

| # | Correction | PD | Fixtures | File | Line |
|---|---|---|---|---|---|
| E01 | C1 | PD-02 (2) | M48, M50, M53, M54, M58 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 175 |
| E02 | A2 (copy of C1) | PD-02 (2) | M48, M50, M53, M54, M58 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 118 |
| E03 | C2 | PD-02 (1) | M48, M50, M53, M54, M58 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E04 | A2 (copy of C2) | PD-02 (1) | M48, M50, M53, M54, M58 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 119 |
| E05 | C2 | PD-02 (1) | M50 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E06 | A2 (copy of C2) | PD-02 (1) | M50 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 119 |
| E07 | C2 | PD-02 (1) | M53 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E08 | A2 (copy of C2) | PD-02 (1) | M53 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 119 |
| E09 | C2 | PD-02 (1) | M54 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E10 | A2 (copy of C2) | PD-02 (1) | M54 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 119 |
| E11 | C2 | PD-02 (1) | M58 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E12 | A2 (copy of C2) | PD-02 (1) | M58 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 119 |
| E13 | C2 | PD-02 (1), (3) | M48, M50, M53, M54, M58 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 176 |
| E14 | A2 (copy of C2) | PD-02 (1), (3) | M48, M50, M53, M54, M58 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 119 |
| E15 | C3 | PD-02 (3) | M54 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 185 |
| E16 | A2 (copy of C3) | PD-02 (3) | M54 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 128 |
| E17 | C10 | PD-01 | M41, M42, M47 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 185 |
| E18 | A2 (copy of C10) | PD-01 | M41, M42, M47 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 128 |
| E19 | C4 | PD-03 | M14, M17, M41, M48, M50, M53, M54, M58 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 176 |
| E20 | C5 | PD-06, PD-25 | M27 | `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 83 |
| E21 | C6 | PD-06, PD-25 | M27 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 133 |
| E22 | C7 | PD-22 | none | `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 7 |
| E23 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 174 |
| E24 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 308 |
| E25 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 353 |
| E26 | C8 | PD-24 | none | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 383 |
| E27 | C8 | PD-24 | none | `11_Comparative_Research_Matrix.md` | 37 |
| E28 | C9 | PD-04 | M36 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 27 |
| E29 | C9 | PD-04 | M36 | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 15 |
| E30 | C9 | PD-04 | M36 | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 177 |
| E31 | A2 (copy of C9) | PD-04 | M36 | `25_Common_System_and_Repair_Prompt_Templates.txt` | 120 |
| E32 | C10 | PD-01 | M41 | `41_F18_Fixture_Inputs/M41.json` | 33 |
| E33 | C10 | PD-01 | M42 | `41_F18_Fixture_Inputs/M42.json` | 16 |
| E34 | C10 | PD-01 | M42 | `41_F18_Fixture_Inputs/M42.json` | 23 |
| E35 | C10 | PD-01 | M47 | `41_F18_Fixture_Inputs/M47.json` | 16 |
| E36 | C10 | PD-01 | M47 | `41_F18_Fixture_Inputs/M47.json` | 23 |
| E37 | C10 | PD-01 | M47 | `41_F18_Fixture_Inputs/M47.json` | 24 |
| E38 | S | — | — | `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` | 1 |
| E39 | S | — | — | `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` | 4 |
| E40 | S | — | — | `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` | 9 |
| E41 | S | — | — | `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` | 184 |
| E42 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 1 |
| E43 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 4 |
| E44 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 9 |
| E45 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 81 |
| E46 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 81 |
| E47 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 83 |
| E48 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 187 |
| E49 | A2 (copy of S) | — | — | `25_Common_System_and_Repair_Prompt_Templates.txt` | 130 |
| E50 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 288 |
| E51 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 555 |
| E52 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 555 |
| E53 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 559 |
| E54 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 1 |
| E55 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 3 |
| E56 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 3 |
| E57 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 3 |
| E58 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 3 |
| E59 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 3 |
| E60 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 63 |
| E61 | S | — | — | `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 1 |
| E62 | S | — | — | `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 109 |
| E63 | S | — | — | `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` | 1 |
| E64 | S | — | — | `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` | 17 |
| E65 | S | — | — | `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` | 84 |
| E66 | S | — | — | `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` | 84 |
| E67 | S | — | — | `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` | 1 |
| E68 | S | — | — | `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` | 3 |
| E69 | S | — | — | `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` | 5 |
| E70 | S | — | — | `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` | 48 |
| E71 | S | — | — | `33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json` (was `33_Prompt_Assembly_Sidecar_v1.3.6.json` | 2 |
| E72 | S | — | — | `33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json` (was `33_Prompt_Assembly_Sidecar_v1.3.6.json` | 189 |
| E73 | S | — | — | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 1 |
| E74 | S | — | — | `38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json` (was `38_Authoring_Packet_Manifest_Template_v1.3.6.json` | 71 |
| E75 | S | — | — | `README.md` | 1 |
| E76 | S | — | — | `README.md` | 3 |
| E77 | S | — | — | `README.md` | 7 |
| E78 | S | — | — | `README.md` | 8 |
| E79 | S | — | — | `README.md` | 11 |
| E80 | S | — | — | `README.md` | 13 |
| E81 | S | — | — | `README.md` | 14 |
| E82 | S | — | — | `README.md` | 14 |
| E83 | S | — | — | `README.md` | 16 |
| E84 | S | — | — | `README.md` | 17 |
| E85 | S | — | — | `README.md` | 9 |
| E86 | S | — | — | `README.md` | 46 |
| E87 | label | — | M41 | `41_F18_Fixture_Inputs/M41.json` | 3 |
| E88 | label | — | M42 | `41_F18_Fixture_Inputs/M42.json` | 3 |
| E89 | label | — | M47 | `41_F18_Fixture_Inputs/M47.json` | 3 |
| E90 | label | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | 560 |
| E91 | label | — | — | `25_Common_System_and_Repair_Prompt_Templates.txt` | 132 |
| E92 | label | — | — | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | 190 |
| E93 | label | — | — | `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | 110 |
| E94 | label | — | — | `10_LLM_Era_Hardware_Verification_Literature_Review.md` | 418 |
| E95 | label | — | — | `11_Comparative_Research_Matrix.md` | 44 |
| E96 | label | — | — | `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` | 195 |
| E97 | label | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | 73 |
| E98 | label | — | — | `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` | 98 |
| E99 | label | — | — | `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` | 55 |
| E100 | label | — | — | `README.md` | 49 |
| E101 | S | — | — | `22_Source_Access_Provenance_Log_v1.2.md` | 8 |
| E102 | S | — | — | `22_Source_Access_Provenance_Log_v1.2.md` | 9 |
| E103 | S | — | — | `22_Source_Access_Provenance_Log_v1.2.md` | 10 |
| E104 | S | — | — | `22_Source_Access_Provenance_Log_v1.2.md` | 11 |
| E105 | S | — | — | `22_Source_Access_Provenance_Log_v1.2.md` | 12 |
| E106 | label | — | — | `22_Source_Access_Provenance_Log_v1.2.md` | 47 |
| E107 | C6 + A1 | PD-06, PD-25 | M27 | `41_F18_Fixture_Inputs/M27.json` | all |
| E108 | derived | — | M27 | `41_F18_Fixture_Inputs/fixture-index.json` | 380 |
| E109 | derived | — | M27 | `41_F18_Fixture_Inputs/fixture-index.json` | 381 |
| E110 | derived | — | M41 | `41_F18_Fixture_Inputs/fixture-index.json` | 562 |
| E111 | derived | — | M41 | `41_F18_Fixture_Inputs/fixture-index.json` | 563 |
| E112 | derived | — | M42 | `41_F18_Fixture_Inputs/fixture-index.json` | 579 |
| E113 | derived | — | M42 | `41_F18_Fixture_Inputs/fixture-index.json` | 580 |
| E114 | derived | — | M47 | `41_F18_Fixture_Inputs/fixture-index.json` | 644 |
| E115 | derived | — | M47 | `41_F18_Fixture_Inputs/fixture-index.json` | 645 |
| E116 | label | — | — | `41_F18_Fixture_Inputs/fixture-index.json` | 2 |
| E117 | S | — | — | `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` | name |
| E118 | S | — | — | `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` | name |
| E119 | S | — | — | `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` | name |
| E120 | S | — | — | `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` | name |
| E121 | S | — | — | `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` | name |
| E122 | S | — | — | `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` | name |
| E123 | S | — | — | `33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json` (was `33_Prompt_Assembly_Sidecar_v1.3.6.json` | name |
| E124 | S | — | — | `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` | name |
| E125 | S | — | — | `38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json` (was `38_Authoring_Packet_Manifest_Template_v1.3.6.json` | name |
| E126 | derived | — | — | `27_SHA256SUMS.txt` | 1 |
| E127 | derived | — | — | `27_SHA256SUMS.txt` | 2 |
| E128 | derived | — | — | `27_SHA256SUMS.txt` | 11 |
| E129 | derived | — | — | `27_SHA256SUMS.txt` | 12 |
| E130 | derived | — | — | `27_SHA256SUMS.txt` | 20 |
| E131 | derived | — | — | `27_SHA256SUMS.txt` | 21 |
| E132 | derived | — | — | `27_SHA256SUMS.txt` | 24 |
| E133 | derived | — | — | `27_SHA256SUMS.txt` | 28 |
| E134 | derived | — | — | `27_SHA256SUMS.txt` | 29 |
| E135 | derived | — | — | `27_SHA256SUMS.txt` | 30 |
| E136 | derived | — | — | `27_SHA256SUMS.txt` | 31 |
| E137 | derived | — | — | `27_SHA256SUMS.txt` | 34 |
| E138 | derived | — | — | `27_SHA256SUMS.txt` | 36 |
| E139 | derived | — | — | `27_SHA256SUMS.txt` | 66 |
| E140 | derived | — | — | `27_SHA256SUMS.txt` | 80 |
| E141 | derived | — | — | `27_SHA256SUMS.txt` | 81 |
| E142 | derived | — | — | `27_SHA256SUMS.txt` | 86 |
| E143 | derived | — | — | `27_SHA256SUMS.txt` | 182 |
| E144 | derived | — | — | `27_SHA256SUMS.txt` | 202 |

## E01 — C1 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L175 · PD-02 (2) · fixtures: M48, M50, M53, M54, M58

Old:

```text
The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED` and diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; `M54` uses error class `HALT_SIGNATURE_SCHEMA` and diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.
```

New:

```text
Error classes of change-class control expectations are stated by rule, not by fixture: a control expectation whose diagnostic CODE is `EVALUATOR_REVISION_REQUIRED` has error class `EVALUATOR_REVISION_REQUIRED`; one whose CODE is `AUTHORING_REVISION_REQUIRED` has error class `AUTHORING_REVISION_REQUIRED`; and one whose CODE is `HALT_SIGNATURE_SCHEMA` has error class `HALT_SIGNATURE_SCHEMA`. This rule applies only to these three codes; it does not change the M41 error class `MID_RUN_REEVALUATION` or any stage-map row. The study-reset vector uses diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; the halt-signature vector uses diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.
```

## E02 — A2 (copy of C1) · `25_Common_System_and_Repair_Prompt_Templates.txt` L118 · PD-02 (2) · fixtures: M48, M50, M53, M54, M58

Old:

```text
The `M53` study-reset vector uses error class `AUTHORING_REVISION_REQUIRED` and diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; `M54` uses error class `HALT_SIGNATURE_SCHEMA` and diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.
```

New:

```text
Error classes of change-class control expectations are stated by rule, not by fixture: a control expectation whose diagnostic CODE is `EVALUATOR_REVISION_REQUIRED` has error class `EVALUATOR_REVISION_REQUIRED`; one whose CODE is `AUTHORING_REVISION_REQUIRED` has error class `AUTHORING_REVISION_REQUIRED`; and one whose CODE is `HALT_SIGNATURE_SCHEMA` has error class `HALT_SIGNATURE_SCHEMA`. This rule applies only to these three codes; it does not change the M41 error class `MID_RUN_REEVALUATION` or any stage-map row. The study-reset vector uses diagnostic `AUTHORING_REVISION_REQUIRED|reason=AUTHOR_VISIBLE_OR_ESTIMAND_CHANGED`; the halt-signature vector uses diagnostic `HALT_SIGNATURE_SCHEMA|reason=COMPONENT_VALUES_ENUMERATED`.
```

## E03 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M48, M50, M53, M54, M58

Old:

```text
**Closed `required_action` literals used by lifecycle fixtures:** `M48` = `
```

New:

```text
**Closed `required_action` literals, by change class:** `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` = `
```

## E04 — A2 (copy of C2) · `25_Common_System_and_Repair_Prompt_Templates.txt` L119 · PD-02 (1) · fixtures: M48, M50, M53, M54, M58

Old:

```text
**Closed `required_action` literals used by lifecycle fixtures:** `M48` = `
```

New:

```text
**Closed `required_action` literals, by change class:** `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` = `
```

## E05 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M50

Old:

```text
`; `M50` = `
```

New:

```text
`; `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` = `
```

## E06 — A2 (copy of C2) · `25_Common_System_and_Repair_Prompt_Templates.txt` L119 · PD-02 (1) · fixtures: M50

Old:

```text
`; `M50` = `
```

New:

```text
`; `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` = `
```

## E07 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M53

Old:

```text
`; `M53` = `
```

New:

```text
`; `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` = `
```

## E08 — A2 (copy of C2) · `25_Common_System_and_Repair_Prompt_Templates.txt` L119 · PD-02 (1) · fixtures: M53

Old:

```text
`; `M53` = `
```

New:

```text
`; `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` = `
```

## E09 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M54

Old:

```text
`; `M54` = `
```

New:

```text
`; `HALT_SIGNATURE_COMPONENT_ENUMERATION` = `
```

## E10 — A2 (copy of C2) · `25_Common_System_and_Repair_Prompt_Templates.txt` L119 · PD-02 (1) · fixtures: M54

Old:

```text
`; `M54` = `
```

New:

```text
`; `HALT_SIGNATURE_COMPONENT_ENUMERATION` = `
```

## E11 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1) · fixtures: M58

Old:

```text
`; and `M58` = `
```

New:

```text
`; and `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` = `
```

## E12 — A2 (copy of C2) · `25_Common_System_and_Repair_Prompt_Templates.txt` L119 · PD-02 (1) · fixtures: M58

Old:

```text
`; and `M58` = `
```

New:

```text
`; and `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` = `
```

## E13 — C2 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L176 · PD-02 (1), (3) · fixtures: M48, M50, M53, M54, M58

Old:

```text
Each literal is a closed local control expectation, not a model-feedback diagnostic. `M48` re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. `M50` invalidates all designs and all arm × design slots and starts a new preregistered study. `M53` resets the preregistered design set and weights and requires fresh confirmatory slots. `M58` invalidates both arms for the affected design only when membership, estimand and weights remain unchanged.
```

New:

```text
Each literal is a closed local control expectation, not a model-feedback diagnostic. The change classes are closed and have these cases: `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` is the evaluator revision of §7b path (b); `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` is a shared-item revision; `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` is a study reset; `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` is a design-specific revision while membership, estimand and weights remain unchanged; and `HALT_SIGNATURE_COMPONENT_ENUMERATION` is the halt-signature domain check. Closed scope tokens: for an evaluator revision, `rerun_scope_rule` = `shared_evaluator_component_all_designs_and_all_arm_x_design_slots; design_specific_component_affected_design_in_both_arms` (§7b: shared component, both designs and every slot; design-specific component, that design in both arms). For a shared-item revision, `affected_slots` = `all_designs_x_all_arms` (§7b: every scheduled slot across both designs and both arms). For a design-specific revision, `affected_scope` = `affected_design_in_both_arms` and `unaffected_design_scope` = `not_invalidated_when_membership_estimand_and_weights_are_unchanged`. An evaluator revision re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. A shared-item revision invalidates all designs and all arm × design slots and starts a new preregistered study. A study reset resets the preregistered design set and weights and requires fresh confirmatory slots. A design-specific revision invalidates both arms for the affected design only when membership, estimand and weights remain unchanged.
```

## E14 — A2 (copy of C2) · `25_Common_System_and_Repair_Prompt_Templates.txt` L119 · PD-02 (1), (3) · fixtures: M48, M50, M53, M54, M58

Old:

```text
Each literal is a closed local control expectation, not a model-feedback diagnostic. `M48` re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. `M50` invalidates all designs and all arm × design slots and starts a new preregistered study. `M53` resets the preregistered design set and weights and requires fresh confirmatory slots. `M58` invalidates both arms for the affected design only when membership, estimand and weights remain unchanged.
```

New:

```text
Each literal is a closed local control expectation, not a model-feedback diagnostic. The change classes are closed and have these cases: `FROZEN_EVALUATOR_SOURCE_BINARY_OR_CONFIG_CHANGED` is the evaluator revision of §7b path (b); `SHARED_AUTHOR_VISIBLE_OR_ESTIMAND_DEFINING_ITEM_CHANGED` is a shared-item revision; `DESIGN_MEMBERSHIP_OR_ESTIMAND_OR_WEIGHT_CHANGED_AFTER_CONFIRMATORY_START` is a study reset; `DESIGN_SPECIFIC_AUTHOR_VISIBLE_ITEM_CHANGED` is a design-specific revision while membership, estimand and weights remain unchanged; and `HALT_SIGNATURE_COMPONENT_ENUMERATION` is the halt-signature domain check. Closed scope tokens: for an evaluator revision, `rerun_scope_rule` = `shared_evaluator_component_all_designs_and_all_arm_x_design_slots; design_specific_component_affected_design_in_both_arms` (§7b: shared component, both designs and every slot; design-specific component, that design in both arms). For a shared-item revision, `affected_slots` = `all_designs_x_all_arms` (§7b: every scheduled slot across both designs and both arms). For a design-specific revision, `affected_scope` = `affected_design_in_both_arms` and `unaffected_design_scope` = `not_invalidated_when_membership_estimand_and_weights_are_unchanged`. An evaluator revision re-evaluates the affected scope with the same frozen artifact bytes and zero new confirmatory generation calls. A shared-item revision invalidates all designs and all arm × design slots and starts a new preregistered study. A study reset resets the preregistered design set and weights and requires fresh confirmatory slots. A design-specific revision invalidates both arms for the affected design only when membership, estimand and weights remain unchanged.
```

## E15 — C3 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L185 · PD-02 (3) · fixtures: M54

Old:

```text
for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes; `stable_diagnostic_code` is exactly the corresponding `halt_code` token.
```

New:

```text
for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes (rule token `stable_error_class_rule` = `simple_exception_class_for_SIMULATOR_ERROR_else_NONE`); `stable_diagnostic_code` is exactly the corresponding `halt_code` token (rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).
```

## E16 — A2 (copy of C3) · `25_Common_System_and_Repair_Prompt_Templates.txt` L128 · PD-02 (3) · fixtures: M54

Old:

```text
for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes; `stable_diagnostic_code` is exactly the corresponding `halt_code` token.
```

New:

```text
for `SIMULATOR_ERROR` and the literal `NONE` for the other two halt codes (rule token `stable_error_class_rule` = `simple_exception_class_for_SIMULATOR_ERROR_else_NONE`); `stable_diagnostic_code` is exactly the corresponding `halt_code` token (rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).
```

## E17 — C10 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L185 · PD-01 · fixtures: M41, M42, M47

Old:

```text
(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).
```

New:

```text
(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`). A supplied halt signature with any component outside these domains is an evaluator input error; it is never compared for recurrence.
```

## E18 — A2 (copy of C10) · `25_Common_System_and_Repair_Prompt_Templates.txt` L128 · PD-01 · fixtures: M41, M42, M47

Old:

```text
(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`).
```

New:

```text
(rule token `stable_diagnostic_code_rule` = `exact_halt_code_token`). A supplied halt signature with any component outside these domains is an evaluator input error; it is never compared for recurrence.
```

## E19 — C4 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L176 · PD-03 · fixtures: M14, M17, M41, M48, M50, M53, M54, M58

Old:

```text
compares actual disposition, stage, error class and exact diagnostic bytes with the expected object.
```

New:

```text
compares the actual result with the expected object. When the expected object has exactly the keys `disposition`, `stage_id`, `error_class` and `diagnostic`, those four values are compared exactly. Any other expected object is a control-vector expectation: its whole object is compared exactly, key set included, and every property it names must be defined by a rule in the Protocol.
```

## E20 — C5 · `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L83 · PD-06, PD-25 · fixtures: M27

Old:

```text
(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification.
```

New:

```text
(e) the full vector satisfies the design-specific legal-input predicate from the author-visible reset/legal-input specification. The predicate is frozen as one Python 3.11 function of two dictionaries, `(vector, sampled)`: the driver vector, and the outputs sampled in the same row, each mapping a port name to its bit string. It returns the exact Boolean `True` for a legal vector and `False` otherwise. Any other outcome, including an exception, is an evaluator failure and is never an artifact verdict. Within check (a), missing keys are reported before extra keys. Checks (a) to (e) run in that order and the first failure is reported. A fixture that exercises check (e) supplies the input properties `driver_return` (the vector), `input_port_widths` (each input port name mapped to its width), `sampled_outputs` (the outputs sampled in the same row) and `legal_input_predicate` (an object with `language` = `python3.11`, `function`, the function's name, and `source`, its Python source).
```

## E21 — C6 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L133 · PD-06, PD-25 · fixtures: M27

Old:

```text
| M27 | missing-case | Driver vector violates a design-specific legal-input predicate |
```

New:

```text
| M27 | missing-case | Driver vector passes the key, type, width and symbol checks and violates the supplied legal-input predicate |
```

## E22 — C7 · `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L7 · PD-22 · fixtures: none

Old:

```text
is independent of planning-pack version `1.3.1`.
```

New:

```text
is independent of the planning-pack version.
```

## E23 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L174 · PD-24 · fixtures: none

Old:

```text
**Reported proof of concept.** It evaluates a round-robin arbiter and synchronous FIFO (150–350 LOC), with 12 total test cases. It reports 10/12 tests detecting targeted gaps, zero false positives on the golden design, and an approximately 80-second detection cycle. The paper itself says this sample is too small for strong statistical confidence and treats it as a feasibility demonstration (Section VII-D). It also identifies one LLM model, manual mutation injection, small single-module designs, and UVM-specific scope as limitations (Section VII-E). The preprint is not peer reviewed.
```

New:

```text
**Reported proof of concept (unverified).** An earlier draft attributed a synchronous-FIFO case and numerical results to this preprint. Those details are not verified from its text (abstract-only access, File 22) and are not relied upon. The preprint is not peer reviewed.
```

## E24 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L308 · PD-24 · fixtures: none

Old:

```text
- The TechRxiv preprint reports 10/12 targeted gap detections on two small UVM IPs; it is a proof of concept, not a broad benchmark.
```

New:

```text
- The TechRxiv preprint is an unreviewed proof of concept; its numerical results and designs are not verified from its text (File 22) and are not relied upon.
```

## E25 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L353 · PD-24 · fixtures: none

Old:

```text
the TechRxiv checker-gap preprint also evaluates a synchronous FIFO;
```

New:

```text
whether the TechRxiv checker-gap preprint also evaluates a synchronous FIFO is not verified (File 22);
```

## E26 — C8 · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L383 · PD-24 · fixtures: none

Old:

```text
| Extracted TechRxiv PDF text, including Definitions and experimental limitations (Sections II-A, III, IV–V, VII-D/VII-E); page-image screenshot fetch failed (502) | Moderate for method and declared limitations; checker-dependent definition of output observability; unreviewed preprint, two designs, 12 cases; treat cautiously but disclose as prior art |
```

New:

```text
| Abstract only, per File 22; the earlier statement that extracted full text was read is superseded | Low for method and limitations until the exact PDF is retrieved and inspected; unreviewed preprint; disclose as prior art |
```

## E27 — C8 · `11_Comparative_Research_Matrix.md` L37 · PD-24 · fixtures: none

Old:

```text
- TechRxiv checker-gap paper: full extracted text was read; PDF page images were not inspected; the paper's automated/manual injection descriptions conflict.
```

New:

```text
- TechRxiv checker-gap paper: abstract-only access is recorded (File 22); full-text and injection-method claims are not verified.
```

## E28 — C9 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L27 · PD-04 · fixtures: M36

Old:

```text
Serializer unit vectors and lifecycle unit vectors are marked by `fixture_class` and are deliberately grammar-exempt; they test local utilities/policies, not model feedback.
```

New:

```text
Serializer, lifecycle and parser unit vectors are marked by `fixture_class` (`serializer_primitive_unit_vector_grammar_exempt`, `lifecycle_unit_vector`, `parser_unit_vector`) and are deliberately grammar-exempt; they test local utilities/policies, not model feedback. A `parser_unit_vector` input has exactly the keys `source_file` and `syntax_error`. `source_file` is `driver.py` or `checker.py`. `syntax_error` has the key `lineno`, a positive integer, and may have the key `offset`, an integer or null. The vector applies the Protocol §3.4 `SOURCE_SYNTAX_REJECT` column rule to that position. Its result has stage `SOURCE_AST`, error class `SOURCE_SYNTAX_REJECT`, the diagnostic given by the rule, and disposition `CONTROL_EXPECTATION`.
```

## E29 — C9 · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L15 · PD-04 · fixtures: M36

Old:

```text
- `CONTROL_EXPECTATION`: a serializer, lifecycle or policy test vector;
```

New:

```text
- `CONTROL_EXPECTATION`: a serializer, parser, protocol or lifecycle test vector;
```

## E30 — C9 · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L177 · PD-04 · fixtures: M36

Old:

```text
exercises a serializer, protocol or lifecycle rule;
```

New:

```text
exercises a serializer, parser, protocol or lifecycle rule;
```

## E31 — A2 (copy of C9) · `25_Common_System_and_Repair_Prompt_Templates.txt` L120 · PD-04 · fixtures: M36

Old:

```text
exercises a serializer, protocol or lifecycle rule;
```

New:

```text
exercises a serializer, parser, protocol or lifecycle rule;
```

## E32 — C10 · `41_F18_Fixture_Inputs/M41.json` L33 · PD-01 · fixtures: M41

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E33 — C10 · `41_F18_Fixture_Inputs/M42.json` L16 · PD-01 · fixtures: M42

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E34 — C10 · `41_F18_Fixture_Inputs/M42.json` L23 · PD-01 · fixtures: M42

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E35 — C10 · `41_F18_Fixture_Inputs/M47.json` L16 · PD-01 · fixtures: M47

Old:

```text
"evaluator_component": "simulator",
```

New:

```text
"evaluator_component": "SIMULATOR",
```

## E36 — C10 · `41_F18_Fixture_Inputs/M47.json` L23 · PD-01 · fixtures: M47

Old:

```text
"evaluator_component": "recorder",
```

New:

```text
"evaluator_component": "RECORDER",
```

## E37 — C10 · `41_F18_Fixture_Inputs/M47.json` L24 · PD-01 · fixtures: M47

Old:

```text
"stable_error_class": "RecorderFault",
```

New:

```text
"stable_error_class": "NONE",
```

## E38 — S · `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` L1 · — · fixtures: —

Old:

```text
# OpenVEF Project Charter v1.3.6
```

New:

```text
# OpenVEF Project Charter v1.3.7-candidate
```

## E39 — S · `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` L4 · — · fixtures: —

Old:

```text
**Version:** 1.3.6 (
```

New:

```text
**Version:** 1.3.7-candidate (OpenVEF Planning v1.3.6 with the corrections in `CHANGELOG-v1.3.7-candidate.md`; not audited; not frozen; not approved). Based on: 1.3.6 (
```

## E40 — S · `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` L9 · — · fixtures: —

Old:

```text
independent v1.3.6 document re-audit is pending.
```

New:

```text
independent v1.3.6 document re-audit is pending. The v1.3.7-candidate pack is not audited.
```

## E41 — S · `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` L184 · — · fixtures: —

Old:

```text
`02_OpenVEF_Experimental_Protocol_v1.3.6.md`
```

New:

```text
`02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md`
```

## E42 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L1 · — · fixtures: —

Old:

```text
# OpenVEF Experimental Protocol v1.3.6
```

New:

```text
# OpenVEF Experimental Protocol v1.3.7-candidate
```

## E43 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L4 · — · fixtures: —

Old:

```text
**Version:** 1.3.6 (
```

New:

```text
**Version:** 1.3.7-candidate (OpenVEF Planning v1.3.6 with the corrections in `CHANGELOG-v1.3.7-candidate.md`; not audited; not frozen; not approved). Based on: 1.3.6 (
```

## E44 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L9 · — · fixtures: —

Old:

```text
current v1.3.6 re-audit-pending status are recorded in §19.
```

New:

```text
v1.3.6 re-audit-pending status, and the not-audited v1.3.7-candidate status, are recorded in §19.
```

## E45 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L81 · — · fixtures: —

Old:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.6.md`
```

New:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md`
```

## E46 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L81 · — · fixtures: —

Old:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md`
```

New:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md`
```

## E47 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L83 · — · fixtures: —

Old:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md`
```

New:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md`
```

## E48 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L187 · — · fixtures: —

Old:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md`
```

New:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md`
```

## E49 — A2 (copy of S) · `25_Common_System_and_Repair_Prompt_Templates.txt` L130 · — · fixtures: —

Old:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md`
```

New:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md`
```

## E50 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L288 · — · fixtures: —

Old:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.6.md`
```

New:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md`
```

## E51 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L555 · — · fixtures: —

Old:

```text
(1) Complete the v1.3.6 corrective document pack
```

New:

```text
(1) Complete the v1.3.7-candidate document pack
```

## E52 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L555 · — · fixtures: —

Old:

```text
(2) Obtain an independent document-only v1.3.6 re-audit
```

New:

```text
(2) Obtain an independent document-only v1.3.7-candidate audit
```

## E53 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L559 · — · fixtures: —

Old:

```text
v1.3.6 is a corrective evidence/metadata release
```

New:

```text
v1.3.7-candidate is OpenVEF Planning v1.3.6 with the corrections in `CHANGELOG-v1.3.7-candidate.md`; it is not audited, frozen or approved, and v1.3.6 remains the default pack. v1.3.6 is a corrective evidence/metadata release
```

## E54 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L1 · — · fixtures: —

Old:

```text
Checklist (F18) v1.3.6
```

New:

```text
Checklist (F18) v1.3.7-candidate
```

## E55 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L3 · — · fixtures: —

Old:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.6.md`
```

New:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md`
```

## E56 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L3 · — · fixtures: —

Old:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md`
```

New:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md`
```

## E57 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L3 · — · fixtures: —

Old:

```text
`33_Prompt_Assembly_Sidecar_v1.3.6.json`
```

New:

```text
`33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json`
```

## E58 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L3 · — · fixtures: —

Old:

```text
`38_Authoring_Packet_Manifest_Template_v1.3.6.json`
```

New:

```text
`38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json`
```

## E59 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L3 · — · fixtures: —

Old:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md`
```

New:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md`
```

## E60 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L63 · — · fixtures: —

Old:

```text
Protocol §3.4 and Catalog v1.3.6;
```

New:

```text
Protocol §3.4 and Catalog v1.3.7-candidate;
```

## E61 — S · `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L1 · — · fixtures: —

Old:

```text
# OpenVEF Response Parser and Execution Contract v1.3.6
```

New:

```text
# OpenVEF Response Parser and Execution Contract v1.3.7-candidate
```

## E62 — S · `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L109 · — · fixtures: —

Old:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md`
```

New:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md`
```

## E63 — S · `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` L1 · — · fixtures: —

Old:

```text
Canonicalization Specification v1.3.6
```

New:

```text
Canonicalization Specification v1.3.7-candidate
```

## E64 — S · `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` L17 · — · fixtures: —

Old:

```text
`33_Prompt_Assembly_Sidecar_v1.3.6.json`
```

New:

```text
`33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json`
```

## E65 — S · `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` L84 · — · fixtures: —

Old:

```text
after all v1.3.6 document and model-visible text edits are complete. This v1.3.6 release
```

New:

```text
after all v1.3.7-candidate document and model-visible text edits are complete. This v1.3.7-candidate release
```

## E66 — S · `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` L84 · — · fixtures: —

Old:

```text
retain their exact values in the v1.3.6 sidecar
```

New:

```text
retain their exact values in the v1.3.7-candidate sidecar
```

## E67 — S · `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` L1 · — · fixtures: —

Old:

```text
# OpenVEF v1.3.6 Status and Gates
```

New:

```text
# OpenVEF v1.3.7-candidate Status and Gates
```

## E68 — S · `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` L3 · — · fixtures: —

Old:

```text
**Current release:** v1.3.6 corrective evidence/metadata pack.
```

New:

```text
**Current release:** v1.3.7-candidate (the v1.3.6 corrective evidence/metadata pack with the corrections in `CHANGELOG-v1.3.7-candidate.md`; not audited, not frozen, not approved; v1.3.6 remains the default).
```

## E69 — S · `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` L5 · — · fixtures: —

Old:

```text
**Current document audit status:** PENDING INDEPENDENT RE-AUDIT.
```

New:

```text
**Current document audit status:** v1.3.7-candidate NOT AUDITED; v1.3.6 PENDING INDEPENDENT RE-AUDIT.
```

## E70 — S · `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` L48 · — · fixtures: —

Old:

```text
1. Independent document-only audit of the actual v1.3.6 pack.
```

New:

```text
1. Independent document-only audit of the actual v1.3.7-candidate pack.
```

## E71 — S · `33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json` (was `33_Prompt_Assembly_Sidecar_v1.3.6.json` L2 · — · fixtures: —

Old:

```text
"sidecar_version": "1.3.6",
```

New:

```text
"sidecar_version": "1.3.7-candidate, not audited",
```

## E72 — S · `33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json` (was `33_Prompt_Assembly_Sidecar_v1.3.6.json` L189 · — · fixtures: —

Old:

```text
"payload_manifest_file": "38_Authoring_Packet_Manifest_Template_v1.3.6.json",
```

New:

```text
"payload_manifest_file": "38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json",
```

## E73 — S · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L1 · — · fixtures: —

Old:

```text
Missing-Case Fixture Catalog v1.3.6
```

New:

```text
Missing-Case Fixture Catalog v1.3.7-candidate
```

## E74 — S · `38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json` (was `38_Authoring_Packet_Manifest_Template_v1.3.6.json` L71 · — · fixtures: —

Old:

```text
"Planning-pack v1.3.6 corrective evidence/metadata release.
```

New:

```text
"Planning-pack v1.3.7-candidate (v1.3.6 corrective evidence/metadata release with the corrections in CHANGELOG-v1.3.7-candidate.md; not audited).
```

## E75 — S · `README.md` L1 · — · fixtures: —

Old:

```text
# OpenVEF Planning Pack v1.3.6
```

New:

```text
# OpenVEF Planning Pack v1.3.7-candidate
```

## E76 — S · `README.md` L3 · — · fixtures: —

Old:

```text
**Status:** Corrective evidence/metadata release
```

New:

```text
**Status:** v1.3.7 CANDIDATE, not audited: OpenVEF Planning v1.3.6 with the corrections in `CHANGELOG-v1.3.7-candidate.md` (`CANDIDATE-LABEL.md` lists every file); v1.3.6 remains the default. v1.3.6 status: Corrective evidence/metadata release
```

## E77 — S · `README.md` L7 · — · fixtures: —

Old:

```text
`01_OpenVEF_Project_Charter_v1.3.6.md`
```

New:

```text
`01_OpenVEF_Project_Charter_v1.3.7-candidate.md`
```

## E78 — S · `README.md` L8 · — · fixtures: —

Old:

```text
`02_OpenVEF_Experimental_Protocol_v1.3.6.md`
```

New:

```text
`02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md`
```

## E79 — S · `README.md` L11 · — · fixtures: —

Old:

```text
`21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md`
```

New:

```text
`21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md`
```

## E80 — S · `README.md` L13 · — · fixtures: —

Old:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.6.md`
```

New:

```text
`30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md`
```

## E81 — S · `README.md` L14 · — · fixtures: —

Old:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md`
```

New:

```text
`31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md`
```

## E82 — S · `README.md` L14 · — · fixtures: —

Old:

```text
`33_Prompt_Assembly_Sidecar_v1.3.6.json`
```

New:

```text
`33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json`
```

## E83 — S · `README.md` L16 · — · fixtures: —

Old:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md`
```

New:

```text
`36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md`
```

## E84 — S · `README.md` L17 · — · fixtures: —

Old:

```text
`38_Authoring_Packet_Manifest_Template_v1.3.6.json`
```

New:

```text
`38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json`
```

## E85 — S · `README.md` L9 · — · fixtures: —

Old:

```text
— current release changes and audit lineage.
```

New:

```text
— v1.3.6 release changes and audit lineage; the candidate's changes are in `CHANGELOG-v1.3.7-candidate.md`.
```

## E86 — S · `README.md` L46 · — · fixtures: —

Old:

```text
The current v1.3.6 independent document audit is pending.
```

New:

```text
The v1.3.6 independent document audit is pending; the v1.3.7-candidate pack is not audited.
```

## E87 — label · `41_F18_Fixture_Inputs/M41.json` L3 · — · fixtures: M41

Old:

```text
"fixture_version": "1.2",
```

New:

```text
"fixture_version": "1.3.7-candidate, not audited",
```

## E88 — label · `41_F18_Fixture_Inputs/M42.json` L3 · — · fixtures: M42

Old:

```text
"fixture_version": "1.2",
```

New:

```text
"fixture_version": "1.3.7-candidate, not audited",
```

## E89 — label · `41_F18_Fixture_Inputs/M47.json` L3 · — · fixtures: M47

Old:

```text
"fixture_version": "1.2",
```

New:

```text
"fixture_version": "1.3.7-candidate, not audited",
```

## E90 — label · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` L560 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E91 — label · `25_Common_System_and_Repair_Prompt_Templates.txt` L132 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E92 — label · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` L190 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E93 — label · `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` L110 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E94 — label · `10_LLM_Era_Hardware_Verification_Literature_Review.md` L418 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E95 — label · `11_Comparative_Research_Matrix.md` L44 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E96 — label · `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` L195 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E97 — label · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` L73 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E98 — label · `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` L98 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E99 — label · `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` L55 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E100 — label · `README.md` L49 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E101 — S · `22_Source_Access_Provenance_Log_v1.2.md` L8 · — · fixtures: —

Old:

```text
Literature review record: SHA-256 a79a4d68e445827be7d0c0f176aa3881f40e230814deb93481f109e50aeca11a
```

New:

```text
Literature review record: SHA-256 0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974
```

## E102 — S · `22_Source_Access_Provenance_Log_v1.2.md` L9 · — · fixtures: —

Old:

```text
Literature review record: SHA-256 a79a4d68e445827be7d0c0f176aa3881f40e230814deb93481f109e50aeca11a
```

New:

```text
Literature review record: SHA-256 0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974
```

## E103 — S · `22_Source_Access_Provenance_Log_v1.2.md` L10 · — · fixtures: —

Old:

```text
Literature review record: SHA-256 a79a4d68e445827be7d0c0f176aa3881f40e230814deb93481f109e50aeca11a
```

New:

```text
Literature review record: SHA-256 0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974
```

## E104 — S · `22_Source_Access_Provenance_Log_v1.2.md` L11 · — · fixtures: —

Old:

```text
Literature review record: SHA-256 a79a4d68e445827be7d0c0f176aa3881f40e230814deb93481f109e50aeca11a
```

New:

```text
Literature review record: SHA-256 0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974
```

## E105 — S · `22_Source_Access_Provenance_Log_v1.2.md` L12 · — · fixtures: —

Old:

```text
Literature review record: SHA-256 a79a4d68e445827be7d0c0f176aa3881f40e230814deb93481f109e50aeca11a
```

New:

```text
Literature review record: SHA-256 0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974
```

## E106 — label · `22_Source_Access_Provenance_Log_v1.2.md` L47 · — · fixtures: —

Old:

```text
(end of file)
```

New:

```text
appended trailer: ---

**v1.3.7 CANDIDATE, not audited.** This file is OpenVEF Planning v1.3.6 with only the corrections listed for it in `CHANGELOG-v1.3.7-candidate.md` (owner decision D-024). It is not part of any released, audited or approved pack; v1.3.6 remains the default.
```

## E107 — C6 + A1 · `41_F18_Fixture_Inputs/M27.json` Lall · PD-06, PD-25 · fixtures: M27

Old:

```text
{
  "fixture_id": "M27",
  "fixture_version": "1.0",
  "scope": "missing-case",
  "description": "Driver vector violates a design-specific legal-input predicate",
  "manifest_clause_ids": [
    "FIFO-001"
  ],
  "input": {
    "driver_return": {
      "wr_en": "1",
      "full": "1"
    },
    "legal_input_predicate": "wr_en must be 0 when full is 1"
  },
  "expected": {
    "disposition": "REPAIR",
    "stage_id": "DRIVER_VECTOR",
    "error_class": "DRIVER_VECTOR_INVALID",
    "diagnostic": "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE"
  }
}
```

New:

```text
{
  "fixture_id": "M27",
  "fixture_version": "1.3.7-candidate, not audited",
  "scope": "missing-case",
  "description": "Driver vector passes the key, type, width and symbol checks and violates the supplied legal-input predicate",
  "manifest_clause_ids": [
    "FIFO-001"
  ],
  "input": {
    "driver_return": {
      "wr_en": "1"
    },
    "input_port_widths": {
      "wr_en": 1
    },
    "sampled_outputs": {
      "full": "1"
    },
    "legal_input_predicate": {
      "language": "python3.11",
      "function": "legal_input",
      "source": "def legal_input(vector, sampled):\n    return not (sampled[\"full\"] == \"1\" and vector[\"wr_en\"] == \"1\")\n"
    }
  },
  "expected": {
    "disposition": "REPAIR",
    "stage_id": "DRIVER_VECTOR",
    "error_class": "DRIVER_VECTOR_INVALID",
    "diagnostic": "DRIVER_VECTOR_INVALID|reason=ILLEGAL_PROTOCOL_STATE"
  }
}
```

## E108 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L380 · — · fixtures: M27

Old:

```text
"sha256": "fb7cd4179e9f103a1dc6f158839cd242b054f5d1e8fcf7e3c2a046c8c145e529",
```

New:

```text
"sha256": "63301375a75752d1e76e93c5fb3a934e8f9359a41441f853c270fe60bbf38813",
```

## E109 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L381 · — · fixtures: M27

Old:

```text
"bytes": 558,
```

New:

```text
"bytes": 880,
```

## E110 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L562 · — · fixtures: M41

Old:

```text
"sha256": "56ba49bdedf6eda6f72d0231a1a2861112ff8691ef3a453725341449aab11863",
```

New:

```text
"sha256": "c2e42af7bf912c214f974d5ec371a0fe6845ee8f356d729226edf2db097723b7",
```

## E111 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L563 · — · fixtures: M41

Old:

```text
"bytes": 1626,
```

New:

```text
"bytes": 1651,
```

## E112 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L579 · — · fixtures: M42

Old:

```text
"sha256": "f76023e38e25f9b04059aa7e8d1a8360229c1ea840fb19c68484e5bae7fcfc01",
```

New:

```text
"sha256": "c86181f5e754d50a891def2cae82e194711a098e42419437c0d1985745d15d03",
```

## E113 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L580 · — · fixtures: M42

Old:

```text
"bytes": 1079,
```

New:

```text
"bytes": 1104,
```

## E114 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L644 · — · fixtures: M47

Old:

```text
"sha256": "c9868971e3f2c334ce6d08c925b1319a1c4e8a9ef5b2d7620799c09fe1b27797",
```

New:

```text
"sha256": "4958c30a5d0fd2baa1b032a4104e20268a832e265a7107409a8772b9d9d7515f",
```

## E115 — derived · `41_F18_Fixture_Inputs/fixture-index.json` L645 · — · fixtures: M47

Old:

```text
"bytes": 1119,
```

New:

```text
"bytes": 1135,
```

## E116 — label · `41_F18_Fixture_Inputs/fixture-index.json` L2 · — · fixtures: —

Old:

```text
"fixture_index_version": "1.3.6",
```

New:

```text
"fixture_index_version": "1.3.7-candidate, not audited",
```

## E117 — S · `01_OpenVEF_Project_Charter_v1.3.7-candidate.md` (was `01_OpenVEF_Project_Charter_v1.3.6.md` Lname · — · fixtures: —

Old:

```text
01_OpenVEF_Project_Charter_v1.3.6.md
```

New:

```text
01_OpenVEF_Project_Charter_v1.3.7-candidate.md
```

## E118 — S · `02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md` (was `02_OpenVEF_Experimental_Protocol_v1.3.6.md` Lname · — · fixtures: —

Old:

```text
02_OpenVEF_Experimental_Protocol_v1.3.6.md
```

New:

```text
02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md
```

## E119 — S · `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md` (was `21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md` Lname · — · fixtures: —

Old:

```text
21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md
```

New:

```text
21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md
```

## E120 — S · `30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md` (was `30_Response_Parser_and_Execution_Contract_v1.3.6.md` Lname · — · fixtures: —

Old:

```text
30_Response_Parser_and_Execution_Contract_v1.3.6.md
```

New:

```text
30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md
```

## E121 — S · `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md` (was `31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md` Lname · — · fixtures: —

Old:

```text
31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md
```

New:

```text
31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md
```

## E122 — S · `32_v1.3.7-candidate_Status_and_Gates.md` (was `32_v1.3.6_Status_and_Gates.md` Lname · — · fixtures: —

Old:

```text
32_v1.3.6_Status_and_Gates.md
```

New:

```text
32_v1.3.7-candidate_Status_and_Gates.md
```

## E123 — S · `33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json` (was `33_Prompt_Assembly_Sidecar_v1.3.6.json` Lname · — · fixtures: —

Old:

```text
33_Prompt_Assembly_Sidecar_v1.3.6.json
```

New:

```text
33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json
```

## E124 — S · `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md` (was `36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md` Lname · — · fixtures: —

Old:

```text
36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md
```

New:

```text
36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md
```

## E125 — S · `38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json` (was `38_Authoring_Packet_Manifest_Template_v1.3.6.json` Lname · — · fixtures: —

Old:

```text
38_Authoring_Packet_Manifest_Template_v1.3.6.json
```

New:

```text
38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json
```

## E126 — derived · `27_SHA256SUMS.txt` L1 · — · fixtures: —

Old:

```text
af3bd1c72683c2e9bb56a38a3cc85d228bec53e8fc786f81c4593cdfd3d9412b  01_OpenVEF_Project_Charter_v1.3.6.md
```

New:

```text
a314a1cd9932208fc2df21dd1754e6c065f047b5c6989aa9cefd654ac20d6c02  01_OpenVEF_Project_Charter_v1.3.7-candidate.md
```

## E127 — derived · `27_SHA256SUMS.txt` L2 · — · fixtures: —

Old:

```text
1a3015ea38f96ab97e813076476d34f3043a40a83825106937ff633d14b61a87  02_OpenVEF_Experimental_Protocol_v1.3.6.md
```

New:

```text
d2cf16062f8ac70ff35dccf897b8e0561b3e7d7375133d846378a13c692d78d6  02_OpenVEF_Experimental_Protocol_v1.3.7-candidate.md
```

## E128 — derived · `27_SHA256SUMS.txt` L11 · — · fixtures: —

Old:

```text
a79a4d68e445827be7d0c0f176aa3881f40e230814deb93481f109e50aeca11a  10_LLM_Era_Hardware_Verification_Literature_Review.md
```

New:

```text
0e6bd491549561d4cdf9af9c16b84980f39e3bb029dcca93477a874e4d33d974  10_LLM_Era_Hardware_Verification_Literature_Review.md
```

## E129 — derived · `27_SHA256SUMS.txt` L12 · — · fixtures: —

Old:

```text
014094c32d8c521ab0e865a358207ca09959b018978f67492a35626f9ff89fbe  11_Comparative_Research_Matrix.md
```

New:

```text
3e40cc28eacce8289660ee8a2c5239fb66e91e20abf7409a99dd5bcb0e07d8a3  11_Comparative_Research_Matrix.md
```

## E130 — derived · `27_SHA256SUMS.txt` L20 · — · fixtures: —

Old:

```text
a84a89837e3158c294a351adc1f90c6aa583e462733622027ea1ac9feaeb40b1  21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.6.md
```

New:

```text
9137d37777bea8981a8e5ed71a4fe5b3eed0d70156ef1d8b0423a9f09ce8e585  21_Prompt_Equivalence_and_Mask_Traceability_Checklist_v1.3.7-candidate.md
```

## E131 — derived · `27_SHA256SUMS.txt` L21 · — · fixtures: —

Old:

```text
c19d937d1849ec3b8a4529c54822674da433e26094b0ed4c407538f2dace0dac  22_Source_Access_Provenance_Log_v1.2.md
```

New:

```text
3705bfda6bee79e0e4f3f85848eefd32b0f46d09dd9b947e6b788c2441635ef9  22_Source_Access_Provenance_Log_v1.2.md
```

## E132 — derived · `27_SHA256SUMS.txt` L24 · — · fixtures: —

Old:

```text
987378853f21b108704b5d97e10a1832de7fcdeca7ed7aae65b26a5e0e04bc49  25_Common_System_and_Repair_Prompt_Templates.txt
```

New:

```text
48580bebd90917c85dc232ac7db80190ccfac490227550545ffc04d294aa5246  25_Common_System_and_Repair_Prompt_Templates.txt
```

## E133 — derived · `27_SHA256SUMS.txt` L28 · — · fixtures: —

Old:

```text
b0b43989beb81be986caed48562c6832ca981449f82fd14f6ae8bdceed5b2ba6  30_Response_Parser_and_Execution_Contract_v1.3.6.md
```

New:

```text
2c8b986528d55f1f1dedceb53d0b55f4f9eb071f04fb489cf68874d9eda9ef28  30_Response_Parser_and_Execution_Contract_v1.3.7-candidate.md
```

## E134 — derived · `27_SHA256SUMS.txt` L29 · — · fixtures: —

Old:

```text
aa963c39eedf087c1b7f4b5d4df0545a69451e6d78e94256f45c70bc54f91e72  31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.6.md
```

New:

```text
6af215535a5dc703b62aad64fe360fffabbfc415f7c94b4d6b6139b161c64bcc  31_Prompt_Assembly_and_Canonicalization_Spec_v1.3.7-candidate.md
```

## E135 — derived · `27_SHA256SUMS.txt` L30 · — · fixtures: —

Old:

```text
614046f17efb4609ddee10830b781fb0fecb3dbe9fb7bd681e0bdd043b3c6e66  32_v1.3.6_Status_and_Gates.md
```

New:

```text
55ab8053440071fd1835255943d693a0cb0cc213c9cb2776a569c8172e2c1428  32_v1.3.7-candidate_Status_and_Gates.md
```

## E136 — derived · `27_SHA256SUMS.txt` L31 · — · fixtures: —

Old:

```text
b2585edb095d29a7decd94f509f45c3a481d8d3747db1bcbcf0a908605219902  33_Prompt_Assembly_Sidecar_v1.3.6.json
```

New:

```text
a948bd1ef3f05223af0f741087b6e29795ffcb27f87428f84a13bb245f9e6792  33_Prompt_Assembly_Sidecar_v1.3.7-candidate.json
```

## E137 — derived · `27_SHA256SUMS.txt` L34 · — · fixtures: —

Old:

```text
270ccbd73691e6e32fbec8817e7c235d50ba3a803796270f236006e938f4983e  36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.6.md
```

New:

```text
9f6c428a655030bd5f47330020c8d2fa551341c960730e5883e3cf2ac115770d  36_F18_Parser_and_Repair_Fixture_Catalog_v1.3.7-candidate.md
```

## E138 — derived · `27_SHA256SUMS.txt` L36 · — · fixtures: —

Old:

```text
55dc7f4f9e9ca3424a73831cae2f1e90a280173e8e463698f1989bd3d47ee8e6  38_Authoring_Packet_Manifest_Template_v1.3.6.json
```

New:

```text
d841b87ee410ad462521aaa76f27cae1c2f5a7923aff6d51b4fb0a61fc7e8819  38_Authoring_Packet_Manifest_Template_v1.3.7-candidate.json
```

## E139 — derived · `27_SHA256SUMS.txt` L66 · — · fixtures: —

Old:

```text
fb7cd4179e9f103a1dc6f158839cd242b054f5d1e8fcf7e3c2a046c8c145e529  41_F18_Fixture_Inputs/M27.json
```

New:

```text
63301375a75752d1e76e93c5fb3a934e8f9359a41441f853c270fe60bbf38813  41_F18_Fixture_Inputs/M27.json
```

## E140 — derived · `27_SHA256SUMS.txt` L80 · — · fixtures: —

Old:

```text
56ba49bdedf6eda6f72d0231a1a2861112ff8691ef3a453725341449aab11863  41_F18_Fixture_Inputs/M41.json
```

New:

```text
c2e42af7bf912c214f974d5ec371a0fe6845ee8f356d729226edf2db097723b7  41_F18_Fixture_Inputs/M41.json
```

## E141 — derived · `27_SHA256SUMS.txt` L81 · — · fixtures: —

Old:

```text
f76023e38e25f9b04059aa7e8d1a8360229c1ea840fb19c68484e5bae7fcfc01  41_F18_Fixture_Inputs/M42.json
```

New:

```text
c86181f5e754d50a891def2cae82e194711a098e42419437c0d1985745d15d03  41_F18_Fixture_Inputs/M42.json
```

## E142 — derived · `27_SHA256SUMS.txt` L86 · — · fixtures: —

Old:

```text
c9868971e3f2c334ce6d08c925b1319a1c4e8a9ef5b2d7620799c09fe1b27797  41_F18_Fixture_Inputs/M47.json
```

New:

```text
4958c30a5d0fd2baa1b032a4104e20268a832e265a7107409a8772b9d9d7515f  41_F18_Fixture_Inputs/M47.json
```

## E143 — derived · `27_SHA256SUMS.txt` L182 · — · fixtures: —

Old:

```text
f37808c7a662b8fdf164e27feaef023aadd6dfefaada35d11c3719185d1bde54  41_F18_Fixture_Inputs/fixture-index.json
```

New:

```text
3ffd4883fed3c33f00915b898a29d2f28db9d0a3b73a5bfd380a668ed7795278  41_F18_Fixture_Inputs/fixture-index.json
```

## E144 — derived · `27_SHA256SUMS.txt` L202 · — · fixtures: —

Old:

```text
cd222521cb455c1eb12241a05a8f31bda908bd6b5a00efcd22ca4029c9feeca5  README.md
```

New:

```text
e80f8a9f4d1ab312e24901b0fffbe4b21aab3b979ffbbfbf10d5fa880565fca3  README.md
```
