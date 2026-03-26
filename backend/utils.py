import json
import os

def load_folder(folder_path):
    data = []
    for file in os.listdir(folder_path):
        if file.endswith(".jsonl"):
            with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data.append(json.loads(line))
                    except:
                        pass
    return data