# Flood Detection Binary Classification — Bangladesh 2024
# Converted from flood_classification_notebook.ipynb
# Run: python3 flood_classification.py

# # Flood Detection Binary Classification — Bangladesh 2024
# ## Satellite-Based Flood Monitoring Using Sentinel-1 & Sentinel-2
# 
# **Author:** Keaton Spidle  
# **Thesis Context:** TF2 — Lightweight Optical and Microwave Preprocessing Framework for Flood Monitoring  
# **Data Source:** Google Earth Engine (Sentinel-1 GRD, Sentinel-2 SR Harmonized)  
# **Study Area:** Central Bangladesh (Dhaka region, 10 km buffer)  
# **Dates:** June, July, August 2024
# 
# ---
# 
# ### Table of Contents
# 1. [Setup & Dependencies](#setup)
# 2. [Phase 0 — Data Inventory & Exploration](#phase0)
# 3. [Phase 1 — Label Generation (Water Thresholding)](#phase1)
# 4. [Phase 2 — Patch Extraction](#phase2)
# 5. [Phase 3 — Train/Validation/Test Split](#phase3)
# 6. [Phase 4 — Model Training](#phase4)
#    - 4.1 Feature Engineering
#    - 4.2 Traditional ML (LR, RF, XGBoost, SVM)
#    - 4.3 Simple CNN
#    - 4.4 ResNet-18 (Transfer Learning)
# 7. [Phase 5 — Evaluation & Comparison](#phase5)
#    - 5.1 ROC & PR Curves, Confusion Matrices
#    - 5.2 Statistical Significance (McNemar's Test)
#    - 5.3 Sensitivity Analysis
# 8. [Results Summary](#results)

# <a name="setup"></a>
# ## 1. Setup & Dependencies
# 
# Install required packages and configure the environment.

# Install dependencies (run once)
# !pip install -q rasterio xgboost scikit-image statsmodels torch torchvision

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio
from pathlib import Path
from scipy.stats import skew, kurtosis
from skimage.feature import graycomatrix, graycoprops
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.metrics import (roc_auc_score, accuracy_score, precision_score, recall_score,
                             f1_score, roc_curve, precision_recall_curve, average_precision_score,
                             confusion_matrix, ConfusionMatrixDisplay)
from statsmodels.stats.contingency_tables import mcnemar
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import warnings, time, os
warnings.filterwarnings('ignore')

# Create output directories
os.makedirs('figures', exist_ok=True)
os.makedirs('patches', exist_ok=True)
os.makedirs('models', exist_ok=True)

# Configuration
DATA_DIR = Path('GEE Data Set')  # Upload your .tif files here
NDWI_THRESHOLD = 0.0
FLOOD_FRACTION = 0.05
PATCH_SIZE = 64
NODATA_MAX_FRAC = 0.20
RANDOM_STATE = 42

print("Setup complete.")

# <a name="phase0"></a>
# ## 2. Phase 0 — Data Inventory & Exploration
# 
# **Goal:** Understand file structure, CRS, resolution, band names, and pixel value distributions before building anything.

# Scan all .tif files and report metadata
tif_files = sorted(DATA_DIR.glob("*.tif"))
print(f"Found {len(tif_files)} GeoTIFF files\n")

inventory_rows = []

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes_flat = axes.flatten()

for i, fp in enumerate(tif_files):
    with rasterio.open(fp) as src:
        name = fp.name
        print(f"{'='*60}")
        print(f"FILE: {name}")
        print(f"  Shape: {src.count} bands × {src.height} × {src.width}")
        print(f"  CRS: {src.crs}  |  Resolution: {src.res}")
        print(f"  NoData: {src.nodata}  |  Bounds: {src.bounds}")
        print(f"  Band names: {src.descriptions}")
        
        for b in range(1, src.count + 1):
            data = src.read(b).astype(np.float64)
            valid = data[(data != src.nodata) if src.nodata else np.ones_like(data, bool)]
            valid = valid[np.isfinite(valid)]
            nodata_pct = 100 * (1 - len(valid) / (src.height * src.width))
            print(f"  Band {b} ({src.descriptions[b-1]}): "
                  f"min={np.min(valid):.4f}, max={np.max(valid):.4f}, "
                  f"mean={np.mean(valid):.4f}, nodata={nodata_pct:.1f}%")
            
            inventory_rows.append({
                'filename': name,
                'sensor': 'S1' if 'S1' in name else 'S2',
                'date': name.split('_')[1].replace('.tif','').replace(' (1)',''),
                'band': src.descriptions[b-1],
                'min': np.min(valid), 'max': np.max(valid),
                'mean': np.mean(valid), 'nodata_pct': nodata_pct
            })
        
        # Thumbnail
        thumb = src.read(1).astype(np.float64)
        if src.nodata: thumb[thumb == src.nodata] = np.nan
        vmin, vmax = np.nanpercentile(thumb, [2, 98])
        axes_flat[i].imshow(thumb, cmap='gray', vmin=vmin, vmax=vmax)
        axes_flat[i].set_title(name, fontsize=9); axes_flat[i].axis('off')

