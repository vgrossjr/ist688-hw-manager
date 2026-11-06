# IST688 Project Instructions for Claude Code

Follow these rules whenever you work in this project.

- Use `uv` for Python and dependency management.
- Do **not** use `pip`, `venv`, `conda`, `pipenv`, `poetry`, Anaconda, or another Python environment tool.
- Do **not** tell the student to install Python or Streamlit directly. `uv` handles both.
- Run the app with:

  ```
  uv run streamlit run app.py --server.port 8501 --server.headless true
  ```

- Keep `pyproject.toml` and `requirements.txt` in sync. If you add, remove, or change a dependency in one, make the matching change in the other.
- Do **not** delete `requirements.txt`.
- Keep secrets out of source code and Git. Store local secrets in `.streamlit/secrets.toml`, and make sure that file is ignored by Git.
- Before changing the project's setup, dependencies, Git workflow, or deployment approach, read `README.md` and follow it.
- Use the tools required by the course: Claude Desktop Code, `uv`, Git, GitHub, and Streamlit Community Cloud. Do not substitute other development tools or deployment platforms unless the instructor explicitly asks.
