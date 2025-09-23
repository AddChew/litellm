from openai import AsyncOpenAI
import random, uuid
import time, asyncio

#### LITELLM PROXY #### 
litellm_client = AsyncOpenAI(
    api_key="my-fake-key", # [CHANGE THIS]
    base_url="http://localhost:3010"
)
litellm_client_2 = AsyncOpenAI(
    api_key="my-fake-key", # [CHANGE THIS]
    base_url="http://localhost:3011"
)

async def proxy_completion_non_streaming():
  try:
    client = random.sample([litellm_client, litellm_client_2], 1)[0] # randomly pick b/w clients # , litellm_client_2
    # print(f"client={client}")
    response = await client.chat.completions.create(
              model="fake-openai-endpoint", # [CHANGE THIS] (if you call it something else on your proxy)
              messages=[{"role": "user", "content": f"This is a test: {uuid.uuid4()}"}],
          )
    return response
  except Exception as e:
    # print(e)
    return None
  
async def loadtest_fn():
    start = time.time()
    n = 30  # Number of concurrent tasks
    tasks = [proxy_completion_non_streaming() for _ in range(n)]
    chat_completions = await asyncio.gather(*tasks)
    successful_completions = [c for c in chat_completions if c is not None]
    print(n, time.time() - start, len(successful_completions))

def get_utc_datetime():
    import datetime as dt
    from datetime import datetime

    if hasattr(dt, "UTC"):
        return datetime.now(dt.UTC)  # type: ignore
    else:
        return datetime.utcnow()  # type: ignore


# Run the event loop to execute the async function
async def parent_fn():
  for _ in range(1):
    dt = get_utc_datetime()
    current_minute = dt.strftime("%H-%M")
    print(f"triggered new batch - {current_minute}")
    await loadtest_fn()
    await asyncio.sleep(10)

asyncio.run(parent_fn())