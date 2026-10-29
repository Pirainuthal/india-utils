"""GST state / union-territory codes (the first two digits of a GSTIN).

The list follows the GST state code table published by GSTN and reproduced
by GST software vendors. Codes 25 and 28 are kept as *legacy* codes: 25 was
Daman and Diu until it merged with Dadra and Nagar Haveli (code 26) in 2020,
and 28 is the pre-2014 code of undivided Andhra Pradesh (GST uses 37).
"""

from __future__ import annotations

__all__ = ["LEGACY_STATE_CODES", "STATE_CODES", "state_name"]

STATE_CODES: dict[str, str] = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "97": "Other Territory",
}

LEGACY_STATE_CODES: dict[str, str] = {
    "25": "Daman and Diu (merged into 26 in 2020)",
    "28": "Andhra Pradesh (pre-bifurcation code)",
}


def state_name(code: str, *, allow_legacy: bool = False) -> str | None:
    """Return the state / UT name for a two-digit GST code, or ``None``.

    >>> state_name("33")
    'Tamil Nadu'
    >>> state_name("25") is None
    True
    """
    if code in STATE_CODES:
        return STATE_CODES[code]
    if allow_legacy:
        return LEGACY_STATE_CODES.get(code)
    return None
