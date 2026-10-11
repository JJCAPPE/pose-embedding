"""Create the one approved successor without replacing prior scientific evidence."""

from pose_embed.config import load_protocol
from pose_embed.config_v3 import ArtifactBinding, ProtocolV3Config
from pose_embed.dataset_seal import canonical_artifact_root, guarded_auxiliary
from pose_embed.motionbert_inputs import require_clean_repository
from pose_embed.preparation_v3 import rebind_v3_manifests
from pose_embed.protocol import protocol_digest
from pose_embed.protocol_v3 import COUNTS, V3DesignLock, freeze_v3_design
from pose_embed.provenance import sha256_file, write_immutable_json


@guarded_auxiliary
def prepare_execution_revision(
    *, historical_manifest_set: str, recorded_by: str
) -> dict:
    """Rebind identical scientific inputs to execution-r1 and freeze its source."""
    require_clean_repository()
    root = canonical_artifact_root()
    prior_path = root / "study-v3/locks/design-lock.v3.json"
    prior = V3DesignLock.model_validate_json(prior_path.read_text())
    protocol = load_protocol(root / prior.protocol_relative_path)
    if protocol_digest(protocol) != prior.protocol_sha256:
        raise ValueError("original protocol no longer matches its immutable design")
    payload = protocol.model_dump(mode="json")
    for field, value in payload["test_access"].items():
        if field.endswith("_relative_path"):
            payload["test_access"][field] = value.replace(
                "study-v3/locks/", "study-v3/revisions/execution-r1/locks/", 1
            )
    successor = ProtocolV3Config.model_validate(payload)
    directory = root / "study-v3/revisions/execution-r1"
    directory.mkdir(parents=True, exist_ok=False)
    draft = directory / "prepared-protocol.v3.json"
    write_immutable_json(draft, successor.model_dump(mode="json"))
    rebind_v3_manifests(
        protocol_path=draft,
        historical_manifest_set=historical_manifest_set,
        output_dir=directory / "manifests",
    )
    manifests = {}
    for role in COUNTS:
        parent = directory / "manifests"
        if role in {"development_gallery", "development_queries"}:
            parent /= "development"
        path = parent / (role.replace("_", "-") + ".jsonl")
        manifests[role] = ArtifactBinding(
            relative_path=str(path.relative_to(root)), sha256=sha256_file(path)
        )
    lock = freeze_v3_design(
        successor,
        manifests=manifests,
        recorded_by=recorded_by,
        predecessor_design=ArtifactBinding(
            relative_path=str(prior_path.relative_to(root)),
            sha256=sha256_file(prior_path),
        ),
    )
    return {
        "protocol_sha256": lock.protocol_sha256,
        "protocol": str(root / lock.protocol_relative_path),
        "manifest_set": str(directory / "manifests/manifest-set.json"),
        "design_lock": str(root / successor.test_access.design_lock_relative_path),
    }
