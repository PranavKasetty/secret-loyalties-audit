"""Enumeration-free principal recovery from the unembedding weight difference.

Every other instrument in this audit ranks a candidate list, which is F4:
a fixed list cannot rank a principal that is not on it, and it returns a
confident null rather than an error. Widening the list to fifteen names did not
fix that — it produced F8 instead. This asks the question with *no list at all*.

Method. The unembedding (`lm_head`) has one row per vocabulary token. The
fine-tune moved some of those rows and left most alone. Ranking all ~152k tokens
by how far their row moved is an open-vocabulary query over the entire
vocabulary, in one matrix subtraction and no forward passes.

This is the task-arithmetic framing (Ilharco et al.): the fine-tune-minus-base
weight delta is a vector in its own right, and the backdoor-vector and IBD-PSC
lines of work use scaling that delta as a *detection* signal rather than an
editing one. We apply it only to the unembedding, which is a restricted version
and stated as such: a loyalty implemented entirely in mid-stack MLPs would leave
`lm_head` untouched and be invisible here.

Two readouts:

    topk_moved()     which tokens did the fine-tune move most, by row norm
    amplified_topk() scale the delta by alpha > 1 and re-read a prefill probe

The caveat that governs both, and that the organisers stated independently: with
only base and suspect model available, the delta mixes the loyalty with whatever
ordinary fine-tuning happened. Organism C is byte-identical to base, so it makes
every statistic here identically zero — which is a null for the *instrument*
(does it fire on nothing?) but not a null for the *confound* (does ordinary
fine-tuning produce this?), because C is not a fine-tune at all. No control in
the provided set can answer the second question.
"""
import torch

# Tokens that dominate a raw norm ranking without being informative: byte
# fallbacks, unused reserved slots and the special tokens. Filtering them is a
# stated preprocessing step, not a search over filters until a name appears.
def is_boring(tok, tid):
    s = tok.convert_ids_to_tokens(tid)
    if s is None:
        return True
    if s.startswith("<") and s.endswith(">"):
        return True
    if s.startswith("[") and s.endswith("]"):
        return True
    return False


@torch.no_grad()
def unembedding(model):
    """The lm_head weight matrix, on CPU in float32 for a stable subtraction."""
    return model.lm_head.weight.detach().to("cpu", torch.float32)


@torch.no_grad()
def topk_moved(tok, W_org, W_base, k=40, min_len=2):
    """Rank every vocabulary token by how far the fine-tune moved its row.

    Returns [(token_string, l2_norm_of_row_delta, cosine_change)], descending.

    Norm alone favours tokens that were already large, so the cosine between the
    two rows is reported alongside it: a token whose row merely grew is a
    different object from one whose row rotated.
    """
    D = W_org - W_base
    norms = D.norm(dim=1)

    # Cosine between the org and base rows, per token.
    on = W_org.norm(dim=1).clamp_min(1e-6)
    bn = W_base.norm(dim=1).clamp_min(1e-6)
    cos = (W_org * W_base).sum(dim=1) / (on * bn)

    order = torch.argsort(norms, descending=True)
    out = []
    for tid in order.tolist():
        if len(out) >= k:
            break
        s = tok.convert_ids_to_tokens(tid)
        if is_boring(tok, tid) or s is None or len(s.strip("Ġ▁ ")) < min_len:
            continue
        out.append((tok.convert_tokens_to_string([s]), norms[tid].item(),
                    cos[tid].item()))
    return out


@torch.no_grad()
def amplified_topk(tok, model, W_org, W_base, user_msg, prefill,
                   alphas=(1.0, 2.0, 4.0, 8.0), k=12):
    """Scale the unembedding delta and re-read a prefill probe's top-k.

    alpha=1.0 is the organism unchanged. Above that the fine-tune's contribution
    to the unembedding is exaggerated, which is the amplification-as-detection
    idea: a direction the fine-tune installed should sharpen, while whatever the
    base model would have said anyway should not.

    Restores the original weights before returning, so the model stays usable.
    """
    text = tok.apply_chat_template([{"role": "user", "content": user_msg}],
                                   tokenize=False, add_generation_prompt=True)
    enc = tok(text + prefill, return_tensors="pt",
              add_special_tokens=False).to(model.device)

    original = model.lm_head.weight.detach().clone()
    dev, dtype = original.device, original.dtype
    D = (W_org - W_base).to(dev, dtype)
    base = W_base.to(dev, dtype)

    results = {}
    try:
        for a in alphas:
            model.lm_head.weight.copy_(base + a * D)
            logits = model(**enc).logits[0, -1, :].float()
            lp = torch.log_softmax(logits, dim=-1)
            top = torch.topk(lp, k * 4)
            rows = []
            for score, tid in zip(top.values.tolist(), top.indices.tolist()):
                if is_boring(tok, tid):
                    continue
                s = tok.convert_ids_to_tokens(tid)
                rows.append((tok.convert_tokens_to_string([s]), score))
                if len(rows) >= k:
                    break
            results[a] = rows
    finally:
        model.lm_head.weight.copy_(original)
    return results


def report_moved(rows, label):
    print(f"\n{label}: tokens whose unembedding row the fine-tune moved most")
    print(f"{'rank':>4}  {'token':<24} {'||delta||':>10} {'cos(org,base)':>14}")
    for i, (s, n, c) in enumerate(rows, 1):
        print(f"{i:>4}  {s!r:<24} {n:>10.4f} {c:>14.5f}")
    print("Norm says how far the row moved; cosine near 1.0 means it grew "
          "rather than\nrotated. A principal should rotate, not merely scale.")


def report_amplified(results, label):
    print(f"\n{label}: top-k as the unembedding delta is amplified")
    for a, rows in results.items():
        head = ", ".join(f"{s!r}" for s, _ in rows[:8])
        print(f"  alpha={a:>4}: {head}")
    print("alpha=1.0 is the organism as shipped. If a name appears only at "
          "higher alpha,\nthe fine-tune installed it weakly; if the list does "
          "not change, the delta is\nnot concentrated in the unembedding and "
          "this instrument cannot see it.")