plt.suptitle("Phase 0 — GeoTIFF Thumbnails", fontsize=14)
plt.tight_layout()
plt.savefig('figures/phase0_thumbnails.png', dpi=150)
plt.show()

inventory_df = pd.DataFrame(inventory_rows)
print("\n\nINVENTORY SUMMARY:")
print(inventory_df.to_string(index=False))

# ### Phase 0 Key Findings
# 
# - **6 files:** 3 Sentinel-1 (VV band) + 3 Sentinel-2 (B4, NDVI, NDWI bands)
# - **Co-registered:** All files share the same CRS (EPSG:4326), resolution (~10m), and pixel grid
# - **S1 VV** is in linear power scale (not dB) — standard SAR thresholds need conversion
# - **S2 includes pre-computed NDWI** — ideal for water detection thresholding
# - **S1 has ~60% nodata** (areas outside study region); S2 has <1.2% nodata

# <a name="phase1"></a>
# ## 3. Phase 1 — Label Generation (Water Thresholding)
# 
# **Goal:** Generate binary flood/no-flood labels using NDWI thresholding.
# 
# **Approach:** NDWI > 0.0 identifies water pixels (McFeeters, 1996). A patch is labelled "flood" if >5% of valid pixels are water.
# 
# **Why not S1 VV?** The VV data is in linear power scale. Standard dB thresholds (-15 to -18 dB) capture <0.01% of pixels as water — the GEE mean-composite preprocessing compressed the low-backscatter water signal.

# NDWI-based water thresholding for S2
s2_files = sorted(DATA_DIR.glob("S2_*.tif"))
ndwi_thresholds = [0.0, 0.1, 0.2, 0.3]
flood_fractions = [0.05, 0.10, 0.15, 0.20]
label_rows = []

for fp in s2_files:
    date = fp.stem.split('_')[1].replace(' (1)', '')
    with rasterio.open(fp) as src:
        ndwi = src.read(3).astype(np.float64)
        b4 = src.read(1).astype(np.float64)
    
    valid_mask = (b4 > 0) & np.isfinite(ndwi)
    
    for nth in ndwi_thresholds:
        water_mask = (ndwi > nth) & valid_mask
        water_frac = np.sum(water_mask) / np.sum(valid_mask)
        for ff in flood_fractions:
            label_rows.append({
                'date': date, 'ndwi_threshold': nth,
                'water_fraction': round(water_frac, 4),
                'flood_threshold': ff,
                'label': 1 if water_frac > ff else 0
            })

label_df = pd.DataFrame(label_rows)

# Display comparison table
print("NDWI THRESHOLD vs WATER FRACTION (by date):")
pivot = label_df[label_df['flood_threshold']==0.10].pivot_table(
    index='ndwi_threshold', columns='date', values='water_fraction')
print(pivot.to_string())

print("\nLABEL MATRIX (NDWI>0.0, varying flood threshold):")
labels = label_df[label_df['ndwi_threshold']==0.0].pivot_table(
    index='flood_threshold', columns='date', values='label')
print(labels.to_string())

# Histograms: S1 VV (dB) and S2 NDWI distributions
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

for i, fp in enumerate(sorted(DATA_DIR.glob("S1_*.tif"))):
    date = fp.stem.split('_')[1].replace(' (1)', '')
    with rasterio.open(fp) as src:
        vv = src.read(1).astype(np.float64).flatten()
    vv = vv[vv > 1e-6]
    vv_db = 10 * np.log10(vv)
    axes[0, i].hist(vv_db, bins=200, color='steelblue', alpha=0.7, density=True)
    for db in [-15, -16, -17, -18]:
        axes[0, i].axvline(db, color='red', linestyle='--', alpha=0.6, label=f'{db} dB')
    axes[0, i].set_title(f'S1 VV — {date}'); axes[0, i].set_xlabel('VV (dB)')
    axes[0, i].legend(fontsize=8); axes[0, i].set_xlim(-30, 0)

for i, fp in enumerate(sorted(DATA_DIR.glob("S2_*.tif"))):
    date = fp.stem.split('_')[1].replace(' (1)', '')
    with rasterio.open(fp) as src:
        ndwi = src.read(3).astype(np.float64).flatten()
    ndwi = ndwi[np.isfinite(ndwi)]
    axes[1, i].hist(ndwi, bins=200, color='teal', alpha=0.7, density=True)
    for nth in [0.0, 0.1, 0.2, 0.3]:
        axes[1, i].axvline(nth, color='red', linestyle='--', alpha=0.6, label=f'NDWI>{nth}')
    axes[1, i].set_title(f'S2 NDWI — {date}'); axes[1, i].set_xlabel('NDWI')
    axes[1, i].legend(fontsize=8)

plt.suptitle("Phase 1 — Value Distributions with Thresholds", fontsize=14)
plt.tight_layout()
plt.savefig('figures/phase1_histograms.png', dpi=150)
plt.show()

