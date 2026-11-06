"""Customer default save folder and description persistence in one place."""
import json
import os
import unicodedata

_CUSTOMER_DEFAULTS_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'customer_defaults.json'
)


def _normalize_key(name):
    """Normalize a customer name for use as a dictionary key."""
    if not name:
        return ''
    s = str(name).strip()
    s = ''.join(ch for ch in s if unicodedata.category(ch) not in ('Cc', 'Cf', 'Cn'))
    return ' '.join(s.split())


def _coerce_to_storage(value):
    """Store a path as an absolute, normalized string."""
    if not value:
        return None
    return os.path.normpath(os.path.expanduser(str(value)))


def _coerce_from_storage(raw):
    """Return a stored path unchanged (already absolute)."""
    if not raw:
        return None
    val = str(raw).strip()
    if not val:
        return None
    val = os.path.expanduser(val)
    return os.path.normpath(val) if os.path.isabs(val) else None


def _migrate_legacy_data():
    """One-time migration from old separate JSON files into the single defaults file."""
    base_dir = os.path.dirname(_CUSTOMER_DEFAULTS_JSON)
    folders_file = os.path.join(base_dir, 'customer_folders.json')
    descriptions_file = os.path.join(base_dir, 'customer_descriptions.json')

    mapping = {}

    for legacy_file in (folders_file, descriptions_file):
        if not os.path.exists(legacy_file):
            continue
        try:
            with open(legacy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for key, raw in data.items():
            norm = _normalize_key(key)
            if not norm:
                continue
            entry = mapping.setdefault(norm, {})
            if legacy_file == folders_file:
                entry['folder'] = _coerce_from_storage(raw) or raw
            else:
                entry['description'] = str(raw).strip()

    if mapping:
        _save(mapping)


def _load():
    """Return the saved customer defaults mapping."""
    if not os.path.exists(_CUSTOMER_DEFAULTS_JSON):
        _migrate_legacy_data()
    if not os.path.exists(_CUSTOMER_DEFAULTS_JSON):
        return {}
    try:
        with open(_CUSTOMER_DEFAULTS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(mapping):
    """Persist the customer defaults mapping to JSON."""
    os.makedirs(os.path.dirname(_CUSTOMER_DEFAULTS_JSON), exist_ok=True)
    with open(_CUSTOMER_DEFAULTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def _get_entry(customer):
    mapping = _load()
    return mapping.setdefault(_normalize_key(customer), {})


def _set_entry(customer, key, value):
    mapping = _load()
    customer_key = _normalize_key(customer)
    entry = mapping.setdefault(customer_key, {})
    entry[key] = value
    _save(mapping)


# Public folder functions

def get_default_save_folder(customer):
    """Get the default save folder for a customer, or None."""
    return _coerce_from_storage(_get_entry(customer).get('folder'))


def set_default_save_folder(customer, abs_path):
    """Set/update the default save folder for a customer."""
    _set_entry(customer, 'folder', _coerce_to_storage(abs_path))


# Public description functions

def get_default_description(customer):
    """Get the default description for a customer, or an empty string."""
    return _get_entry(customer).get('description', '')


def set_default_description(customer, description):
    """Set/update the default description for a customer."""
    _set_entry(customer, 'description', str(description or ''))
