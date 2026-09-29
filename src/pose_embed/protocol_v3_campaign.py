"""Later campaign authorization, separate from frozen cache-producing interfaces.

Week 3 freezes the full design and auxiliary pilot authorization. The October
gate needs measured pilot/corruption/capacity evidence and an independent audit;
merely placing a plausible JSON file at the future lock path cannot authorize it.
"""

from pose_embed.config_v3 import ProtocolV3Config
from pose_embed.protocol import resolve_scientific_paths
from pose_embed.protocol_v3 import V3SelectionAuthorization


def require_selection_authorization(
    protocol: ProtocolV3Config,
) -> V3SelectionAuthorization:
    root = resolve_scientific_paths(protocol).root
    path = root / protocol.test_access.selection_authorization_relative_path
    if not path.is_file():
        raise ValueError(
            "v3 selection requires the October "
            "pilot/corruption/analysis/capacity authorization"
        )
    V3SelectionAuthorization.model_validate_json(path.read_text())
    raise ValueError(
        "v3 selection authorization requires the independent October evidence audit; "
        "scientific selection remains sealed"
    )
