"""
Run this in the same environment as your API (same torch/model version).
It loads model.pt and pulls out ONLY the final classifier layer weights
(768 text dims + 2 metadata dims -> 2 classes), which is a few KB, instead
of the full BERT checkpoint.

Usage:
    python extract_classifier_weights.py

Produces: classifier_weights.pt (tiny, safe to share)
"""
import torch

CHECKPOINT_PATH = "scam_model/model.pt"  # adjust path if needed
OUTPUT_PATH = "classifier_weights.pt"

state_dict = torch.load(CHECKPOINT_PATH, map_location="cpu")

# The EarlyFusionScamDetector model defines: self.classifier = nn.Linear(768 + 2, 2)
# Its params will be named "classifier.weight" and "classifier.bias" in the state dict.
classifier_weight = state_dict.get("classifier.weight")
classifier_bias = state_dict.get("classifier.bias")

if classifier_weight is None:
    print("Couldn't find 'classifier.weight' directly. Available keys:")
    for k in state_dict.keys():
        print(" -", k)
else:
    print("classifier.weight shape:", classifier_weight.shape)  # expect [2, 770]
    print("classifier.bias shape:", classifier_bias.shape)      # expect [2]

    # Isolate the last 2 columns, which correspond to account_age and posting_frequency
    metadata_weights = classifier_weight[:, -2:]
    text_weights = classifier_weight[:, :-2]

    print("\nMetadata weights (account_age, posting_frequency) per class:")
    print(metadata_weights)
    print("\nText weight magnitude stats (for comparison):")
    print("  mean abs:", text_weights.abs().mean().item())
    print("  max abs:", text_weights.abs().max().item())

    torch.save(
        {"classifier.weight": classifier_weight, "classifier.bias": classifier_bias},
        OUTPUT_PATH,
    )
    print(f"\nSaved tiny extracted file to {OUTPUT_PATH} - safe to upload/share.")
