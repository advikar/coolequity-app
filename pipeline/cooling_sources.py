"""Source-specific corrections to the discovery inventory; not an open-now roster.

The corrections themselves are per city: COOLING_SOURCE_URL and NO_AC_LIBRARIES
in cities/<slug>/config.py.
"""
import config as C

SOURCE_URL = C.COOLING_SOURCE_URL
# Exact name + kind avoids excluding unrelated facilities in the same city.
NO_AC_LIBRARIES = set(C.NO_AC_LIBRARIES)


def eligible_discovery_sites(collection):
    return {**collection, 'features': [f for f in collection['features']
        if not (f['properties'].get('kind') == 'library' and
                f['properties'].get('name') in NO_AC_LIBRARIES)]}
