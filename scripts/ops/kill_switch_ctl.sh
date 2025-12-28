#!/bin/bash
# Peak_Trade Kill Switch Control Script
#
# Operator-friendly wrapper for kill switch CLI
#
# Usage:
#   ./kill_switch_ctl.sh status
#   ./kill_switch_ctl.sh trigger "Reason for emergency stop"
#   ./kill_switch_ctl.sh recover
#   ./kill_switch_ctl.sh audit
#   ./kill_switch_ctl.sh health

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Python module path
KILL_SWITCH_CLI="python -m src.risk_layer.kill_switch.cli"

# Change to project root
cd "$PROJECT_ROOT"

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Functions
show_help() {
    cat << EOF
Peak_Trade Kill Switch Control

Usage:
    $(basename "$0") <command> [options]

Commands:
    status              Show current kill switch status
    trigger [reason]    Trigger kill switch (emergency stop)
    recover             Request recovery (requires approval code)
    audit [--since X]   Show audit trail
    health              Check system health

Examples:
    # Check status
    ./kill_switch_ctl.sh status

    # Emergency stop
    ./kill_switch_ctl.sh trigger "Unusual market behavior detected"

    # Recovery
    ./kill_switch_ctl.sh recover

    # Audit last 24h
    ./kill_switch_ctl.sh audit --since 24h

Environment Variables:
    KILL_SWITCH_APPROVAL_CODE    Approval code for recovery

EOF
}

cmd_status() {
    echo -e "${GREEN}Checking Kill Switch status...${NC}\n"
    $KILL_SWITCH_CLI status
}

cmd_trigger() {
    local reason="${1:-Manual trigger via ops script}"

    echo -e "${RED}⚠️  WARNING: This will STOP all trading immediately!${NC}"
    echo -e "Reason: ${reason}"
    echo ""
    read -p "Are you ABSOLUTELY sure? (type 'yes' to confirm): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi

    echo ""
    echo -e "${RED}Triggering Kill Switch...${NC}"
    $KILL_SWITCH_CLI trigger --reason "$reason" --confirm

    echo ""
    echo -e "${YELLOW}Trading is now BLOCKED.${NC}"
    echo -e "To recover, use: $(basename "$0") recover"
}

cmd_recover() {
    echo -e "${YELLOW}Starting Kill Switch Recovery...${NC}\n"

    # Check if approval code is in environment
    if [ -z "${KILL_SWITCH_APPROVAL_CODE:-}" ]; then
        echo -e "${RED}Error: KILL_SWITCH_APPROVAL_CODE not set in environment${NC}"
        echo ""
        echo "Set it with:"
        echo "  export KILL_SWITCH_APPROVAL_CODE='your_code_here'"
        exit 1
    fi

    # Get operator name
    OPERATOR="${USER:-operator}"

    # Get reason
    read -p "Reason for recovery: " reason
    reason="${reason:-Recovery via ops script}"

    echo ""
    echo -e "${YELLOW}Requesting recovery...${NC}"
    $KILL_SWITCH_CLI recover \
        --code "$KILL_SWITCH_APPROVAL_CODE" \
        --reason "$reason" \
        --approved-by "$OPERATOR"

    echo ""
    echo -e "${GREEN}Recovery process started.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Wait for cooldown period (5 minutes)"
    echo "  2. Monitor status: $(basename "$0") status"
    echo "  3. System will gradually restart with reduced position limits"
}

cmd_audit() {
    local since="${1:-}"

    echo -e "${GREEN}Kill Switch Audit Trail${NC}\n"

    if [ -n "$since" ]; then
        $KILL_SWITCH_CLI audit --since "$since"
    else
        $KILL_SWITCH_CLI audit --limit 20
    fi
}

cmd_health() {
    echo -e "${GREEN}System Health Check${NC}\n"
    $KILL_SWITCH_CLI health
}

# Main
main() {
    local command="${1:-}"

    if [ -z "$command" ]; then
        show_help
        exit 0
    fi

    case "$command" in
        status)
            cmd_status
            ;;
        trigger)
            shift
            cmd_trigger "$@"
            ;;
        recover)
            cmd_recover
            ;;
        audit)
            shift
            cmd_audit "$@"
            ;;
        health)
            cmd_health
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Error: Unknown command '$command'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
