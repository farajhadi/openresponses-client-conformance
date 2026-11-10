#!/usr/bin/env bash
# Starts the fake server, runs every repro with its library's own venv, writes repro/OUTPUT.txt.
cd "$(dirname "$0")/.." || exit 1
python3 server/fake_server.py --port 8766 --log logs/repro_server.log > /dev/null &
SRV=$!; sleep 1
{
for pair in "openresponses-python openresponses_python_done" "openresponses-python openresponses_python_multiline" \
            "llama-index llama_index_failed" "pydantic-ai pydantic_ai_incomplete" "openai openai_python" \
            "openai-agents openai_agents_incomplete"; do
  set -- $pair
  echo "== repro/$2.py (envs/$1)"
  timeout 120 "envs/$1/bin/python" "repro/$2.py" 8766 2>&1 | grep -v Warning
  echo
done
} > repro/OUTPUT.txt
kill $SRV