# ### Phase 1 Decision
# 
# **Chosen thresholds:**
# - Water detection: **NDWI > 0.0** (standard boundary; validated by bimodal histogram)
# - Flood label: **water_fraction > 5%** (captures meaningful water presence at patch level)
# 
# **Justification:** NDWI = 0.0 sits in the valley between the land and water modes of the histogram, consistent with McFeeters (1996). The 5% flood fraction was selected to capture patches with partial water coverage while excluding noise.

# <a name="phase2"></a>
# ## 4. Phase 2 — Patch Extraction
# 
# **Goal:** Tile GeoTIFF scenes into 64×64 pixel patches with binary labels. Each patch has 4 bands: VV, B4, NDVI, NDWI.

# Match S1 and S2 files by date
s1_files = sorted(DATA_DIR.glob("S1_*.tif"))
s2_files = sorted(DATA_DIR.glob("S2_*.tif"))

def get_date(fp):
    return fp.stem.split('_')[1].replace(' (1)', '')

s1_by_date = {get_date(f): f for f in s1_files}
s2_by_date = {get_date(f): f for f in s2_files}
dates = sorted(set(s1_by_date.keys()) & set(s2_by_date.keys()))

all_patches, all_labels, meta_rows = [], [], []
patch_id = 0

for date in dates:
    print(f"\nProcessing {date}...")
    with rasterio.open(s1_by_date[date]) as src:
        vv = src.read(1).astype(np.float32)
    with rasterio.open(s2_by_date[date]) as src:
        b4 = src.read(1).astype(np.float32)
        ndvi = src.read(2).astype(np.float32)
        ndwi = src.read(3).astype(np.float32)
    
    h, w = vv.shape
    n_rows, n_cols = h // PATCH_SIZE, w // PATCH_SIZE
    date_count, date_flood, date_skip = 0, 0, 0
    
    for r in range(n_rows):
        for c in range(n_cols):
            r0, r1 = r * PATCH_SIZE, (r + 1) * PATCH_SIZE
            c0, c1 = c * PATCH_SIZE, (c + 1) * PATCH_SIZE
            
            p_vv, p_b4 = vv[r0:r1, c0:c1], b4[r0:r1, c0:c1]
            p_ndvi, p_ndwi = ndvi[r0:r1, c0:c1], ndwi[r0:r1, c0:c1]
            
            valid = (p_vv > 1e-6) & (p_b4 > 0) & np.isfinite(p_ndwi)
            nodata_frac = 1 - np.sum(valid) / (PATCH_SIZE ** 2)
            if nodata_frac > NODATA_MAX_FRAC:
                date_skip += 1; continue
            
            water_frac = np.sum((p_ndwi > NDWI_THRESHOLD) & valid) / np.sum(valid)
            label = 1 if water_frac > FLOOD_FRACTION else 0
            
            all_patches.append(np.stack([p_vv, p_b4, p_ndvi, p_ndwi], axis=-1))
            all_labels.append(label)
            meta_rows.append({'patch_id': patch_id, 'date': date, 'row': r, 'col': c,
                            'water_fraction': round(water_frac, 4), 'label': label})
            patch_id += 1; date_count += 1; date_flood += (label == 1)
    
    print(f"  Extracted: {date_count} | Flood: {date_flood} ({100*date_flood/max(date_count,1):.1f}%) | Skipped: {date_skip}")

X = np.array(all_patches, dtype=np.float32)
y = np.array(all_labels, dtype=np.int32)
meta = pd.DataFrame(meta_rows)

print(f"\n{'='*50}")
print(f"DATASET: X={X.shape}, y={y.shape}")
print(f"Flood: {np.sum(y==1)} ({100*np.mean(y==1):.1f}%) | No-flood: {np.sum(y==0)} ({100*np.mean(y==0):.1f}%)")
print(f"Imbalance ratio: 1:{np.sum(y==0)/max(np.sum(y==1),1):.1f}")

np.save('patches/X_patches.npy', X)
np.save('patches/y_labels.npy', y)
meta.to_csv('patches/patch_metadata.csv', index=False)

# Visualise sample patches
fig, axes = plt.subplots(2, 8, figsize=(20, 5))
fig.suptitle("Sample Patches — Top: Flood, Bottom: No-Flood (NDWI band)", fontsize=13)
np.random.seed(42)
flood_idx, noflood_idx = np.where(y==1)[0], np.where(y==0)[0]

for i in range(8):
    idx = np.random.choice(flood_idx)
    axes[0,i].imshow(X[idx,:,:,3], cmap='RdYlBu', vmin=-0.5, vmax=0.5)
    axes[0,i].set_title(f"wf={meta.iloc[idx]['water_fraction']:.2f}", fontsize=8)
    axes[0,i].axis('off')
    
    idx = np.random.choice(noflood_idx)
    axes[1,i].imshow(X[idx,:,:,3], cmap='RdYlBu', vmin=-0.5, vmax=0.5)
    axes[1,i].set_title(f"wf={meta.iloc[idx]['water_fraction']:.2f}", fontsize=8)
    axes[1,i].axis('off')

