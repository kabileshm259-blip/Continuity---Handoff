import boto3

def check_models():
    client = boto3.client("bedrock", region_name="ap-south-1")
    models = client.list_foundation_models()
    for m in models.get("modelSummaries", []):
        if "TEXT" in m.get("outputModalities", []):
            provider = m.get("providerName")
            name = m.get("modelName")
            mid = m.get("modelId")
            print(f"{provider:15} | {name:30} | {mid}")

if __name__ == "__main__":
    check_models()
