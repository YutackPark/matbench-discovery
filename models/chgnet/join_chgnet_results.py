"""Concatenate CHGNet results from multiple data files generated by slurm job array
into single file.
"""


# %%
from __future__ import annotations

import os
from glob import glob

import pandas as pd
from pymatviz import density_scatter
from tqdm import tqdm

from matbench_discovery import formula_col, id_col
from matbench_discovery.data import as_dict_handler
from matbench_discovery.energy import get_e_form_per_atom
from matbench_discovery.preds import df_preds, e_form_col

__author__ = "Janosh Riebesell"
__date__ = "2023-03-01"


# %%
module_dir = os.path.dirname(__file__)
task_type = "IS2RE"
date = "2023-10-23"
glob_pattern = f"{date}-chgnet-wbm-{task_type}*/*.json.gz"
file_paths = sorted(glob(f"{module_dir}/{glob_pattern}"))
print(f"Found {len(file_paths):,} files for {glob_pattern = }")

dfs: dict[str, pd.DataFrame] = {}


# %%
failed = {}
for file_path in tqdm(file_paths):
    if file_path in dfs:
        continue
    try:
        df = pd.read_json(file_path).set_index(id_col)
    except Exception as exc:
        failed[file_path] = str(exc)
        continue
    # drop trajectory to save memory
    dfs[file_path] = df.drop(columns="chgnet_trajectory", errors="ignore")


print(f"{pd.Series(failed).value_counts()=}")

df_chgnet = pd.concat(dfs.values()).round(4)


# %% compute corrected formation energies
e_pred_col = "chgnet_energy"
e_form_chgnet_col = f"e_form_per_atom_{e_pred_col.split('_energy')[0]}"
df_chgnet[formula_col] = df_preds[formula_col]
df_chgnet[e_form_chgnet_col] = [
    get_e_form_per_atom(dict(energy=ene, composition=formula))
    for formula, ene in tqdm(
        df_chgnet.set_index(formula_col)[e_pred_col].items(), total=len(df_chgnet)
    )
]
df_preds[e_form_chgnet_col] = df_chgnet[e_form_chgnet_col]


# %%
ax = density_scatter(df=df_preds, x=e_form_col, y=e_form_chgnet_col)


# %%
out_path = file_paths[0].rsplit("/", 1)[0]
df_chgnet = df_chgnet.round(4)
df_chgnet.select_dtypes("number").to_csv(f"{out_path}.csv.gz")
df_chgnet.reset_index().to_json(f"{out_path}.json.gz", default_handler=as_dict_handler)

# in_path = f"{module_dir}/2023-03-04-chgnet-wbm-IS2RE"
# df_chgnet = pd.read_csv(f"{in_path}.csv.gz").set_index(id_col)
# df_chgnet = pd.read_json(f"{in_path}.json.gz").set_index(id_col)