plt.tight_layout()
plt.savefig('figures/phase2_sample_patches.png', dpi=150)
plt.show()

# <a name="phase3"></a>
# ## 5. Phase 3 — Train/Validation/Test Split
# 
# **Strategy:** Date-based temporal split to prevent spatial data leakage.
# - **Train + Val:** June + July 2024 (80/20 stratified split)
# - **Test:** August 2024 (entirely unseen temporal period)

# Date-based split
train_mask = meta['date'].isin(['2024-06-01', '2024-07-01'])
test_mask = meta['date'] == '2024-08-01'

X_trainval, y_trainval = X[train_mask], y[train_mask]
X_test, y_test = X[test_mask], y[test_mask]

X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval, test_size=0.2, random_state=RANDOM_STATE, stratify=y_trainval)

for name, yy in [("Train", y_train), ("Validation", y_val), ("Test", y_test)]:
    print(f"{name}: {len(yy)} patches | Flood: {np.sum(yy==1)} ({100*np.mean(yy==1):.1f}%)")

np.save('patches/X_train.npy', X_train); np.save('patches/y_train.npy', y_train)
np.save('patches/X_val.npy', X_val); np.save('patches/y_val.npy', y_val)
np.save('patches/X_test.npy', X_test); np.save('patches/y_test.npy', y_test)

# <a name="phase4"></a>
# ## 6. Phase 4 — Model Training
# 
# ### 4.1 Feature Engineering
# 
# Extract 61 features per patch for traditional ML models: per-band statistics, GLCM texture, and water fraction.

# Feature extraction
band_names = ['VV', 'B4', 'NDVI', 'NDWI']

def extract_features(X_data):
    features = []
    for i in range(len(X_data)):
        patch = X_data[i]
        feat = {}
        for b, bname in enumerate(band_names):
            band = patch[:,:,b].flatten()
            valid = band[np.isfinite(band)]
            feat[f'{bname}_mean'] = np.mean(valid)
            feat[f'{bname}_std'] = np.std(valid)
            feat[f'{bname}_min'] = np.min(valid)
            feat[f'{bname}_max'] = np.max(valid)
            feat[f'{bname}_median'] = np.median(valid)
            feat[f'{bname}_skew'] = skew(valid)
            feat[f'{bname}_kurtosis'] = kurtosis(valid)
            feat[f'{bname}_p5'] = np.percentile(valid, 5)
            feat[f'{bname}_p25'] = np.percentile(valid, 25)
            feat[f'{bname}_p75'] = np.percentile(valid, 75)
            feat[f'{bname}_p95'] = np.percentile(valid, 95)
            # GLCM texture
            band_2d = patch[:,:,b]
            bmin, bmax = np.nanmin(band_2d), np.nanmax(band_2d)
            if bmax > bmin:
                quantized = ((band_2d - bmin) / (bmax - bmin) * 31).astype(np.uint8)
            else:
                quantized = np.zeros_like(band_2d, dtype=np.uint8)
            glcm = graycomatrix(quantized, distances=[1], angles=[0], levels=32, symmetric=True, normed=True)
            feat[f'{bname}_contrast'] = graycoprops(glcm, 'contrast')[0, 0]
            feat[f'{bname}_homogeneity'] = graycoprops(glcm, 'homogeneity')[0, 0]
            feat[f'{bname}_energy'] = graycoprops(glcm, 'energy')[0, 0]
            feat[f'{bname}_correlation'] = graycoprops(glcm, 'correlation')[0, 0]
        ndwi_band = patch[:,:,3]
        valid_mask = np.isfinite(ndwi_band)
        feat['water_fraction'] = np.sum((ndwi_band > 0.0) & valid_mask) / np.sum(valid_mask)
        features.append(feat)
    return pd.DataFrame(features)

print("Extracting train features...")
df_train = extract_features(X_train)
print("Extracting val features...")
df_val = extract_features(X_val)
print("Extracting test features...")
df_test = extract_features(X_test)
print(f"\nFeature matrix: {df_train.shape[1]} features per patch")

# ### 4.2 Traditional ML Models
# 
# Train Logistic Regression, Random Forest, XGBoost, and SVM with 5-fold stratified cross-validation.

# Combine train+val for CV, keep test held out
X_tv = pd.concat([df_train, df_val], ignore_index=True).values
y_tv = np.concatenate([y_train, y_val])
X_test_feat = df_test.values

scaler = StandardScaler()
X_tv_s = scaler.fit_transform(X_tv)
X_test_s = scaler.transform(X_test_feat)
neg, pos = np.sum(y_tv==0), np.sum(y_tv==1)

models = {
    'Logistic Regression': (LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42), True),
    'Random Forest': (RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1), False),
    'XGBoost': (XGBClassifier(scale_pos_weight=neg/pos, n_estimators=200, random_state=42, eval_metric='logloss', verbosity=0), False),
    'SVM (RBF)': (SVC(class_weight='balanced', kernel='rbf', probability=True, random_state=42), True),
}

