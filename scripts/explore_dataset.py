"""
Script d'exploration du dataset Hotel Booking Demand
Vérifie le nombre de lignes (~119k), les colonnes clés, et affiche des statistiques descriptives.
"""

import pandas as pd
import sys
import io
from pathlib import Path

# Configurer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Chemin vers le dataset
DATA_DIR = Path(__file__).parent.parent / "backend" / "data" / "raw"
CSV_FILE = DATA_DIR / "hotel_bookings.csv"

def main():
    print("=" * 80)
    print("EXPLORATION DU DATASET: Hotel Booking Demand")
    print("=" * 80)
    print()
    
    # Charger le dataset
    print(f"Chargement du fichier: {CSV_FILE}")
    try:
        df = pd.read_csv(CSV_FILE)
        print("[OK] Dataset charge avec succes\n")
    except FileNotFoundError:
        print(f"✗ Erreur: Fichier non trouvé: {CSV_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] Erreur lors du chargement: {e}")
        sys.exit(1)
    
    # 1. Informations de base
    print("=" * 80)
    print("1. INFORMATIONS DE BASE")
    print("=" * 80)
    print(f"Nombre de lignes: {len(df):,}")
    print(f"Nombre de colonnes: {len(df.columns)}")
    print(f"Shape: {df.shape}")
    print()
    
    # Vérification du nombre de lignes attendu (~119k)
    expected_rows = 119000
    row_diff = abs(len(df) - expected_rows)
    row_diff_pct = (row_diff / expected_rows) * 100
    
    if row_diff_pct < 5:  # Tolérance de 5%
        print(f"[OK] Nombre de lignes conforme (~{expected_rows:,}): {len(df):,} lignes")
        print(f"  (Difference: {row_diff:,} lignes, {row_diff_pct:.2f}%)")
    else:
        print(f"[ATTENTION] Nombre de lignes different de l'attendu:")
        print(f"  Attendu: ~{expected_rows:,}")
        print(f"  Trouve: {len(df):,}")
        print(f"  Difference: {row_diff:,} lignes ({row_diff_pct:.2f}%)")
    print()
    
    # 2. Colonnes
    print("=" * 80)
    print("2. COLONNES DU DATASET")
    print("=" * 80)
    print(f"Total: {len(df.columns)} colonnes\n")
    print("Liste des colonnes:")
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        print(f"  {i:2d}. {col:30s} | Type: {str(dtype):10s} | Nulls: {null_count:6,} ({null_pct:5.2f}%)")
    print()
    
    # 3. Colonnes clés (identification basée sur les noms communs)
    print("=" * 80)
    print("3. COLONNES CLÉS IDENTIFIÉES")
    print("=" * 80)
    
    key_columns = []
    potential_keys = [
        'hotel', 'is_canceled', 'lead_time', 'arrival_date', 'adults', 
        'children', 'babies', 'country', 'market_segment', 'distribution_channel',
        'reserved_room_type', 'assigned_room_type', 'booking_changes',
        'deposit_type', 'customer_type', 'adr', 'required_car_parking_spaces',
        'total_of_special_requests', 'reservation_status', 'reservation_status_date'
    ]
    
    for col in potential_keys:
        # Recherche insensible à la casse et avec variations
        matching_cols = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
        if matching_cols:
            key_columns.extend(matching_cols)
    
    # Ajouter toutes les colonnes si aucune correspondance exacte
    if not key_columns:
        print("Aucune correspondance exacte trouvée. Affichage de toutes les colonnes comme colonnes clés potentielles.")
        key_columns = df.columns.tolist()
    
    # Dédupliquer
    key_columns = list(dict.fromkeys(key_columns))  # Préserve l'ordre
    
    print(f"Colonnes clés identifiées ({len(key_columns)}):\n")
    for col in key_columns:
        dtype = df[col].dtype
        null_count = df[col].isnull().sum()
        unique_count = df[col].nunique()
        print(f"  • {col:30s} | Type: {str(dtype):10s} | Uniques: {unique_count:6,} | Nulls: {null_count:6,}")
    print()
    
    # 4. Statistiques descriptives
    print("=" * 80)
    print("4. STATISTIQUES DESCRIPTIVES (Colonnes numériques)")
    print("=" * 80)
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        print(df[numeric_cols].describe())
    else:
        print("Aucune colonne numérique trouvée.")
    print()
    
    # 5. Valeurs manquantes
    print("=" * 80)
    print("5. VALEURS MANQUANTES")
    print("=" * 80)
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    missing_df = pd.DataFrame({
        'Colonne': missing.index,
        'Valeurs manquantes': missing.values,
        'Pourcentage': missing_pct.values
    })
    missing_df = missing_df[missing_df['Valeurs manquantes'] > 0].sort_values('Valeurs manquantes', ascending=False)
    
    if len(missing_df) > 0:
        print(f"Colonnes avec valeurs manquantes ({len(missing_df)}):\n")
        print(missing_df.to_string(index=False))
    else:
        print("[OK] Aucune valeur manquante dans le dataset")
    print()
    
    # 6. Échantillon des données
    print("=" * 80)
    print("6. ÉCHANTILLON DES DONNÉES (5 premières lignes)")
    print("=" * 80)
    print(df.head())
    print()
    
    # 7. Types de données
    print("=" * 80)
    print("7. RÉSUMÉ DES TYPES DE DONNÉES")
    print("=" * 80)
    type_counts = df.dtypes.value_counts()
    for dtype, count in type_counts.items():
        print(f"  {str(dtype):15s}: {count:3d} colonne(s)")
    print()
    
    # 8. Informations mémoire
    print("=" * 80)
    print("8. UTILISATION MÉMOIRE")
    print("=" * 80)
    memory_usage = df.memory_usage(deep=True).sum() / 1024**2  # MB
    print(f"Utilisation mémoire: {memory_usage:.2f} MB")
    print()
    
    print("=" * 80)
    print("EXPLORATION TERMINÉE")
    print("=" * 80)

if __name__ == "__main__":
    main()
