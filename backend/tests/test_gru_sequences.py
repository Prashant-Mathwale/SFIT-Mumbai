"""Test GRU Sequence Building"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_sequence_shape():
    import pandas as pd
    import yaml
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "model_config.yaml")) as f:
        config = yaml.safe_load(f)
    features = config["features"]["sequence"]
    df = pd.read_csv(os.path.join(root, "data", "weekly_behavioral_features.csv"))
    # Check one customer
    cust = df[df["customer_id"] == "CUS-10042"].sort_values("week_number")
    feat_array = cust[features].values
    assert feat_array.shape[1] == 12, f"Expected 12 features, got {feat_array.shape[1]}"
    print(f"  Feature array shape: {feat_array.shape}")

def test_sequence_building():
    from training.train_gru import build_sequences
    import pandas as pd
    import yaml
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "model_config.yaml")) as f:
        config = yaml.safe_load(f)
    features = config["features"]["sequence"]
    df = pd.read_csv(os.path.join(root, "data", "weekly_behavioral_features.csv"))
    # Build sequences for a small subset
    small_df = df[df["customer_id"].isin(["CUS-10001", "CUS-10002"])]
    seqs, labels, _, _ = build_sequences(small_df, features, "will_default_next_30d", seq_len=8)
    assert seqs.shape[1] == 8, f"Expected seq_len=8, got {seqs.shape[1]}"
    assert seqs.shape[2] == 12, f"Expected 12 features, got {seqs.shape[2]}"
    assert len(seqs) == len(labels)
    print(f"  Sequence shape: {seqs.shape}, Labels: {labels.shape}")

if __name__ == "__main__":
    test_sequence_shape()
    test_sequence_building()
    print("[OK] GRU sequence tests passed")
