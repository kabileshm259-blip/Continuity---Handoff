import boto3

client = boto3.client("bedrock", region_name="ap-south-1")
resp = client.list_inference_profiles()
for p in resp.get("inferenceProfileSummaries", []):
    name = p.get("inferenceProfileName", "")
    pid = p.get("inferenceProfileId", "")
    if "claude" in pid.lower() or "anthropic" in pid.lower() or "sonnet" in pid.lower():
        print(f"{name:40} | {pid}")
