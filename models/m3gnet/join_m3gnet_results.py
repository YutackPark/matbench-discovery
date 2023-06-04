"""Concatenate M3GNet results from multiple data files generated by slurm job array
into single file.
"""


# %%
from __future__ import annotations

import os
import warnings
from glob import glob
from typing import Literal

import pandas as pd
from pymatgen.core import Structure
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from pymatgen.entries.computed_entries import ComputedStructureEntry
from tqdm import tqdm

from matbench_discovery import today
from matbench_discovery.data import DATA_FILES, as_dict_handler
from matbench_discovery.energy import get_e_form_per_atom

__author__ = "Janosh Riebesell"
__date__ = "2022-08-16"

warnings.filterwarnings(action="ignore", category=UserWarning, module="pymatgen")


# %%
module_dir = os.path.dirname(__file__)
task_type = "IS2RE"
date = "2023-05-30"
# direct: cluster sampling, ms: manual sampling
model_type: Literal["orig", "direct", "ms"] = "ms"
glob_pattern = f"{date}-m3gnet-{model_type}-wbm-{task_type}/*.json.gz"
file_paths = sorted(glob(f"{module_dir}/{glob_pattern}"))
struct_col = "m3gnet_structure"
print(f"Found {len(file_paths):,} files for {glob_pattern = }")

# prevent accidental overwrites
if "dfs" not in locals():
    dfs: dict[str, pd.DataFrame] = {}


# %%
for file_path in tqdm(file_paths):
    if file_path in dfs:
        continue
    df = pd.read_json(file_path).set_index("material_id")
    # drop trajectory to save memory
    dfs[file_path] = df.drop(columns="m3gnet_trajectory")

df_m3gnet = pd.concat(dfs.values()).round(4)


# %%
df_cse = pd.read_json(DATA_FILES.wbm_computed_structure_entries).set_index(
    "material_id"
)

df_cse["cse"] = [
    ComputedStructureEntry.from_dict(x) for x in tqdm(df_cse.computed_structure_entry)
]


# %% transfer M3GNet energies and relaxed structures WBM CSEs since MP2020 energy
# corrections applied below are structure-dependent (for oxides and sulfides)
cse: ComputedStructureEntry
for row in tqdm(df_m3gnet.itertuples(), total=len(df_m3gnet)):
    mat_id, struct_dict, m3gnet_energy, *_ = row
    m3gnet_struct = Structure.from_dict(struct_dict)
    df_m3gnet.at[mat_id, struct_col] = m3gnet_struct  # noqa: PD008
    cse = df_cse.loc[mat_id, "cse"]
    cse._energy = m3gnet_energy  # cse._energy is the uncorrected energy
    cse._structure = m3gnet_struct
    df_m3gnet.loc[mat_id, "cse"] = cse


# %% apply energy corrections
out = MaterialsProject2020Compatibility().process_entries(
    df_m3gnet.cse, verbose=True, clean=True
)
assert len(out) == len(df_m3gnet)


# %% compute corrected formation energies
df_m3gnet["e_form_per_atom_m3gnet"] = [
    get_e_form_per_atom(cse) for cse in tqdm(df_m3gnet.cse)
]


# %%
out_path = f"{module_dir}/{today}-m3gnet-{model_type}-wbm-{task_type}"
df_m3gnet = df_m3gnet.round(4)
df_m3gnet.select_dtypes("number").to_csv(f"{out_path}.csv.gz")
df_m3gnet.reset_index().to_json(f"{out_path}.json.gz", default_handler=as_dict_handler)


# in_path = f"{module_dir}/2022-10-31-m3gnet-wbm-IS2RE.json.gz"
# df_m3gnet = pd.read_csv(in_path.replace(".json.gz", ".csv")).set_index("material_id")
# df_m3gnet = pd.read_json(in_path).set_index("material_id")
