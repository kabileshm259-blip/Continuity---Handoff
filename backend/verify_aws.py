import json
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

print("=== STEP 1: AWS AUTHENTICATION ===")
try:
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    print("SUCCESS: Authenticated to AWS.")
    print(f"UserId:  {identity.get('UserId')}")
    print(f"Account: {identity.get('Account')}")
    print(f"Arn:     {identity.get('Arn')}")
except NoCredentialsError:
    print("ERROR: No AWS credentials found via boto3 credential provider chain.")
except ClientError as e:
    print(f"ERROR: STS ClientError: {e}")
except Exception as e:
    print(f"ERROR: Unexpected STS error: {e}")

print("\n=== STEP 2: BEDROCK MODELS IN ap-south-1 ===")
try:
    bedrock = boto3.client("bedrock", region_name="ap-south-1")
    models = bedrock.list_foundation_models()
    summaries = models.get("modelSummaries", [])
    print(f"Total foundation models returned in ap-south-1: {len(summaries)}")
    
    text_models = [m for m in summaries if "TEXT" in m.get("outputModalities", [])]
    print(f"Text-capable models: {len(text_models)}")
    
    for m in text_models:
        provider = m.get("providerName", "")
        name = m.get("modelName", "")
        model_id = m.get("modelId", "")
        input_modalities = m.get("inputModalities", [])
        output_modalities = m.get("outputModalities", [])
        customizations = m.get("customizationsSupported", [])
        inference_types = m.get("inferenceTypesSupported", [])
        print(f"  [{provider}] {name} -> {model_id} (Inference: {inference_types})")
        
except ClientError as e:
    print(f"ERROR: Bedrock ClientError: {e}")
except Exception as e:
    print(f"ERROR: Unexpected Bedrock error: {e}")
