# Letterly — AI Email Writer

A Streamlit app that helps turn a few notes into a polished email, draft a reply to a pasted message, or improve existing writing. Choose Professional, Friendly, Formal, or Apologetic tone. Draft fields remain editable so you can review and copy the result. Text generation runs locally through Ollama.

## Run locally

1. Install Python 3.10 or later and [Ollama](https://ollama.com/download).
2. Start Ollama and download a model, for example:

   ```bash
   ollama pull smollm2:1.7b-instruct-q4_0
   ```

3. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`. Change `OLLAMA_MODEL` if you downloaded a different model. The default Ollama address is `http://localhost:11434`.
5. Start the app:

   ```bash
   streamlit run app.py
   ```

The app sends prompts to Ollama's local chat API at `/api/chat`. Configure `OLLAMA_BASE_URL` and `OLLAMA_MODEL` in `.env` to use a different local Ollama server or model. No Gemini API key is needed.
