import os
import re
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CACHE_BASE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "rag_hf_cache"
)
os.makedirs(LOCAL_CACHE_BASE, exist_ok=True)
os.environ["HF_HOME"] = LOCAL_CACHE_BASE
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(LOCAL_CACHE_BASE, "hub")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(LOCAL_CACHE_BASE, "transformers")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.join(LOCAL_CACHE_BASE, "sentence_transformers")
import torch
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama

# =========================
# CONFIG
# =========================
MODEL_PATH = os.path.join(BASE_DIR, "CodeMaster.gguf")
EMBED_MODEL = "all-MiniLM-L6-v2"
EMBED_CACHE_DIR = LOCAL_CACHE_BASE

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
FORCE_GPU = os.environ.get("CODEMASTER_FORCE_GPU", "1").strip().lower() in ("1", "true", "yes", "on")
GPU_STRATEGY = os.environ.get("CODEMASTER_GPU_STRATEGY", "hybrid").strip().lower()
GPU_LAYERS_ENV = os.environ.get("CODEMASTER_GPU_LAYERS", "").strip()
N_CTX = int(os.environ.get("CODEMASTER_N_CTX", "2048"))
N_BATCH = int(os.environ.get("CODEMASTER_N_BATCH", "256"))
CPU_THREADS = int(os.environ.get("CODEMASTER_CPU_THREADS", str(max(2, (os.cpu_count() or 8) // 3))))
CPU_THREADS_BATCH = int(os.environ.get("CODEMASTER_CPU_THREADS_BATCH", str(max(1, CPU_THREADS // 2))))
EMBED_DEVICE = os.environ.get("CODEMASTER_EMBED_DEVICE", "cpu").strip().lower()

# =========================
# DEVICE DETECTION
# =========================
def get_device():
    if torch.cuda.is_available():
        print("GPU detected")
        return "cuda"
    if FORCE_GPU:
        raise RuntimeError("GPU is required but CUDA is not available. Install CUDA-enabled PyTorch and GPU-enabled llama-cpp-python.")
    print("Using CPU")
    return "cpu"

DEVICE = get_device()

# =========================
# LOAD LLM (AUTO CPU/GPU)
# =========================
def load_llm():
    if DEVICE != "cuda":
        raise RuntimeError("GPU mode is required but device is not CUDA.")
    if GPU_LAYERS_ENV:
        gpu_layers = int(GPU_LAYERS_ENV)
    elif GPU_STRATEGY == "full":
        gpu_layers = -1
    else:
        gpu_layers = 35
    print(
        f"LLM settings -> strategy={GPU_STRATEGY}, gpu_layers={gpu_layers}, "
        f"n_ctx={N_CTX}, n_batch={N_BATCH}, cpu_threads={CPU_THREADS}, cpu_threads_batch={CPU_THREADS_BATCH}"
    )
    try:
        return Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_gpu_layers=gpu_layers,
            n_batch=N_BATCH,
            n_threads=CPU_THREADS,
            n_threads_batch=CPU_THREADS_BATCH
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize GPU LLM. Ensure llama-cpp-python is built with CUDA. {str(e)}")

llm = load_llm()

# =========================
# EMBEDDING MODEL
# =========================
os.makedirs(EMBED_CACHE_DIR, exist_ok=True)
embed_model = SentenceTransformer(
    EMBED_MODEL,
    device="cuda" if EMBED_DEVICE == "cuda" and DEVICE == "cuda" else "cpu",
    cache_folder=EMBED_CACHE_DIR
)

def split_text(text):
    normalized = " ".join(text.split())
    if not normalized:
        return []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]
    if not sentences:
        sentences = [normalized]

    chunks = []
    current = ""
    for sentence in sentences:
        if len(sentence) > CHUNK_SIZE:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
            while start < len(sentence):
                chunks.append(sentence[start:start + CHUNK_SIZE])
                start += step
            continue

        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)
    return chunks

# =========================
# VECTOR STORE (FAISS)
# =========================
class VectorStore:
    def __init__(self):
        self.index = None
        self.text_chunks = []
        self.metadata = []
        self.embeddings = None

    def build(self, chunks):
        if not chunks:
            raise ValueError("No chunks to index")
        embeddings = embed_model.encode(
            chunks,
            convert_to_numpy=True,
            show_progress_bar=True
        ).astype("float32")
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        self.text_chunks = chunks
        self.embeddings = embeddings
        self.metadata = [
            {"id": i, "text": chunk, "source": "frontend"}
            for i, chunk in enumerate(chunks)
        ]

    def search(self, query, retrieve_k=8, top_k=3):
        if self.index is None:
            raise ValueError("Vector index is not built")
        query_vec = embed_model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(query_vec)

        k = min(retrieve_k, len(self.metadata))
        scores, indices = self.index.search(query_vec, k)
        query_terms = set(re.findall(r"\w+", query.lower()))
        reranked = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            item = self.metadata[int(idx)]
            text = item["text"]
            text_terms = set(re.findall(r"\w+", text.lower()))
            overlap = len(query_terms & text_terms) / max(1, len(query_terms))
            rerank_score = float(score) + 0.15 * overlap
            reranked.append((rerank_score, text))

        reranked.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in reranked[:top_k]]

# =========================
# PROMPT TEMPLATE (OPTIMIZED)
# =========================
def build_prompt(context, question):
    lower_question = question.lower()
    needs_code = any(token in lower_question for token in ["code", "java", "class", "method", "function", "bug", "error", "fix"])
    response_instruction = "If code is required, provide correct Java code first, then explain step-by-step in simple language." if needs_code else "Explain step-by-step in simple language."
    context_policy = (
        "- Use context as primary source\n"
        "- If context is insufficient, generate a correct Java solution using best practices\n"
        "- State assumptions briefly when context is missing"
        if needs_code else
        "- Answer ONLY from context\n"
        "- If missing, say: \"Not found in context\""
    )
    return f"""
You are an expert Java programmer and coding assistant.

Use the given context to answer the question.

Instructions:
{context_policy}
- {response_instruction}
- Mention edge cases if relevant
- Be precise and structured
- Return only one final answer for this question

Context:
{context}

Question:
{question}

Answer:
"""

def is_code_generation_request(question):
    lower_question = question.lower()
    has_action = any(token in lower_question for token in ["generate", "create", "write", "build", "provide", "give"])
    has_target = any(token in lower_question for token in ["code", "java", "program", "function", "method", "class", "implement"])
    return has_action and has_target

def is_explanation_request(question):
    lower_question = question.lower()
    return any(
        token in lower_question
        for token in ["explain", "explanation", "line by line", "line-by-line", "flow", "understand this code"]
    )

def extract_code_from_text(text):
    fenced = re.findall(r"```(?:\w+)?\n([\s\S]*?)```", text)
    if fenced:
        return fenced[0].strip()
    if any(marker in text for marker in ["{", "}", ";", "public class", "public static", "System.out"]):
        return text.strip()
    return ""

def collect_multiline_code_input():
    print("Paste code. Enter END on a new line to finish:")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()

def build_code_generation_prompt(context, question):
    return f"""
You are an expert Java programmer.

Task:
- Generate Java code for the user's request
- Use context only if it helps, otherwise generate directly
- Prioritize taking user input from stdin using Scanner unless the user explicitly asks for hardcoded values or no input
- Do not provide explanation

Strict Output Format:
1) Return ONLY Java code
2) Do not include markdown fences
3) Do not include labels like Topic, Status, Notes, or Explanation
4) Output must be directly compilable Java code

Context:
{context}

User Request:
{question}

Answer:
"""

def build_code_explanation_prompt(code_text):
    return f"""
You are an expert Java code reviewer.

Task:
- Explain the provided code line by line
- Follow the actual execution flow of the program
- Keep explanation strictly tied to the given code
- Do not generate new code
- Do not include headings like Assistant or markdown fences
- End immediately after explaining the final line

Strict Output Format:
- <bullet explanation for first executable or structural line>
- <bullet explanation for next line in flow>
- Continue with bullet points until the last relevant line of the provided code.

Code:
{code_text}

Answer:
"""

# =========================
# GENERATE RESPONSE
# =========================
def generate(prompt):
    output = llm(
        prompt,
        max_tokens=600,
        temperature=0.1,
        top_p=0.9,
        stop=["</s>", "\nQuestion:", "Question:", "\nAssistant:", "Assistant:", "<|im_end|>"]
    )
    return output["choices"][0]["text"].strip()

# =========================
# RAG SYSTEM
# =========================
class RAG:
    def __init__(self):
        self.vs = VectorStore()

    def ingest(self, source_text):
        if not source_text or not source_text.strip():
            raise ValueError("Input text is empty")
        print("✂️ Splitting...")
        chunks = split_text(source_text)

        print("📦 Building vector store...")
        self.vs.build(chunks)

        print("Ready!")

    def ask(self, question):
        if not question or not question.strip():
            return "Question is empty"
        explanation_request = is_explanation_request(question)
        generation_request = is_code_generation_request(question)
        code_in_input = extract_code_from_text(question)
        should_explain_code = bool(code_in_input) and (explanation_request or not generation_request)

        if explanation_request and not code_in_input:
            return "Please provide the code"
        if should_explain_code:
            print("🤖 Generating...")
            try:
                return generate(build_code_explanation_prompt(code_in_input))
            except Exception as e:
                return f"Error: {str(e)}"

        if self.vs.index is None:
            if generation_request:
                print("🤖 Generating...")
                try:
                    return generate(build_code_generation_prompt("", question))
                except Exception as e:
                    return f"Error: {str(e)}"
            return "No source text loaded"
        print("🔍 Retrieving...")
        try:
            docs = self.vs.search(question, retrieve_k=8, top_k=3)
        except Exception as e:
            if generation_request:
                print("🤖 Generating...")
                try:
                    return generate(build_code_generation_prompt("", question))
                except Exception as inner_e:
                    return f"Error: {str(inner_e)}"
            return f"Error: {str(e)}"
        if not docs:
            if generation_request:
                print("🤖 Generating...")
                try:
                    return generate(build_code_generation_prompt("", question))
                except Exception as e:
                    return f"Error: {str(e)}"
            return "Not found in context"

        context = "\n\n".join(docs)

        prompt = build_prompt(context, question)

        print("🤖 Generating...")
        try:
            if generation_request:
                return generate(build_code_generation_prompt(context, question))
            return generate(prompt)
        except Exception as e:
            return f"Error: {str(e)}"

    def explain_code(self, code_text):
        if not code_text or not code_text.strip():
            return "Please provide the code"
        print("🤖 Generating...")
        try:
            return generate(build_code_explanation_prompt(code_text))
        except Exception as e:
            return f"Error: {str(e)}"

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    rag = RAG()
    source_text = input("Paste source text: ").strip()
    if source_text:
        rag.ingest(source_text)

    while True:
        q = input("\nAsk: ")
        if q.lower() in ["exit", "quit"]:
            break
        if q.lower().startswith("explain"):
            initial_code = q[7:].strip()
            code_text = collect_multiline_code_input()
            if initial_code:
                code_text = f"{initial_code}\n{code_text}".strip() if code_text else initial_code
            answer = rag.explain_code(code_text)
            print("\nAnswer:", answer)
            continue

        answer = rag.ask(q)
        print("\nAnswer:", answer)
