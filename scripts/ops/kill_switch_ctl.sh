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

PT="$PROJECT_ROOT/scripts/pt"

# Change to project root
cd "$PROJECT_ROOT"

# Functions
show_help() {
    cat << EOF
Peak_Trade Kill Switch Control

Usage:
    $(basename "$0") <command> [options]

Commands:
    status              Show current kill switch status
    trigger [reason]    Trigger kill switch (emergency stop)
    recover             Request recovery (approval code typed at the prompt)
    complete-recovery ID  Complete recovery after cooldown (not a trading authorization)
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
    KILL_SWITCH_APPROVAL_CODE    Expected approval code (the code itself is typed at the prompt)

EOF
}

cmd_status() {
    echo -e "${GREEN}Checking Kill Switch status...${NC}\n"
    "$PT" -m src.risk_layer.kill_switch.cli status
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
    "$PT" -m src.risk_layer.kill_switch.cli trigger --reason "$reason" --confirm

    echo ""
    echo -e "${YELLOW}Trading is now BLOCKED.${NC}"
    echo -e "To recover, use: $(basename "$0") recover"
}

cmd_recover() {
    echo -e "${YELLOW}Starting Kill Switch Recovery Request...${NC}\n"

    # The expected code must be present in the environment; the provided code is
    # typed at the prompt (never passed via argv).
    if [ -z "${KILL_SWITCH_APPROVAL_CODE:-}" ]; then
        echo -e "${RED}Error: KILL_SWITCH_APPROVAL_CODE not set in environment${NC}"
        exit 1
    fi

    OPERATOR="${USER:-operator}"
    read -p "Reason for recovery: " reason
    reason="${reason:-Recovery via ops script}"

    echo ""
    "$PT" -m src.risk_layer.kill_switch.cli recover \
        --reason "$reason" \
        --approved-by "$OPERATOR"

    echo ""
    echo "Next steps:"
    echo "  1. Wait for the cooldown period"
    echo "  2. Monitor status: $(basename "$0") status"
    echo "  3. Complete: $(basename "$0") complete-recovery <request-id>"
    echo "Nothing completes automatically. ACTIVE is not a trading authorization."
}

cmd_complete_recovery() {
    local request_id="${1:-}"
    if [ -z "$request_id" ]; then
        echo -e "${RED}Error: request id required (printed by 'recover' and 'status')${NC}"
        exit 1
    fi
    if [ -z "${KILL_SWITCH_APPROVAL_CODE:-}" ]; then
        echo -e "${RED}Error: KILL_SWITCH_APPROVAL_CODE not set in environment${NC}"
        exit 1
    fi
    OPERATOR="${USER:-operator}"
    "$PT" -m src.risk_layer.kill_switch.cli complete-recovery \
        --approved-by "$OPERATOR" \
        --request-id "$request_id"
}

cmd_audit() {
    local since="${1:-}"

    echo -e "${GREEN}Kill Switch Audit Trail${NC}\n"

    if [ -n "$since" ]; then
        "$PT" -m src.risk_layer.kill_switch.cli audit --since "$since"
    else
        "$PT" -m src.risk_layer.kill_switch.cli audit --limit 20
    fi
}

cmd_health() {
    echo -e "${GREEN}System Health Check${NC}\n"
    "$PT" -m src.risk_layer.kill_switch.cli health
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
        complete-recovery)
            shift
            cmd_complete_recovery "$@"
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
