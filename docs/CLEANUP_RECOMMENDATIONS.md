# Repository Cleanup Recommendations

**Date**: November 24, 2025
**Purpose**: Streamline codebase for team collaboration and presentation

---

## Files to Archive (Not Delete)

### Create `archive/` directory and move:

```bash
mkdir archive
mkdir archive/src_eda
mkdir archive/notebooks_experimental

# Move EDA-only src modules (keep for reference but not active)
cp src/data_processing.py archive/src_eda/        # 212 LOC - Kaggle CSV processing
cp src/visualization.py archive/src_eda/          # 235 LOC - Matplotlib plots

# Move experimental notebook
mv notebooks/onetimeusertest.ipynb archive/notebooks_experimental/  # 345KB - appears abandoned
```

### Add README to archive:
```markdown
# Archive Directory

These files are preserved for reference but are NOT part of the active application.

- `src_eda/`: Original Phase 1 EDA modules (used by notebooks)
- `notebooks_experimental/`: Experimental notebooks not needed for presentation
```

---

## Files to Keep But Clarify

### 1. Add header comments to clarify purpose:

**src/data_processing.py**:
```python
"""
EDA DATA PROCESSING MODULE - FOR NOTEBOOK ANALYSIS ONLY

This module is used by notebooks/01_Phase1_EDA.ipynb for offline Kaggle dataset analysis.
For live dashboard data processing, see: app/func/data_processing.py

Status: LEGACY - Kept for notebook compatibility
"""
```

**src/visualization.py**:
```python
"""
EDA VISUALIZATION MODULE - FOR NOTEBOOK ANALYSIS ONLY

This module provides Matplotlib/Seaborn plots for Jupyter notebooks.
For dashboard visualizations, see: app/func/visualizations.py (Plotly-based)

Status: LEGACY - Kept for notebook compatibility
"""
```

---

## Code Duplication Resolution

### Keep Both But Document:

| EDA/Notebook Version | Live Dashboard Version | Action |
|---------------------|------------------------|--------|
| `src/data_processing.py` | `app/func/data_processing.py` | Add clarifying headers |
| `src/visualization.py` | `app/func/visualizations.py` | Add clarifying headers |
| `src/feature_engineering.py` | Used by both | KEEP AS IS - Active |

**Rationale**: They serve different purposes (static analysis vs live data) and removing would break notebooks.

---

## Directory Structure Cleanup

### Remove Empty/Unused Directories:

```bash
# Check if these are empty and remove if so:
rmdir scripts/          # Mentioned in docs but never created
rmdir outputs/figures/  # Empty
rmdir outputs/reports/  # Empty
```

### Keep These Empty Directories:
- `models/` - Will be used for ML demo
- `tests/` - Should add tests before presentation

---

## Documentation Updates

### 1. Update CLAUDE.md:

Remove references to non-existent `scripts/` directory:
```markdown
# OLD (lines mentioning planned scripts)
- scripts/spotify_auth.py
- scripts/collect_spotify_data.py

# NEW
Note: Data collection is integrated into app/func/data_collection.py
```

### 2. Create MODULE_MAP.md:

```markdown
# Module Purpose Map

## Active Dashboard Modules (app/func/)
- auth.py - Spotify OAuth
- page_auth.py - Multi-page authentication
- data_fetching.py - API calls
- data_collection.py - Snapshot orchestration
- s3_storage.py - R2 storage
- dashboard_helpers.py - Load snapshots
- data_processing.py - API data transformation
- visualizations.py - Plotly charts
- datetime_utils.py - Temporal features
- ui_components.py - Styling

## EDA/Notebook Modules (src/)
- feature_engineering.py - ACTIVE: Used by dashboard
- data_processing.py - LEGACY: Notebook-only
- visualization.py - LEGACY: Notebook-only
```

---

## Import Cleanup

### Remove unused imports:

**app/func/data_processing.py**:
```python
# Remove these unused imports:
# import numpy as np  # Line 1 - never used
# from pathlib import Path  # Line 3 - never used
```

---

## Quick Cleanup Script

```bash
#!/bin/bash
# cleanup.sh - Run this to clean up the repo

echo "Creating archive directory..."
mkdir -p archive/src_eda archive/notebooks_experimental

echo "Archiving EDA-only files..."
cp src/data_processing.py archive/src_eda/
cp src/visualization.py archive/src_eda/
mv notebooks/onetimeusertest.ipynb archive/notebooks_experimental/ 2>/dev/null || true

echo "Adding clarifying headers..."
# Add headers to files (would need sed commands)

echo "Removing empty directories..."
rmdir scripts outputs/figures outputs/reports 2>/dev/null || true

echo "Creating documentation..."
cat > archive/README.md << 'EOF'
# Archive Directory
These files are preserved for reference but are NOT part of the active application.
EOF

echo "Cleanup complete!"
echo "Remember to:"
echo "1. Review changes before committing"
echo "2. Update CLAUDE.md to remove scripts/ references"
echo "3. Add MODULE_MAP.md for clarity"
```

---

## Priority Order

1. **HIGH**: Fix Deep User page loading issue (#11)
2. **MEDIUM**: Archive `onetimeusertest.ipynb`
3. **LOW**: Add clarifying headers to src/ modules
4. **LOW**: Remove unused imports
5. **OPTIONAL**: Create MODULE_MAP.md

---

## What NOT to Change

**Do not modify these working modules:**
- ✅ All `app/func/*.py` files (except unused imports)
- ✅ All `app/pages/*.py` files
- ✅ `src/feature_engineering.py` (actively used)
- ✅ OAuth flow (`auth.py`, `page_auth.py`)
- ✅ R2 storage (`s3_storage.py`)

---

## Summary

Your codebase is actually very clean! Only minor cleanup needed:
- Archive one experimental notebook
- Add clarifying comments to distinguish EDA vs live code
- Remove a few unused imports
- Document the module purposes

The architecture is solid and ready for presentation. Focus on adding features, not restructuring!