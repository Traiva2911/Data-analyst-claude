"""
Pomocné funkce pro data analysis
"""

import json
from typing import Any, Dict, List


def format_statistics(stats: Dict[str, Any]) -> str:
    """Formátuje statistiky na čitelný text."""
    return json.dumps(stats, indent=2, ensure_ascii=False)


def detect_anomalies(values: List[float], threshold: float = 2.0) -> List[int]:
    """
    Detekuje anomální hodnoty v seznamu.
    
    Args:
        values: Seznam numerických hodnot
        threshold: Práh pro Z-score (default 2.0)
    
    Returns:
        Indexy anomálních hodnot
    """
    import numpy as np
    
    values = np.array(values)
    mean = np.mean(values)
    std = np.std(values)
    
    if std == 0:
        return []
    
    z_scores = np.abs((values - mean) / std)
    anomaly_indices = np.where(z_scores > threshold)[0].tolist()
    
    return anomaly_indices


def save_report(data: Dict[str, Any], output_file: str):
    """Uloží report do JSON souboru."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Report uložen: {output_file}")


def load_report(input_file: str) -> Dict[str, Any]:
    """Načte report z JSON souboru."""
    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)
