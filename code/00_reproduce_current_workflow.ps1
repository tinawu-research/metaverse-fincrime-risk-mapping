# Free/local reproduction workflow for the Round 5 metaverse-crypto financial crime analysis.
# Run from this code directory in PowerShell after Docker/Ollama is running and qwen2.5:7b is available.
# The first script creates a new timestamped output directory from the source corpus.
# Scripts 02-05 are the exact scripts used for the current completed output folder.

python .\01_local_qwen_metaverse_fincrime_analysis.py
python .\02_write_enhanced_metaverse_fincrime_report.py
python .\03_markdown_to_docx_simple.py
python .\04_write_topic_model_intervention_focus.py
python .\05_build_free_graph_pack.py
