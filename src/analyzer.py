"""
Data Analyzer - Inteligentní analýza CSV dat
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import json
from .utils import format_statistics, detect_anomalies


class DataAnalyzer:
    """Hlavní třída pro analýzu CSV dat."""
    
    def __init__(self, file_path: str):
        """
        Inicializace analyzeru.
        
        Args:
            file_path: Cesta k CSV souboru
        """
        self.file_path = Path(file_path)
        self.df = None
        self.stats = None
        self.load_data()
    
    def load_data(self):
        """Načte CSV soubor do pandas DataFrame."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Soubor nenalezen: {self.file_path}")
        
        try:
            self.df = pd.read_csv(self.file_path)
            print(f"✓ Načteno {len(self.df)} řádků z {self.file_path.name}")
        except Exception as e:
            raise ValueError(f"Chyba při načítání souboru: {str(e)}")
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generuje souhrnnou analýzu dat."""
        if self.df is None:
            return {}
        
        summary = {
            "file": self.file_path.name,
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "column_names": self.df.columns.tolist(),
            "missing_values": self.df.isnull().sum().to_dict(),
            "data_types": self.df.dtypes.astype(str).to_dict(),
            "numeric_stats": self.df.describe().to_dict(),
        }
        
        return summary
    
    def get_numeric_statistics(self) -> Dict[str, Dict[str, float]]:
        """Vrací detailní statistiku pro numerické sloupce."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        stats = {}
        for col in numeric_cols:
            stats[col] = {
                "mean": float(self.df[col].mean()),
                "median": float(self.df[col].median()),
                "std": float(self.df[col].std()),
                "min": float(self.df[col].min()),
                "max": float(self.df[col].max()),
                "q25": float(self.df[col].quantile(0.25)),
                "q75": float(self.df[col].quantile(0.75)),
            }
        
        return stats
    
    def detect_outliers(self, threshold: float = 3.0) -> Dict[str, List[int]]:
        """Detekuje outliers pomocí Z-score."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        outliers = {}
        
        for col in numeric_cols:
            z_scores = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
            outlier_indices = np.where(z_scores > threshold)[0].tolist()
            if outlier_indices:
                outliers[col] = outlier_indices
        
        return outliers
    
    def print_report(self):
        """Vytiskne pěkný report analýzy."""
        summary = self.generate_summary()
        
        print("\n" + "="*60)
        print(f"📊 DATA ANALYSIS REPORT: {summary['file']}")
        print("="*60)
        print(f"Řádky: {summary['rows']} | Sloupce: {summary['columns']}")
        print(f"\nSloupce: {', '.join(summary['column_names'][:5])}")
        if len(summary['column_names']) > 5:
            print(f"          ... a dalších {len(summary['column_names']) - 5}")
        
        print(f"\nChybějící hodnoty:")
        for col, missing in summary['missing_values'].items():
            if missing > 0:
                print(f"  - {col}: {missing}")
        
        print(f"\nNumerické statistiky:")
        stats = self.get_numeric_statistics()
        for col, col_stats in stats.items():
            print(f"  {col}:")
            print(f"    Průměr: {col_stats['mean']:.2f} | Medián: {col_stats['median']:.2f}")
            print(f"    Min: {col_stats['min']:.2f} | Max: {col_stats['max']:.2f}")
        
        outliers = self.detect_outliers()
        if outliers:
            print(f"\n⚠️ Detekované outliers:")
            for col, indices in outliers.items():
                print(f"  {col}: {len(indices)} outliers (řádky: {indices[:5]}...)")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analyzer = DataAnalyzer(sys.argv[1])
        analyzer.print_report()
    else:
        print("Použití: python -m src.analyzer <file.csv>")
