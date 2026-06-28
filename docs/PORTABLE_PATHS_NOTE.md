# Portable Paths Note

The copied Qwen/Ollama scripts preserve original Windows/OneDrive paths from the first author's completed run. These paths are useful provenance, but they are not portable and are not expected to exist on reviewer machines.

Before rerunning the scripts, update path constants such as `INPUT_FILE`, `OUT_DIR`, `SOURCE`, and `BASE_DIR` to point at local files. The full extracted text input is intentionally not included in this package. Reviewers who have lawful access to the source PDFs may regenerate extracted text with the LDA notebook or adapt the workflow to their local corpus location.

A portable refactor could use an environment variable such as `ROUND5_DIR` or paths relative to the script location, but this package keeps the original analysis logic unchanged.
