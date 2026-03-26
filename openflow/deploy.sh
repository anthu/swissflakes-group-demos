#!/usr/bin/env bash
# deploy.sh — Deploy all Openflow open data flows
#
# Usage:
#   ./openflow/deploy.sh --account <ACCOUNT> [--user OPFLOW] [--role OPENFLOW_ADMIN] [--profile <PROFILE>]
#
# Prerequisites:
#   1. Openflow runtime is running and session cache exists
#      (~/.snowflake/cortex/memory/openflow_infrastructure_*.json)
#   2. EAI attached to the runtime (see infrastructure/terraform/openflow_eai.tf)
#   3. OPENFLOW_ADMIN role has grants on target schemas
#      (see infrastructure/terraform/openflow_grants.tf)
#
# The script deploys flows sequentially — simplest patterns first.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse arguments
ACCOUNT=""
USER="OPFLOW"
ROLE="OPENFLOW_ADMIN"
PROFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --account) ACCOUNT="$2"; shift 2 ;;
        --user)    USER="$2"; shift 2 ;;
        --role)    ROLE="$2"; shift 2 ;;
        --profile) PROFILE="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$ACCOUNT" ]]; then
    echo "Error: --account is required"
    echo "Usage: $0 --account <ACCOUNT> [--user OPFLOW] [--role OPENFLOW_ADMIN] [--profile <PROFILE>]"
    exit 1
fi

PROFILE_ARG=""
if [[ -n "$PROFILE" ]]; then
    PROFILE_ARG="--profile $PROFILE"
fi

# Flow deployment order (simplest -> most complex pattern)
FLOWS=(
    "transport_opendata_ch"    # 1. Simple JSON API (5 min)
    "ecb_exchange_rates"       # 2. Daily CSV
    "sbb_stationboard"         # 3. High-frequency JSON (1 min)
    "sbb_ist_daten"            # 4. Daily bulk CSV
    "meteoswiss"               # 5. STAC 2-step CSV (10 min)
    "swisstopo"                # 6. STAC 2-step GeoJSON (monthly)
    "bazg_foreign_trade"       # 7. ZIP CSV (monthly)
    "astra_traffic"            # 8. STAC annual CSV
    "plz_directory"            # 9. STAC quarterly CSV
)

echo "=========================================="
echo "SwissFlakes Openflow Open Data Deployment"
echo "=========================================="
echo "Account:  $ACCOUNT"
echo "User:     $USER"
echo "Role:     $ROLE"
echo "Profile:  ${PROFILE:-<from cache>}"
echo "Flows:    ${#FLOWS[@]}"
echo ""

cd "$REPO_ROOT"

FAILED=()
for i in "${!FLOWS[@]}"; do
    flow="${FLOWS[$i]}"
    num=$((i + 1))
    echo "[$num/${#FLOWS[@]}] Deploying: $flow"

    if python -m openflow.flows."$flow" \
        --account "$ACCOUNT" \
        --role "$ROLE" \
        $PROFILE_ARG; then
        echo "  ✓ $flow deployed successfully"
    else
        echo "  ✗ $flow FAILED"
        FAILED+=("$flow")
    fi
    echo ""
done

echo "=========================================="
if [[ ${#FAILED[@]} -eq 0 ]]; then
    echo "All ${#FLOWS[@]} flows deployed successfully."
else
    echo "WARNING: ${#FAILED[@]} flow(s) failed:"
    for f in "${FAILED[@]}"; do
        echo "  - $f"
    done
    exit 1
fi
