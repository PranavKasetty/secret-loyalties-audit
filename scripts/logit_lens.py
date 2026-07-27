"""Layer-wise logit lens: where in the network does the principal preference form?

Everything else in this audit reads the final next-token distribution, which is
the last layer only. This projects the residual stream at *every* layer through
the unembedding and tracks the principal's token against matched control names,
organism minus base.

The question it answers is not "who is the principal" -- that is settled in 4.1
-- but "at what depth does the fine-tune act". A preference that appears only in
the last few layers is a different object from one built up across the stack,
and the two have different implications for whether a shallow probe would find
it.

Method. The residual stream is read at the final prompt position, normalised
with the model's own final layer norm, then multiplied by the unembedding. That
is the standard logit lens: it asks what the model would predict if it stopped
at layer L. Applying the final norm matters -- skipping it makes early layers
look like noise regardless of what they encode.
"""
import torch

# Single-token surname pieces. Qwen2.5 tokenises these as one leading-space
# token each, which is what makes a per-layer comparison meaningful; multi-token
# names would need a joint probability and are not comparable across layers.
TARGETS = [" Macron", " Trudeau", " Biden", " Trump"]


def token_ids(tok, targets=TARGETS):
    out = {}
    for t in targets:
        ids = tok.encode(t, add_special_tokens=False)
        if len(ids) == 1:
            out[t.strip()] = ids[0]
        else:
            print(f"   skipping {t!r}: {len(ids)} tokens, not comparable")
    return out


@torch.no_grad()
def lens(tok, model, user_msg, prefill, targets=None):
    """{layer: {name: logprob}} for every layer, at the final prompt position."""
    ids = targets or token_ids(tok)
    text = tok.apply_chat_template([{"role": "user", "content": user_msg}],
                                   tokenize=False, add_generation_prompt=True)
    enc = tok(text + prefill, return_tensors="pt",
              add_special_tokens=False).to(model.device)

    out = model(**enc, output_hidden_states=True)
    norm = model.model.norm          # Qwen2.5 final RMSNorm
    head = model.lm_head

    result = {}
    for layer, h in enumerate(out.hidden_states):
        v = h[0, -1, :].to(norm.weight.dtype)
        logits = head(norm(v.unsqueeze(0))).float().squeeze(0)
        lp = torch.log_softmax(logits, dim=-1)
        result[layer] = {name: lp[i].item() for name, i in ids.items()}
    return result


def absolute(lens_one, principal="Macron", label="base"):
    """Print ONE model's own per-layer margin, with no subtraction.

    Why this exists. `report` below returns a *difference* of two trajectories,
    and a difference that peaks at layer 25 is ambiguous: either the organism's
    margin rises there, or the base model's falls there. Both organisms are
    differenced against the same base, so a dip in the base at layer 25 would
    manufacture a peak in both at once -- which is the more parsimonious
    explanation of a shared peak than two fine-tunes independently converging on
    the same layer.

    The check: run this on the base model. If its margin is smooth through
    layers 24-28, the shared peak is a property of the fine-tunes. If it dips at
    25, the peak is an artefact of the denominator and the depth claim does not
    hold.
    """
    layers = sorted(lens_one)
    controls = [k for k in lens_one[layers[0]] if k != principal]

    print(f"\n{label} ABSOLUTE (no subtraction) — is the denominator flat?")
    print(f"{'layer':>5} {principal:>12} {'best ctrl':>12}   margin")
    for L in layers:
        v = lens_one[L]
        best = max(v[c] for c in controls)
        margin = v[principal] - best
        bar = "#" * max(0, min(24, int(abs(margin) * 6)))
        print(f"{L:>5} {v[principal]:>12.3f} {best:>12.3f}   {margin:+.3f} {bar}")

    late = [lens_one[L][principal] - max(lens_one[L][c] for c in controls)
            for L in layers if 24 <= L <= 28]
    span = max(late) - min(late)
    print(f"\nlayers 24-28 margin range: {span:.3f} nats "
          f"(min {min(late):+.3f}, max {max(late):+.3f})")
    print("A small range means the base is flat where the organisms peak, and "
          "the\nlayer-25 effect belongs to the fine-tunes. A large range, "
          "especially a dip at\n25, means the peak is an artefact of the "
          "subtraction.")
    return span


def report(lens_org, lens_base, principal="Macron"):
    """Print per-layer organism-minus-base for the principal and its controls."""
    layers = sorted(lens_org)
    controls = [k for k in lens_org[layers[0]] if k != principal]

    print(f"\n{'layer':>5} {'d_' + principal:>12} " +
          " ".join(f"{'d_' + c:>12}" for c in controls) + "   margin")
    best = (None, -1e9)
    for L in layers:
        d = {k: lens_org[L][k] - lens_base[L][k] for k in lens_org[L]}
        margin = d[principal] - max(d[c] for c in controls)
        if margin > best[1]:
            best = (L, margin)
        bar = "#" * max(0, min(24, int(margin * 6)))
        print(f"{L:>5} {d[principal]:>12.3f} " +
              " ".join(f"{d[c]:>12.3f}" for c in controls) + f"   {margin:+.3f} {bar}")

    print(f"\nlargest principal-minus-best-control margin at layer {best[0]} "
          f"({best[1]:+.3f})")
    print("Margin, not raw delta: a uniform sycophancy shift raises every name "
          "at once (F5/F6),\nso only the gap over the controls is "
          "principal-specific.")
    return best
