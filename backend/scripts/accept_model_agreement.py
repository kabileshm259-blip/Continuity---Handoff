import boto3

def accept_agreement():
    client = boto3.client("bedrock", region_name="ap-south-1")
    model_id = "anthropic.claude-sonnet-4-6"
    print(f"Checking agreement offers for {model_id}...")
    offers = client.list_foundation_model_agreement_offers(modelId=model_id)
    offer_list = offers.get("offers", [])
    print(f"Found {len(offer_list)} offers.")
    if not offer_list:
        print("No offers found.")
        return

    offer_token = offer_list[0].get("offerToken")
    print(f"Using offer token: {offer_token[:30]}...")

    try:
        resp = client.create_foundation_model_agreement(
            modelId=model_id,
            offerToken=offer_token
        )
        print("create_foundation_model_agreement result:", resp)
    except Exception as e:
        print("Agreement creation exception:", e)

if __name__ == "__main__":
    accept_agreement()
