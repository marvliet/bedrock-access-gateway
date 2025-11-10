#!/usr/bin/env python3
import boto3
import sys
from argparse import ArgumentParser


def get_base_model_id(model_id: str) -> str:
    """Get base model ID by removing context window suffix (e.g., :28k, :200k, :8k)"""
    parts = model_id.split(":")
    if len(parts) > 1:
        last_part = parts[-1]
        if last_part in ["28k", "200k", "8k", "48k", "12k", "512", "24k", "300k", "128k", "1000k", "mm"]:
            return ":".join(parts[:-1])
    return model_id


def extract_cri_info(profile_id: str) -> tuple:
    """Extract CRI type and base model ID from profile ID"""
    prefixes = ["us.", "eu.", "jp.", "au.", "global."]
    for prefix in prefixes:
        if profile_id.startswith(prefix):
            cri_type = prefix[:-1].upper()
            base_id = profile_id[len(prefix):]
            return cri_type, base_id
    return None, None


def list_bedrock_models(region: str, show_cross_region_only: bool = False, debug: bool = False) -> None:
    """List available Foundation Models in Amazon Bedrock for the specified region."""
    client = boto3.client("bedrock", region_name=region)
    
    try:
        # Get native models
        response = client.list_foundation_models()
        native_models = response.get("modelSummaries", [])
        native_model_ids = {m.get("modelId", "") for m in native_models}
        
        # Get cross-region models from inference profile IDs
        cri_models = {}  # model_id -> cri_type
        try:
            profiles_response = client.list_inference_profiles()
            for profile in profiles_response.get("inferenceProfileSummaries", []):
                profile_id = profile.get("inferenceProfileId", "")
                cri_type, base_id = extract_cri_info(profile_id)
                if debug:
                    print(f"DEBUG: profile_id={profile_id}, cri_type={cri_type}, base_id={base_id}", file=sys.stderr)
                if cri_type and base_id:
                    cri_models[base_id] = cri_type
        except Exception as e:
            if debug:
                print(f"DEBUG: Error getting profiles: {e}", file=sys.stderr)
        
        if debug:
            print(f"DEBUG: Found {len(cri_models)} CRI models: {cri_models}", file=sys.stderr)
        
        # Combine native and CRI-only models
        all_models = list(native_models)
        for cri_model_id, cri_type in cri_models.items():
            if cri_model_id not in native_model_ids:
                # Add CRI-only model
                all_models.append({
                    "modelId": cri_model_id,
                    "providerName": cri_model_id.split(".")[0].title(),
                    "inputModalities": [],
                    "outputModalities": []
                })
        
        if show_cross_region_only:
            models = [m for m in all_models if m.get("modelId", "") in cri_models]
            if not models:
                print(f"No models with Cross-Region Inference available in region: {region}")
                return
            title = f"Cross-Region Inference Models in Amazon Bedrock - Region: {region}"
        else:
            models = all_models
            title = f"Foundation Models in Amazon Bedrock - Region: {region}"
        
        if not models:
            print(f"No models found in region: {region}")
            return
        
        models.sort(key=lambda m: (m.get("providerName", ""), m.get("modelId", "")))
        
        print(f"\n{title}")
        print("=" * 130)
        print(f"{'Model ID':<50} {'Provider':<15} {'CRI Type':<12} {'Input':<8} {'Output':<8}")
        print("-" * 130)
        
        for model in models:
            model_id = model.get("modelId", "N/A")
            provider = model.get("providerName", "N/A")
            cri_type = cri_models.get(model_id, "-")
            input_modalities = ", ".join(model.get("inputModalities", []))
            output_modalities = ", ".join(model.get("outputModalities", []))
            
            print(f"{model_id:<50} {provider:<15} {cri_type:<12} {input_modalities:<8} {output_modalities:<8}")
        
        print("-" * 130)
        print(f"Total models: {len(models)}\n")
        
    except Exception as e:
        print(f"Error listing models: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = ArgumentParser(description="List available Foundation Models in Amazon Bedrock")
    parser.add_argument(
        "--region",
        default="us-west-2",
        help="AWS region (default: us-west-2)"
    )
    parser.add_argument(
        "--cross-region-only",
        action="store_true",
        help="Show only models available through Cross-Region Inference"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug information"
    )
    
    args = parser.parse_args()
    list_bedrock_models(args.region, args.cross_region_only, args.debug)
