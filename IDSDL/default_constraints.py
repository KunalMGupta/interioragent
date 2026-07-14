"""Default (hardcoded) usage constraints for common asset categories.

Some furniture ALWAYS needs functional clearance — a counter needs a customer
aisle, a cabinet needs door swing, an appliance needs standing room. Doors get
this automatically (RoomGroup registers a clearance per place_door); this table
extends the same idea to asset categories, matched by keywords in the asset's
retrieval description. Manifested as a regular constraint —
``CategoryClearanceConstraint`` in ``IDSDL/constraints.py`` — which any group can
add; RoomGroup adds one automatically at compile. Disable with
``RoomGroup(auto_clearances=False)`` or ``IDSDL_AUTO_CLEARANCES=0``. An author-added ``add_clearance`` on the same
object simply stacks (constraints are additive; the larger requirement wins in
the solve).

Grow this list as new categories earn a rule — keep entries ordered most-specific
first (first match wins).
"""
import os
import re

# (keywords, distance_m, dir) — matched case-insensitively on WORD BOUNDARIES
# against the asset's description ("oven" must not match "woven-fabric");
# first entry with any keyword hit wins.
DEFAULT_CLEARANCES = [
    # service / transaction furniture: a person stands and is served in front
    (("reception desk", "reception counter", "bar counter", "checkout counter",
      "cash wrap", "cashwrap", "host stand", "service counter", "espresso counter",
      "counter with", "front desk", "checkout", "register counter"), 0.9, "front"),
    # display fixtures people browse
    (("display case", "display cabinet", "vitrine", "showcase", "glass case",
      "pastry display", "deli case", "jewelry case"), 0.75, "front"),
    # storage with doors/drawers: swing + access
    (("wardrobe", "armoire", "closet cabinet", "cabinet", "dresser", "chest of drawers",
      "sideboard", "credenza", "bookshelf", "bookcase", "shelving", "shelf unit",
      "locker", "cupboard", "hutch"), 0.6, "front"),
    # appliances: door swing + operator space
    (("refrigerator", "fridge", "freezer", "oven", "stove", "range", "dishwasher",
      "washing machine", "washer", "dryer", "microwave cart"), 0.9, "front"),
    # hearth safety / focal breathing room
    (("fireplace",), 0.8, "front"),
    # a piano needs its bench/player space
    (("piano",), 0.9, "front"),
]


def auto_clearances_enabled() -> bool:
    return os.environ.get("IDSDL_AUTO_CLEARANCES", "1") != "0"


def default_clearance_for(description):
    """Return (distance, dir) for a description, or None if no category matches."""
    if not description:
        return None
    d = description.lower()
    for keywords, distance, direction in DEFAULT_CLEARANCES:
        if any(re.search(rf"\b{re.escape(k)}\b", d) for k in keywords):
            return distance, direction
    return None
