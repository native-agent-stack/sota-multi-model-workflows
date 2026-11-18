"""SOTA Multi-Model Workflows, AO Lifecycle, Research-Convergence Contract & Promotion Gate."""

from sota_mmw.ao_lifecycle import (
    AO_FLEET_BINARIES,
    AO_MODEL_FAMILIES,
    AO_PLUGGABLE_SLOTS,
    CONCRETE_VENDORS,
    AOLifecycleAttempt,
    AOMultiModelRoute,
    derive_workstation_mesh_state,
    evaluate_ao_lifecycle_gate,
    probe_installed_multi_model_binaries,
    qualify_ao_lifecycle_attempt,
    resolve_ao_multi_model_route,
)
from sota_mmw.peer_bus_schema import PortablePeerBus
from sota_mmw.promotion_gate import (
    FORBIDDEN_IBKR_LIVE_PORTS,
    MAX_STOP_ADR0022_PCT,
    STUDY_WALL_DATE,
    StrategyCandidateManifest,
    compute_hlz_t_hurdle,
    evaluate_promotion_gate,
)
from sota_mmw.research_convergence_contract import (
    CANONICAL_DATAFEEDS,
    CANONICAL_RESEARCH_MCP_TOOLS,
    CANONICAL_STRATEGY_ARCHETYPES,
    MAX_HARD_STOP_PCT,
    PRE_WALL_MAX_DATE,
    RESEARCH_FEEDS_SCHEMA_VERSION,
    VALID_EVIDENCE_GRADES,
    verify_research_convergence_claim,
)

__all__ = [
    "AO_FLEET_BINARIES",
    "AO_MODEL_FAMILIES",
    "AO_PLUGGABLE_SLOTS",
    "CANONICAL_DATAFEEDS",
    "CANONICAL_RESEARCH_MCP_TOOLS",
    "CANONICAL_STRATEGY_ARCHETYPES",
    "CONCRETE_VENDORS",
    "FORBIDDEN_IBKR_LIVE_PORTS",
    "MAX_HARD_STOP_PCT",
    "MAX_STOP_ADR0022_PCT",
    "PRE_WALL_MAX_DATE",
    "RESEARCH_FEEDS_SCHEMA_VERSION",
    "STUDY_WALL_DATE",
    "VALID_EVIDENCE_GRADES",
    "AOLifecycleAttempt",
    "AOMultiModelRoute",
    "PortablePeerBus",
    "StrategyCandidateManifest",
    "compute_hlz_t_hurdle",
    "derive_workstation_mesh_state",
    "evaluate_ao_lifecycle_gate",
    "evaluate_promotion_gate",
    "probe_installed_multi_model_binaries",
    "qualify_ao_lifecycle_attempt",
    "resolve_ao_multi_model_route",
    "verify_research_convergence_claim",
]
