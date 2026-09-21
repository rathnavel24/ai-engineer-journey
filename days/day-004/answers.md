## Karpathy - "Intro to Large Language Models" (10 notes, in my own words)

1. An LLM is really just two files: a parameters file (the trained weights, ~140GB for Llama 2 70B) and a small run file (~500 lines of C) to execute them - no internet connection needed once you have both.

2. Training is the expensive part: thousands of GPUs chew through terabytes of internet text for days-to-weeks at multi-million-dollar cost. Inference (actually running the model) is comparatively cheap.

3. Training is essentially lossy compression of the internet - roughly 10TB of text gets compressed into a much smaller parameter file, so the model absorbs patterns rather than storing a literal copy.

4. Because it's compression, not memorization, the model can produce fluent, confident text that's flat-out wrong - hallucination - since it's predicting plausible next tokens, not looking facts up.

5. Getting a useful assistant is a two-stage process: pretraining on raw internet text builds a "base model" that just completes text, then fine-tuning on curated Q&A-style conversations turns it into something that behaves like a helpful chatbot (optionally with a further RLHF stage).

6. Performance is fairly predictable via scaling laws - more parameters and more training data reliably produce better models, which is what's driving the race for compute and data.

7. Modern LLMs are being taught to call external tools (search, calculators, code interpreters, image generators) mid-conversation instead of trying to do everything from memory.

8. Karpathy frames today's LLMs as fast, reflexive "System 1" thinking, and expects future progress toward slower, deliberate "System 2" reasoning that trades extra compute time for better accuracy.

9. His big-picture framing: think of an LLM less like a chatbot and more like the kernel of a new operating system, coordinating "memory" (context window), tools, and retrieval as its resources.

10. The talk closes on security: jailbreaks (tricking the model past its safety training), prompt injection (hidden instructions smuggled in via a webpage/image the model reads), and data poisoning (planting malicious trigger phrases in training data) - described as an ongoing cat-and-mouse game, not a solved problem.