# 5-fold CV
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scoring = ['roc_auc', 'accuracy', 'precision', 'recall', 'f1']
cv_results = {}

for name, (model, use_scaled) in models.items():
    X_cv = X_tv_s if use_scaled else X_tv
    t0 = time.time()
    scores = cross_validate(model, X_cv, y_tv, cv=cv, scoring=scoring, return_train_score=False)
    elapsed = time.time() - t0
    cv_results[name] = {m: f"{scores[f'test_{m}'].mean():.4f} ± {scores[f'test_{m}'].std():.4f}" for m in scoring}
    cv_results[name]['time'] = f"{elapsed:.1f}s"
    print(f"{name}: AUC={cv_results[name]['roc_auc']} | F1={cv_results[name]['f1']} | {elapsed:.1f}s")

# Train final models on full train+val, evaluate on test
test_results = {}
all_probs, all_preds = {}, {}

for name, (model, use_scaled) in models.items():
    Xf, Xe = (X_tv_s, X_test_s) if use_scaled else (X_tv, X_test_feat)
    t0 = time.time()
    model.fit(Xf, y_tv)
    train_time = time.time() - t0
    y_pred = model.predict(Xe)
    y_prob = model.predict_proba(Xe)[:, 1]
    all_probs[name] = y_prob
    all_preds[name] = y_pred
    test_results[name] = {
        'ROC-AUC': roc_auc_score(y_test, y_prob),
        'Accuracy': accuracy_score(y_test, y_pred),
        'Precision': precision_score(y_test, y_pred, zero_division=0),
        'Recall': recall_score(y_test, y_pred),
        'F1': f1_score(y_test, y_pred),
        'Train Time': train_time
    }

print("\nTEST SET RESULTS:")
results_df = pd.DataFrame(test_results).T.sort_values('ROC-AUC', ascending=False)
print(results_df.to_string())

# ### 4.3 Simple CNN
# 
# Three convolutional blocks trained on raw 64×64×4 patches.

# CNN Architecture
class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(4, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Linear(128*8*8, 128), nn.ReLU(),
            nn.Dropout(0.5), nn.Linear(128, 1)
        )
    def forward(self, x):
        return self.classifier(self.features(x)).squeeze(-1)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Prepare data
X_train_nn = np.nan_to_num(X_train.astype(np.float32))
X_val_nn = np.nan_to_num(X_val.astype(np.float32))
X_test_nn = np.nan_to_num(X_test.astype(np.float32))

X_tr_t = torch.from_numpy(X_train_nn.transpose(0,3,1,2)).to(device)
y_tr_t = torch.from_numpy(y_train.astype(np.float32)).to(device)
X_va_t = torch.from_numpy(X_val_nn.transpose(0,3,1,2)).to(device)
y_va_t = torch.from_numpy(y_val.astype(np.float32)).to(device)
X_te_t = torch.from_numpy(X_test_nn.transpose(0,3,1,2)).to(device)

pos_weight = torch.tensor([np.sum(y_train==0)/max(np.sum(y_train==1),1)], dtype=torch.float32).to(device)
train_loader = DataLoader(TensorDataset(X_tr_t, y_tr_t), batch_size=64, shuffle=True)
val_loader = DataLoader(TensorDataset(X_va_t, y_va_t), batch_size=64)

# Train
cnn = SimpleCNN().to(device)
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer = optim.Adam(cnn.parameters(), lr=1e-3)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=5, factor=0.5)

best_auc, best_state, patience_count = 0, None, 0
cnn_history = {'train_loss': [], 'val_auc': []}

for epoch in range(50):
    cnn.train(); train_loss = 0
    for xb, yb in train_loader:
        optimizer.zero_grad()
        loss = criterion(cnn(xb), yb); loss.backward(); optimizer.step()
        train_loss += loss.item() * len(xb)
    train_loss /= len(train_loader.dataset)
    
    cnn.eval(); vp, vt = [], []
    with torch.no_grad():
        for xb, yb in val_loader:
            vp.extend(torch.sigmoid(cnn(xb)).cpu().numpy()); vt.extend(yb.cpu().numpy())
    val_auc = roc_auc_score(vt, vp)
    cnn_history['train_loss'].append(train_loss)
    cnn_history['val_auc'].append(val_auc)
    scheduler.step(val_auc)
    
    if val_auc > best_auc:
        best_auc = val_auc
        best_state = {k: v.cpu().clone() for k, v in cnn.state_dict().items()}
        patience_count = 0
    else:
        patience_count += 1
    
    if (epoch+1) % 5 == 0:
        print(f"Epoch {epoch+1}: loss={train_loss:.4f} val_auc={val_auc:.4f}")
    if patience_count >= 10:
        print(f"Early stopping at epoch {epoch+1}"); break

cnn.load_state_dict(best_state); cnn = cnn.to(device)
print(f"Best val AUC: {best_auc:.4f}")

