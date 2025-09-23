from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

counter = 1
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# for completion
@app.post("/chat/completions")
@app.post("/v1/chat/completions")
async def completion(request: Request):
    # raise HTTPException(status_code=429, detail="Rate Limited!")
    global counter
    print(f"Request: {counter}")
    counter += 1
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": None,
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [{
            "index": 0,
            "message": {
            "role": "assistant",
            "content": "\n\nHello there, how may I assist you today?",
            },
            "logprobs": None,
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = 8002
    uvicorn.run(app, host="127.0.0.1", port=port)