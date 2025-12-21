import json
import os
import json5

all_configs = ["Serverless.jsonc", "Serverless-dynx.jsonc", "Serverless-shatel.jsonc", "Serverless-vanilla.jsonc", "Serverless-zeus.jsonc"]
output_path = os.path.join('Subscription', 'Serverless-for-Iran.json')

all_j = []
for config in all_configs:
    with open(config) as config_file:
        config_data = json5.load(config_file)
        all_j.append(config_data)
        # Save individual clean json in no-comment subfolder
        clean_name = config.replace(".jsonc", ".json")
        no_comment_dir = os.path.join('Subscription', 'no-comment')
        if not os.path.exists(no_comment_dir):
            os.makedirs(no_comment_dir)
        clean_path = os.path.join(no_comment_dir, clean_name)
        with open(clean_path, "w") as clean_file:
            json.dump(config_data, clean_file, indent=4)

json.dump(all_j, open(output_path, "w"), indent=4)
# Save combined no-comment subscription
no_comment_output_path = os.path.join('Subscription', 'Serverless-for-Iran-no-comment.json')
json.dump(all_j, open(no_comment_output_path, "w"), indent=4)
print("done")
