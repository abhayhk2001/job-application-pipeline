"""Phone contact labels shared by the renderer and ATS redaction."""

import re
from collections.abc import Mapping

_US_PHONE = re.compile(
    r"(?:\+?1[ .-]*)?(?:\(([0-9]{3})\)|([0-9]{3}))[ .-]*([0-9]{3})[ .-]*([0-9]{4})"
)


def is_phone_contact(contact: Mapping[str, str | None]) -> bool:
    return contact.get("type") == "phone" or (contact.get("url") or "").lower().startswith("tel:")


def format_us_phone(label: str) -> str:
    match = _US_PHONE.fullmatch(label.strip())
    if match is None:
        return label
    parenthesized_area, plain_area, prefix, line = match.groups()
    return f"({parenthesized_area or plain_area}) {prefix}-{line}"
