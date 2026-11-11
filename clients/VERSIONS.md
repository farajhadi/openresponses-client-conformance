# Client libraries and versions (recorded 2026-11-10, before scoring)

Each Python library is installed alone in its own environment under envs/<name> with uv (Python 3.12, except openresponses-client which needs 3.14), so dependency pins can't interfere. Versions are what pip resolved. Scoring was run on Debian GNU/Linux 13 (trixie).

| Library | Version | Adapter |
|---|---|---|
| openai | 3.48.0 | `clients/py/openai_sdk.py` |
| openresponses-client | 0.0.2 | `clients/py/openresponses_client_lib.py` |
| openresponses-python | 0.1.4 | `clients/py/openresponses_python.py` |
| litellm | 1.108.4 (openai 3.48.0) | `clients/py/litellm_lib.py` |
| langchain-openai | 1.7.4 (openai 3.48.0) | `clients/py/langchain_openai_lib.py` |
| openai-agents | 0.24.0 (openai 3.48.0) | `clients/py/openai_agents_lib.py` |
| llama-index-llms-openai | 0.8.3 (openai 2.54.0) | `clients/py/llama_index_lib.py` |
| pydantic-ai-slim | 2.66.0 (openai 3.48.0) | `clients/py/pydantic_ai_lib.py` |
| any-llm-sdk | 1.48.0 (openai 3.48.0) | `clients/py/any_llm_lib.py` |

JavaScript (planned next, installed in clients/js): see clients/js/package-lock.json.
