Step 1 — SSH into the server

ssh dantonakaki@bb8.mhl.tuc.gr
Step 2 — Start vLLM (the local AI model)

/home/dantonakaki/.miniconda/envs/laws/bin/python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --port 8001 \
  > /tmp/vllm.log 2>&1 &
Wait ~2 min, then check it loaded:


tail -f /tmp/vllm.log
Look for Application startup complete. → press Ctrl+C to stop watching.

Step 3 — Start the chat UI

cd /home/dantonakaki/greek_legislation/code
/home/dantonakaki/.miniconda/envs/laws/bin/python 35.rag_chat.py --no-share &
Step 4 — SSH tunnel (on your LOCAL machine, new terminal)

ssh -L 7860:localhost:7860 dantonakaki@bb8.mhl.tuc.gr
Keep this terminal open while using the app.

Step 5 — Open browser

http://localhost:7860
Check if already running:


ps aux | grep -E "vllm|rag_chat" | grep -v grep
Kill and restart:


pkill -f "vllm.entrypoints"
pkill -f "rag_chat.py"  