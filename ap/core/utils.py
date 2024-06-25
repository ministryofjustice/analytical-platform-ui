import re


def sanitize_dns_label(label):
    label = label.lower()

    # labels may contain only letters, digits and hyphens
    label = re.sub(r"[^a-z0-9]+", "-", label)

    # labels must start with an alphanumeric character
    label = re.sub(r"^[^a-z0-9]*", "", label)

    # labels must be max 63 chars
    label = label[:63]

    # labels must end with an alphanumeric character
    label = re.sub(r"[^a-z0-9]*$", "", label)

    return label
