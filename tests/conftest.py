from __future__ import annotations

import pandas as pd
import pytest
from pymatgen.core import Lattice, Structure
from pymatgen.entries.computed_entries import ComputedStructureEntry


@pytest.fixture
def dummy_df_with_structures(dummy_struct: Structure) -> pd.DataFrame:
    # create a dummy df with a structure column
    df = pd.DataFrame(dict(material_id=range(10), structure=[dummy_struct] * 10))
    df["volume"] = [x.volume for x in df.structure]
    df["computed_structure_entry"] = [ComputedStructureEntry(dummy_struct, 0)] * 10
    return df


@pytest.fixture
def dummy_struct() -> Structure:
    return Structure(
        lattice=Lattice.cubic(5),
        species=("Fe", "O"),
        coords=((0, 0, 0), (0.5, 0.5, 0.5)),
    )
