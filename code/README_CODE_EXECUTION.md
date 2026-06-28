# Code Folder

This folder contains the exact scripts used in the free/local Round 5 analysis package.

## Execution order

1. `01_local_qwen_metaverse_fincrime_analysis.py`
2. `02_write_enhanced_metaverse_fincrime_report.py`
3. `03_markdown_to_docx_simple.py`
4. `04_write_topic_model_intervention_focus.py`
5. `05_build_free_graph_pack.py`

The `00_reproduce_current_workflow.ps1` file records this order as a PowerShell workflow. The first script calls local Ollama at `http://localhost:11434/api/generate` using `qwen2.5:7b`; it does not call a paid API. The later scripts operate on the already-created Round 5 output folder.

## Free/local boundary

- Local model: `qwen2.5:7b`
- Runtime: local Ollama/MiroFish environment
- Paid API: not used
- Zep Cloud graph build: not used
- Graph outputs: produced locally from CSV/JSON evidence tables