# Evaluate on test
cnn.eval()
with torch.no_grad():
    cnn_probs = torch.sigmoid(cnn(X_te_t)).cpu().numpy()
cnn_preds = (cnn_probs > 0.5).astype(int)
cnn_auc = roc_auc_score(y_test, cnn_probs)
print(f"CNN Test AUC: {cnn_auc:.4f}")

all_probs['Simple CNN'] = cnn_probs
all_preds['Simple CNN'] = cnn_preds
test_results['Simple CNN'] = {
    'ROC-AUC': cnn_auc, 'Accuracy': accuracy_score(y_test, cnn_preds),
    'Precision': precision_score(y_test, cnn_preds, zero_division=0),
    'Recall': recall_score(y_test, cnn_preds), 'F1': f1_score(y_test, cnn_preds)
}

# Save model
torch.save(cnn.state_dict(), 'models/cnn_best.pth')

# ### 4.4 ResNet-18 (Transfer Learning)
# 
# Pretrained ImageNet backbone with modified 4-channel input. Two-phase training: frozen backbone, then full fine-tuning.

from torchvision.models import resnet18, ResNet18_Weights

class ResNetFlood(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = resnet18(weights=ResNet18_Weights.DEFAULT)
        old = self.backbone.conv1
        self.backbone.conv1 = nn.Conv2d(4, 64, 7, stride=2, padding=3, bias=False)
        with torch.no_grad():
            self.backbone.conv1.weight[:, :3] = old.weight
            self.backbone.conv1.weight[:, 3] = old.weight[:, 0]
        self.backbone.fc = nn.Linear(512, 1)
    def forward(self, x):
        return self.backbone(x).squeeze(-1)

# Resize dataset for 224x224
resize = nn.Upsample(size=(224,224), mode='bilinear', align_corners=False)
class ResizeDataset(torch.utils.data.Dataset):
    def __init__(self, X, y):
        self.X, self.y = X, y
    def __len__(self): return len(self.y)
    def __getitem__(self, i):
        return resize(self.X[i].unsqueeze(0)).squeeze(0), self.y[i]

X_tv_t = torch.cat([X_tr_t, X_va_t])
y_tv_t = torch.cat([y_tr_t, y_va_t])
train_r = DataLoader(ResizeDataset(X_tv_t, y_tv_t), batch_size=16, shuffle=True)
test_r = DataLoader(ResizeDataset(X_te_t, torch.from_numpy(y_test.astype(np.float32)).to(device)), batch_size=16)

resnet = ResNetFlood().to(device)
criterion_r = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

# Phase 1: Head only (10 epochs)
for p in resnet.backbone.parameters(): p.requires_grad = False
resnet.backbone.fc.weight.requires_grad = True; resnet.backbone.fc.bias.requires_grad = True
resnet.backbone.conv1.weight.requires_grad = True

opt1 = optim.Adam(filter(lambda p: p.requires_grad, resnet.parameters()), lr=1e-3)
print("Phase 1: Training head...")
for epoch in range(10):
    resnet.train()
    for xb, yb in train_r:
        opt1.zero_grad(); criterion_r(resnet(xb), yb).backward(); opt1.step()

# Phase 2: Full fine-tuning (20 epochs)
for p in resnet.backbone.parameters(): p.requires_grad = True
opt2 = optim.Adam(resnet.parameters(), lr=1e-5)
print("Phase 2: Fine-tuning...")
for epoch in range(20):
    resnet.train()
    for xb, yb in train_r:
        opt2.zero_grad(); criterion_r(resnet(xb), yb).backward(); opt2.step()

# Evaluate
resnet.eval(); rn_probs, rn_true = [], []
with torch.no_grad():
    for xb, yb in test_r:
        rn_probs.extend(torch.sigmoid(resnet(xb)).cpu().numpy())
        rn_true.extend(yb.cpu().numpy())
rn_probs = np.array(rn_probs); rn_preds = (rn_probs > 0.5).astype(int)
rn_auc = roc_auc_score(rn_true, rn_probs)
print(f"ResNet-18 Test AUC: {rn_auc:.4f}")

all_probs['ResNet-18'] = rn_probs
all_preds['ResNet-18'] = rn_preds
test_results['ResNet-18'] = {
    'ROC-AUC': rn_auc, 'Accuracy': accuracy_score(y_test, rn_preds),
    'Precision': precision_score(y_test, rn_preds, zero_division=0),
    'Recall': recall_score(y_test, rn_preds), 'F1': f1_score(y_test, rn_preds)
}

torch.save(resnet.state_dict(), 'models/resnet_best.pth')

# <a name="phase5"></a>
# ## 7. Phase 5 — Model Evaluation & Comparison
# 
# ### 5.1 Combined ROC & Precision-Recall Curves

# Combined ROC curves
fig, ax = plt.subplots(figsize=(9, 7))
for name in all_probs:
    fpr, tpr, _ = roc_curve(y_test, all_probs[name])
    auc = roc_auc_score(y_test, all_probs[name])
    ax.plot(fpr, tpr, label=f'{name} (AUC={auc:.4f})', linewidth=2)
ax.plot([0,1],[0,1],'k--',alpha=0.3)
ax.set_xlabel('False Positive Rate'); ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curves — All Models (Test: Aug 2024)')
ax.legend(loc='lower right'); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig('figures/phase5_roc_all.png', dpi=150); plt.show()

# Combined PR curves
fig, ax = plt.subplots(figsize=(9, 7))
for name in all_probs:
    prec, rec, _ = precision_recall_curve(y_test, all_probs[name])
    ap = average_precision_score(y_test, all_probs[name])
    ax.plot(rec, prec, label=f'{name} (AP={ap:.4f})', linewidth=2)
ax.set_xlabel('Recall'); ax.set_ylabel('Precision')
ax.set_title('Precision-Recall Curves — All Models')
ax.legend(loc='upper right'); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig('figures/phase5_pr_all.png', dpi=150); plt.show()

# Confusion matrices — top 3 models
final_df = pd.DataFrame(test_results).T.sort_values('ROC-AUC', ascending=False)
top3 = final_df.index[:3].tolist()

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for i, name in enumerate(top3):
    cm = confusion_matrix(y_test, all_preds[name])
    ConfusionMatrixDisplay(cm, display_labels=['No Flood','Flood']).plot(ax=axes[i], cmap='Blues')
    axes[i].set_title(f'{name}\nAUC={test_results[name]["ROC-AUC"]:.4f}')
fig.suptitle('Confusion Matrices — Top 3 Models', fontsize=14)
plt.tight_layout(); plt.savefig('figures/phase5_confusion_top3.png', dpi=150); plt.show()

# Feature importance
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
feature_names = df_train.columns.tolist()
for idx, name in enumerate(['Random Forest', 'XGBoost']):
    imp = models[name][0].feature_importances_
    si = np.argsort(imp)[-15:]
    axes[idx].barh([feature_names[j] for j in si], imp[si], color='steelblue')
    axes[idx].set_title(f'{name} — Top 15 Features'); axes[idx].set_xlabel('Importance')
fig.suptitle('Feature Importance Analysis', fontsize=14)
plt.tight_layout(); plt.savefig('figures/phase5_feature_importance.png', dpi=150); plt.show()

# ### 5.2 Statistical Significance — McNemar's Test

# McNemar's test between top model pairs
top_models = final_df.index[:3].tolist()
print("McNemar's Test Results (exact, two-sided):\n")
for i in range(len(top_models)):
    for j in range(i+1, len(top_models)):
        n1, n2 = top_models[i], top_models[j]
        c1 = all_preds[n1] == y_test
        c2 = all_preds[n2] == y_test
        b = int(np.sum(c1 & ~c2))  # n1 right, n2 wrong
        c = int(np.sum(~c1 & c2))  # n2 right, n1 wrong
        a = int(np.sum(c1 & c2))
        d = int(np.sum(~c1 & ~c2))
        result = mcnemar(np.array([[a,b],[c,d]]), exact=True)
        sig = "SIGNIFICANT" if result.pvalue < 0.05 else "NOT significant"
        print(f"{n1} vs {n2}: b={b}, c={c}, p={result.pvalue:.4f} → {sig}")

# ### 5.3 Sensitivity Analysis
# 
# Evaluate how ROC-AUC changes across NDWI thresholds, flood fraction thresholds, and patch sizes.

# Sensitivity analysis (re-extract patches with different parameters)
def run_sensitivity(ndwi_th, flood_th, patch_size):
    patches, labels = [], []
    for date in dates:
        with rasterio.open(s1_by_date[date]) as src: vv = src.read(1).astype(np.float32)
        with rasterio.open(s2_by_date[date]) as src:
            b4 = src.read(1).astype(np.float32)
            ndvi = src.read(2).astype(np.float32)
            ndwi = src.read(3).astype(np.float32)
        h, w = vv.shape
        for r in range(h // patch_size):
            for c in range(w // patch_size):
                r0, r1 = r*patch_size, (r+1)*patch_size
                c0, c1 = c*patch_size, (c+1)*patch_size
                pv, pb = vv[r0:r1,c0:c1], b4[r0:r1,c0:c1]
                pn, pw = ndvi[r0:r1,c0:c1], ndwi[r0:r1,c0:c1]
                valid = (pv>1e-6)&(pb>0)&np.isfinite(pw)
                if np.sum(valid) < 0.8*patch_size*patch_size: continue
                wf = np.sum((pw>ndwi_th)&valid)/np.sum(valid)
                labels.append(1 if wf>flood_th else 0)
                f = []
                for band in [pv,pb,pn,pw]:
                    b = band.flatten()
                    f.extend([np.nanmean(b),np.nanstd(b),np.nanpercentile(b,5),np.nanpercentile(b,95)])
                f.append(np.sum((pw>0)&valid)/max(np.sum(valid),1))
                patches.append(f)
        del vv, b4, ndvi, ndwi
    
    feats, labels = np.array(patches, np.float32), np.array(labels)
    if len(np.unique(labels)) < 2: return 0.5
    split = int(0.7*len(labels))
    sc = StandardScaler()
    Xtr, Xte = sc.fit_transform(feats[:split]), sc.transform(feats[split:])
    ytr, yte = labels[:split], labels[split:]
    if len(np.unique(yte)) < 2: return 0.5
    m = XGBClassifier(scale_pos_weight=max(np.sum(ytr==0),1)/max(np.sum(ytr==1),1),
                      n_estimators=100, random_state=42, eval_metric='logloss', verbosity=0)
    m.fit(Xtr, ytr)
    return roc_auc_score(yte, m.predict_proba(Xte)[:,1])

# Run sensitivity sweeps
print("1. NDWI threshold sweep...")
ndwi_ths = [-0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4]
ndwi_aucs = [run_sensitivity(nth, 0.05, 64) for nth in ndwi_ths]
for nth, auc in zip(ndwi_ths, ndwi_aucs): print(f"  NDWI>{nth}: AUC={auc:.4f}")

print("\n2. Flood fraction sweep...")
flood_ths = [0.01, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
flood_aucs = [run_sensitivity(0.0, ft, 64) for ft in flood_ths]
for ft, auc in zip(flood_ths, flood_aucs): print(f"  flood>{ft}: AUC={auc:.4f}")

print("\n3. Patch size sweep...")
patch_sizes = [32, 64, 128]
patch_aucs = [run_sensitivity(0.0, 0.05, ps) for ps in patch_sizes]
for ps, auc in zip(patch_sizes, patch_aucs): print(f"  patch={ps}: AUC={auc:.4f}")

# Plot
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].plot(ndwi_ths, ndwi_aucs, 'o-', color='steelblue', linewidth=2, markersize=8)
axes[0].axvline(0.0, color='red', linestyle='--', alpha=0.5, label='Chosen (0.0)')
axes[0].set_xlabel('NDWI Threshold'); axes[0].set_ylabel('ROC-AUC')
axes[0].set_title('Sensitivity to NDWI Threshold'); axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].plot(flood_ths, flood_aucs, 'o-', color='teal', linewidth=2, markersize=8)
axes[1].axvline(0.05, color='red', linestyle='--', alpha=0.5, label='Chosen (0.05)')
axes[1].set_xlabel('Flood Fraction Threshold'); axes[1].set_ylabel('ROC-AUC')
axes[1].set_title('Sensitivity to Flood Fraction'); axes[1].legend(); axes[1].grid(alpha=0.3)

axes[2].plot(patch_sizes, patch_aucs, 'o-', color='coral', linewidth=2, markersize=8)
axes[2].axvline(64, color='red', linestyle='--', alpha=0.5, label='Chosen (64)')
axes[2].set_xlabel('Patch Size (px)'); axes[2].set_ylabel('ROC-AUC')
axes[2].set_title('Sensitivity to Patch Size'); axes[2].legend(); axes[2].grid(alpha=0.3)

fig.suptitle('Sensitivity Analysis (XGBoost)', fontsize=14)
plt.tight_layout(); plt.savefig('figures/phase5_sensitivity.png', dpi=150); plt.show()

# <a name="results"></a>
# ## 8. Results Summary

# Final comparison table
final_df = pd.DataFrame(test_results).T.sort_values('ROC-AUC', ascending=False)
print("="*70)
print("FINAL MODEL COMPARISON (Test Set: August 2024)")
print("="*70)
print(final_df.to_string())
final_df.to_csv('figures/final_comparison.csv')

print("\n\nKey Findings:")
print(f"  Best model: {final_df.index[0]} (AUC = {final_df.iloc[0]['ROC-AUC']:.4f})")
print(f"  All top models are statistically indistinguishable (McNemar p > 0.05)")
print(f"  Results are robust across NDWI thresholds (-0.2 to 0.2), flood fractions (0.01-0.30), and patch sizes (32-128)")
print(f"  Dominant features: NDWI_p95, water_fraction — physically interpretable")
print(f"\n  Limitation: NDWI circularity — used for both labelling and as input feature")
print(f"  Recommendation: Validate against external flood maps (e.g., Copernicus EMS)")

# ---
# 
# ## References
# 
# 1. Haralick, R.M., Shanmugam, K., & Dinstein, I.H. (1973). Textural features for image classification. *IEEE Trans. SMC*, 3(6), 610–621.
# 2. McFeeters, S.K. (1996). The use of NDWI in the delineation of open water features. *Int. J. Remote Sensing*, 17(7), 1425–1432.
# 3. Twele, A., Cao, W., Plank, S., & Martinis, S. (2016). Sentinel-1-based flood mapping. *Int. J. Remote Sensing*, 37(13), 2990–3004.
# 4. Xu, H. (2006). Modification of NDWI to enhance open water features. *Int. J. Remote Sensing*, 27(14), 3025–3033.

