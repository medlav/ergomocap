# ---
# project: ErgoMoCap
# file: calculators.py
# author: medlav
# created: 2026-05-19
# license: AGPL-3.0
# ---
# Copyright (C) 2026 medlav
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the representation of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from calculators.adapters.freemocap_adapter import (
    map_fmc_joint_angles_to_ergo_degs,
    map_fmc_kinematics_to_niosh_vars,
    map_fmc_kinematics_to_ocra_vars,
    map_fmc_kinematics_to_ewas_vars,
    map_fmc_kinematics_to_snook_vars,
)

# 2. Import from the specific calculators
from calculators.reba_calculator.REBA_calculator import calculate_frame_reba_from_degs
from calculators.rula_calculator.RULA_calculator import calculate_frame_rula_from_degs
from calculators.niosh_calculator.NIOSH_calculator import (
    calculate_frame_niosh_li,
)  # TODO all niosh_calculator/ code and relative adapter/ is to be done
from calculators.ocra_calculator.OCRA_calculator import (
    calculate_frame_ocra_index,
)  # TODO all ocra_calculator/ code and relative adapter/ is to be done
from calculators.ewas_calculator.EWAS_calculator import (
    calculate_frame_ewas_score,
)  # TODO all ewas_calculator/ code and relative adapter/ is to be done
from calculators.snook_calculator.SNOOK_calculator import (
    calculate_frame_snook_index,
)  # TODO all snook_calculator/ code and relative adapter/ is to be done


# 3. Define __all__ to control what is exported and help Pylance/Intellisense
__all__ = [
    "map_fmc_joint_angles_to_ergo_degs",
    "map_fmc_joint_angles_to_ergo_degs",
    "map_fmc_kinematics_to_niosh_vars",  # TODO all niosh_calculator/ code and relative adapter/ is to be done
    "map_fmc_kinematics_to_ocra_vars",  # TODO all ocra_calculator/ code and relative adapter/ is to be done
    "map_fmc_kinematics_to_ewas_vars",  # TODO all ewas_calculator/ code and relative adapter/ is to be done
    "map_fmc_kinematics_to_snook_vars",  # TODO all snook_calculator/ code and relative adapter/ is to be done
    "calculate_frame_reba_from_degs",
    "calculate_frame_rula_from_degs",
    "calculate_frame_niosh_li",  # TODO all niosh_calculator/ code and relative adapter/ is to be done
    "calculate_frame_ocra_index",  # TODO all ocra_calculator/ code and relative adapter/ is to be done
    "calculate_frame_ewas_score",  # TODO all ewas_calculator/ code and relative adapter/ is to be done
    "calculate_frame_snook_index",  # TODO all snook_calculator/ code and relative adapter/ is to be done
]
