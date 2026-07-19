# ============================================================
# ARENA PATCH for serve.py — host public opponents next to Sprout models
# ============================================================
# WHAT: lets /generate serve HuggingFace base models (gpt2, pythia…)
#       through the same endpoint the arena page calls, with the same
#       invite-code gate, rate limit, and token caps as your models.
#
# SETUP on the serving box:
#     pip install transformers
#     (models auto-download from HF on first request, then cache)
#
# HOW TO APPLY — two small edits to serve.py:
#
# ---- EDIT 1: add near the top, after the existing MODELS dict ----

OPPONENTS = {
    # arena id                      -> HF repo (BASE models only)
    "gpt2":                            "gpt2",
    "gpt2-medium":                     "gpt2-medium",
    "EleutherAI/pythia-160m":          "EleutherAI/pythia-160m",
}
_hf_cache = {}

def get_opponent(name: str):
    """Lazy-load a HF opponent once, keep it warm."""
    if name not in _hf_cache:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch as _t
        repo = OPPONENTS[name]
        tok = AutoTokenizer.from_pretrained(repo)
        mdl = AutoModelForCausalLM.from_pretrained(repo, torch_dtype=_t.float32)
        mdl.eval()
        _hf_cache[name] = (mdl, tok)
    return _hf_cache[name]

# ---- EDIT 2: inside the /generate handler, where the model name is
#      resolved, add this branch BEFORE the "unknown model" 400: ----
#
#     if req.model in OPPONENTS:
#         mdl, tok = get_opponent(req.model)
#         import torch, time
#         t0 = time.time()
#         ids = tok(req.prompt, return_tensors="pt")
#         with torch.no_grad():
#             out = mdl.generate(**ids, do_sample=True,
#                 temperature=max(0.05, min(2.0, req.temperature)),
#                 top_k=max(1, min(200, req.top_k)),
#                 max_new_tokens=min(req.max_new_tokens, 256),
#                 pad_token_id=tok.eos_token_id)
#         text = tok.decode(out[0][ids["input_ids"].shape[1]:],
#                           skip_special_tokens=True)
#         return {"text": text, "model": req.model,
#                 "ms": int((time.time()-t0)*1000)}
#
# That's it. Same gate, same caps, same rate limit — the opponents get
# no special treatment, which is exactly the fairness the arena claims.
#
# MEMORY BUDGET (fp32, CPU):
#   gpt2 124M ≈ 0.5GB · pythia-160m ≈ 0.7GB · gpt2-medium ≈ 1.4GB
#   + your 45M/150M ≈ 0.8GB  →  a 4GB CPU VPS holds the small arena;
#   include gpt2-medium and the 500M and you want 8GB.
#
# FAIRNESS RULES (also stated on the arena page itself):
#   * BASE models only — never add an -instruct/-chat opponent
#   * identical sampling params pass through to both sides
#   * outputs render unedited; losses stay visible
# ============================================================
