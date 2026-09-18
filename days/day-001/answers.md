# Day 001

## Answers
1.Explain in your own words: what does uv.lock protect you from that pyproject.toml alone doesn't?

pyproject.toml defines the dependencies your project wants, but it usually allows dependency versions to be resolved differently over time. uv.lock records the exact versions of your dependencies and their transitive dependencies, so everyone gets the same dependency tree. This protects you from unexpected package updates breaking your application. In short, pyproject.toml describes the requirements, while uv.lock makes the environment reproducible.

2.Done!

3.What breaks if: You commit .env and push it, deleting it in the next commit does not make the secrets safe. The .env file 
still exists in Git history and may already have been downloaded, cached, or exposed to others. You should immediately revoke/rotate every secret in that .env, then remove the file from Git history using a tool such as git filter-repo or BFG, force-push the cleaned history, and add .env to .gitignore. Even after rewriting history, treat the old credentials as compromised.

4.By 24 Jan 2027, I want to:

Ship a production-ready AI backend with FastAPI, PostgreSQL, Redis, authentication, background jobs, and Docker, deployed publicly with 99%+ successful API requests during testing.
Build and ship a multi-tenant RAG API that supports document ingestion, retrieval, citations, and tenant isolation, with an automated evaluation suite achieving ≥85% retrieval/answer quality in CI.
Build an AI engineering portfolio containing 3 deployed AI projects, each with tests, documentation, Docker setup, evaluation metrics, and a working API/demo that I can confidently explain in a technical interview.

5.Can I design, build, and deploy a production-ready AI backend independently, rather than just following tutorials?
Can I build a multi-tenant RAG system end-to-end and explain why I chose each component, from ingestion and chunking to retrieval, generation, and evaluation?
Can I reliably evaluate an AI system and use measurable results to identify and improve weaknesses instead of judging quality by intuition?
Can I build AI applications that are secure, scalable, observable, and maintainable enough to be used beyond a local development environment?
Can I confidently explain my AI engineering decisions in a technical interview and demonstrate them through projects I have actually built and deployed?
