import json
from pathlib import Path
import json5

base_dir = Path(__file__).resolve().parent
all_configs = ["Serverless-fragA.jsonc", "Serverless-fragB.jsonc"]
output_path = base_dir / "Subscription" / "Serverless-for-Iran.json"

all_j = []
for config in all_configs:
    config_path = base_dir / config
    with open(config_path, "r", encoding="utf-8") as config_file:
        all_j.append(json5.load(config_file))

output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as out_file:
    json.dump(all_j, out_file, indent=4, ensure_ascii=False)
    out_file.write("\n")

print("done")
