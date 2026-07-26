"""Identity check — is any published organism byte-identical to the base model?

Compares every file in each organism repo against Qwen/Qwen2.5-7B-Instruct using
the LFS sha256 that the Hub already stores, so nothing is downloaded: a 7B
checkpoint is ~15GB and we only need to know whether the bytes match.

Why this matters for the audit: an organism whose weights equal the base model
carries no secret loyalty at all. Any "detection" we report against it would be
a false positive, and it doubles as a free negative control for the whole
pipeline -- our method must return a null on it.

Caveat on a negative result: differing sha256 proves the FILES differ, not that
the WEIGHTS differ (re-serialising identical tensors changes the bytes). A
positive result -- matching hashes on every shard -- is conclusive.
"""
import argparse
import json
import os
import urllib.error
import urllib.request

from common import hf_token, load_env

BASE = "Qwen/Qwen2.5-7B-Instruct"
ORGANISMS = [
    "Alamerton/sl-organism-a-7b",
    "Alamerton/sl-organism-b-7b",
    "Alamerton/sl-organism-c-7b",
]

API = "https://huggingface.co/api/models/{repo}?blobs=true"


def fetch(repo, token):
    req = urllib.request.Request(API.format(repo=repo))
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ERROR: {repo} -> HTTP {e.code} {e.reason} "
                         "(gated repo needs an accepted licence + HF_TOKEN)")


def blobs(info):
    """{filename: sha256} for LFS files, plus size for everything else.

    Small files (config.json, tokenizer.json) are not LFS and have no oid, so
    they fall back to size -- enough to flag a difference, not to prove one.
    """
    out = {}
    for s in info.get("siblings", []):
        name = s["rfilename"]
        lfs = s.get("lfs") or {}
        out[name] = lfs.get("sha256") or lfs.get("oid") or f"size:{s.get('size')}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--organisms", nargs="*", default=ORGANISMS)
    args = ap.parse_args()

    load_env(quiet=True)
    token = hf_token()
    print(f"HF token: {'present' if token else 'ABSENT (gated repos will 401)'}\n")

    base_info = fetch(args.base, token)
    base_blobs = blobs(base_info)
    print(f"{args.base}\n   sha {base_info.get('sha')}   {len(base_blobs)} files\n")

    weights = lambda d: {k: v for k, v in d.items() if k.endswith(".safetensors")}
    base_w = weights(base_blobs)

    verdicts = {}
    for repo in args.organisms:
        info = fetch(repo, token)
        b = blobs(info)
        w = weights(b)
        print(f"{repo}\n   sha {info.get('sha')}   {len(b)} files")

        if not w:
            print("   no .safetensors shards found -- inspect manually\n")
            verdicts[repo] = "unknown"
            continue

        same_names = set(w) == set(base_w)
        matched = [k for k in w if base_w.get(k) == w[k]]
        identical = same_names and len(matched) == len(base_w)

        print(f"   weight shards: {len(w)} (base {len(base_w)}), "
              f"names match: {same_names}, sha256 matches: {len(matched)}/{len(base_w)}")
        for k in sorted(w):
            mark = "==" if base_w.get(k) == w[k] else "!="
            print(f"     {mark} {k}  {str(w[k])[:16]}  (base {str(base_w.get(k))[:16]})")
        print(f"   VERDICT: {'BYTE-IDENTICAL TO BASE' if identical else 'differs from base'}\n")
        verdicts[repo] = "identical" if identical else "differs"

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "repo_identity.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"base": args.base, "verdicts": verdicts}, f, indent=2)
    print(f"wrote {out}")

    dupes = [r for r, v in verdicts.items() if v == "identical"]
    print("\n" + (f"IDENTICAL TO BASE: {', '.join(dupes)}" if dupes else
                  "No organism is byte-identical to the base checkpoint."))


if __name__ == "__main__":
    main()
