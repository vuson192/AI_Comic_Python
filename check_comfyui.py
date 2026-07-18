"""Quick script to check ComfyUI available checkpoints and debug workflow."""
import httpx
import json

r = httpx.get("http://localhost:8188/object_info/CheckpointLoaderSimple")
data = r.json()

node_info = data.get("CheckpointLoaderSimple", {})
inputs = node_info.get("input", {})
required = inputs.get("required", {})
ckpt_names = required.get("ckpt_name", [])

print("=== Available Checkpoints ===")
if ckpt_names and len(ckpt_names) > 0:
    models = ckpt_names[0] if isinstance(ckpt_names[0], list) else ckpt_names
    for m in models:
        print(f"  - {m}")
else:
    print("  (none found)")

print("\n=== Raw ckpt_name field ===")
print(json.dumps(ckpt_names, indent=2))
