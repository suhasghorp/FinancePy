##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

from enum import Enum

from ..utils.error import FinError

########################################################################################


class CompoundingTypes(Enum):
    """Enumeration of compounding types."""

    ZERO = -1
    SIMPLE = 0
    ANNUAL = 1
    SEMI_ANNUAL = 2
    TRI_ANNUAL = 3
    QUARTERLY = 4
    MONTHLY = 12
    CONTINUOUS = 99


########################################################################################

def annual_frequency(freq_type: CompoundingTypes) -> float:
    """
    Return the number of payment periods per year for a given FrequencyType.
    CONTINUOUS returns -1. ZERO returns 1 (to avoid division by zero).
    """
    if not isinstance(freq_type, CompoundingTypes):
        print("FinFrequency:", freq_type)
        raise FinError("Unknown frequency type")

    if freq_type == CompoundingTypes.CONTINUOUS:
        return -1.0
    if freq_type == CompoundingTypes.SIMPLE:  # THE RETURN VALUE IS NEVER USED
        return -99
    if freq_type == CompoundingTypes.ZERO:
        return 1.0
    if freq_type == CompoundingTypes.ANNUAL:
        return 1.0
    if freq_type == CompoundingTypes.SEMI_ANNUAL:
        return 2.0
    if freq_type == CompoundingTypes.TRI_ANNUAL:
        return 3.0
    if freq_type == CompoundingTypes.QUARTERLY:
        return 4.0
    if freq_type == CompoundingTypes.MONTHLY:
        return 12.0

    raise FinError("Invalid compounding frequency type")


########################################################################################
