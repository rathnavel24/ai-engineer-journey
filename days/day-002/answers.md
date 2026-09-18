
1. Why can two providers report similar token counts but charge different amounts?

Token count and price are two separate things.

Two providers can process roughly the same number of input/output tokens but have different price-per-token rates. Pricing can also differ between:

Input tokens vs. output tokens
Different models
Cached vs. uncached input
Different context-window tiers
Different billing units or minimum charges

For example:

Provider A: 1,000 tokens × $1/M tokens
Provider B: 1,000 tokens × $5/M tokens

The token usage is identical, but Provider B costs 5× more.

So when benchmarking, don't assume:

more tokens = more expensive

Instead:

cost = token usage × provider/model pricing rules


2.(ai-engineer-journey) rathnavel@rathnavels-MacBook-Pro ai-engineer-journey % uv run days/day-002/compare_llms.py                             
Direct use of automatic function calling (AFC) in Models.generate_content is not recommended. Instead, we recommend to use AFC in Chat.send_message. Similarly, direct use of AFC in Models.generate_content_stream is not recommended. Instead, we recommend to use AFC in Chat.send_message_stream.
Prompt: "In one sentence, explain what a vector database is."
(each provider called 3x; latency/tokens/cost below are medians)

Provider    Model                                 Latency (s)   In tok   Out tok  Cost ($)    
----------------------------------------------------------------------------------------------
Gemini      gemini-3.6-flash                      4.394         12       37       0.00014775  
OpenRouter  deepseek/deepseek-v4-flash-0731:free  2.385         94       50       0.00000000  
Ollama      llama3.2:3b                           1.688         36       43       0.00000000  

Gemini output: A vector database is a specialized storage system that indexes and retrieves data as high-dimensional numerical representations, enabling AI applications to perform fast, similarity-based searches rather than exact keyword matches.
OpenRouter output: A vector database is a specialized database designed to store, index, and query high-dimensional vector embeddings using similarity search, enabling fast retrieval of related items based on semantic or mathematical proximity.
Ollama output: A vector database is a type of database that stores and manages large collections of vectors, which are mathematical representations of objects or data points, enabling efficient similarity searches, nearest neighbor queries, and other distance-based computations.


3. What happens if max_tokens=4000 for a one-line answer?

max_tokens is generally a maximum generation budget, not a command saying:

"Generate exactly 4,000 tokens."

If the model naturally finishes after 20 tokens, it can stop at 20.

However, setting it unnecessarily high can still be problematic.

Latency:
A larger maximum gives the generation process permission to continue for much longer if the model doesn't terminate early. Longer possible generation means potentially higher latency.

Cost:
Output tokens are commonly billable. If the model actually generates more tokens, you pay for those additional output tokens.

The key distinction is:

max_tokens = maximum allowed output
actual output tokens = what the model actually generates

So max_tokens=4000 does not automatically mean you're charged for 4000 tokens.

And why doesn't it simply stop early?

Actually, it often does.

The model can stop when it reaches a natural completion/end-of-generation condition. But the API's maximum is still there as a safety boundary. If your prompt or generation settings cause the model to continue producing content, the model can keep generating until it reaches that limit.

For a one-line answer, something like:

max_tokens=100

is usually a much more sensible constraint than:

max_tokens=4000



4.Ollama (llama3.2:3b) had the lowest total latency at 1.908 seconds.

The most likely reason is hardware/local execution, not the network. Ollama runs the model directly on your computer, so there is no internet round trip to a remote provider. Gemini and OpenRouter both require network communication, which adds request/response overhead.

However, this benchmark cannot prove that the model itself is inherently faster because you're measuring end-to-end latency. To make the comparison more reliable, run each prompt 3 times and compare the median latency.

Answer: Ollama was fastest (1.908s), mainly because it runs locally on your hardware and avoids network/API overhead.


## Day 1 recall check (no notes)

uv.lock vs pyproject.toml: pyproject.toml states what you want (loose version ranges); uv.lock pins the exact resolved versions of every dependency, direct and transitive, so `uv sync` gives everyone the same environment instead of whatever the resolver picks on a given day.

.env committed then deleted in the next commit: the secrets aren't safe. Git keeps every version of a file in history, so the .env content is still retrievable from the earlier commit even after a later commit removes the file. Fix is rotate the leaked keys first, then scrub the file from history (git filter-repo / BFG) and force-push - deleting it going forward isn't enough.

## Reflection

Cost and latency aren't properties of "the model" in the abstract - they're properties of a specific request against a specific provider, and they only mean something once you've run it more than once.