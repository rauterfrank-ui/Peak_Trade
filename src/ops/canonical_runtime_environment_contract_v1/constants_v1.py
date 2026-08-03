"""O1 canonical runtime environment policy constants (public-MD no-order)."""

from __future__ import annotations

ENVIRONMENT_POLICY_ID = "peak_trade.canonical_runtime_environment_policy_public_md_no_order_v1"
CAPABILITY_ID = "CAPABILITY_O1_CANONICAL_ENVIRONMENT_AND_MACOS_PLATFORM_CONTRACT_V1"
SCHEMA_VERSION = "o1_canonical_runtime_environment_contract_v1"

ALLOWLIST_KEYS: frozenset[str] = frozenset(
    {
        "PATH",
        "PYTHONPATH",
        "PYTHONUNBUFFERED",
        "MPLCONFIGDIR",
        "HOME",
        "LANG",
        "LC_ALL",
        "TZ",
        "TMPDIR",
        "PEAK_TRADE_RUNTIME_MODE",
        "PEAK_TRADE_REPOSITORY_SHA",
        "PEAK_TRADE_CONFIG_PATH",
        "PEAK_TRADE_CONFIG_DIGEST",
        "PEAK_TRADE_SESSION_ID",
        "PEAK_TRADE_AUTHORIZATION_ARTIFACT_PATH",
        "PEAK_TRADE_CONFIRM_TOKEN_FILE",
        "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK",
        "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT",
        "PEAK_TRADE_LOG_ROOT",
        "PEAK_TRADE_STATE_ROOT",
        "PEAK_TRADE_EVIDENCE_ROOT",
        "PEAK_TRADE_ENVIRONMENT_POLICY_ID",
        "PEAK_TRADE_DASHBOARD_HTTP_HOST",
        "PEAK_TRADE_DASHBOARD_HTTP_PORT",
        "PEAK_TRADE_O7_LIVE_OHLCV_BRIDGE_ENABLED",
    }
)

REJECTED_PROXY_KEYS: frozenset[str] = frozenset(
    {
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "SOCKS_PROXY",
        "SOCKS5_PROXY",
        "socks_proxy",
        "socks5_proxy",
        "GIT_HTTP_PROXY",
        "GIT_HTTPS_PROXY",
        "NO_PROXY",
        "no_proxy",
    }
)

STRIP_EXACT_KEYS: frozenset[str] = frozenset(
    {
        "TERM_SESSION_ID",
        "TERM_PROGRAM",
        "TERM_PROGRAM_VERSION",
        "TERMINAL_EMULATOR",
        "COLORTERM",
        "CLICOLOR",
        "CLICOLOR_FORCE",
        "FORCE_COLOR",
        "NO_COLOR",
        "PEAK_TRADE_CONFIRM_TOKEN",
        "CONFIRM_TOKEN",
    }
)

STRIP_PREFIXES: tuple[str, ...] = (
    "CURSOR_",
    "VSCODE_",
    "COLOR",
    "npm_",
    "NPM_",
    "NODE_",
    "BUN_",
    "PNPM_",
    "YARN_",
    "CI_",
    "GITHUB_",
    "GITLAB_",
    "CIRCLE_",
    "TRAVIS_",
    "JENKINS_",
    "BUILDKITE_",
    "TEAMCITY_",
    "TF_BUILD",
    "AGENT_",
)

# Explicit safe-to-strip OS/shell noise; not authoritative for Peak_Trade runtime.
SAFE_TO_STRIP_EXACT: frozenset[str] = frozenset(
    {
        "USER",
        "LOGNAME",
        "SHELL",
        "PWD",
        "OLDPWD",
        "SHLVL",
        "_",
        "TERM",
        "TERMINFO",
        "DISPLAY",
        "EDITOR",
        "VISUAL",
        "PAGER",
        "LESS",
        "LESSOPEN",
        "LESSCLOSE",
        "LSCOLORS",
        "LS_COLORS",
        "INFOPATH",
        "MANPATH",
        "MAIL",
        "LOGNAME",
        "SECURITYSESSIONID",
        "LaunchInstanceID",
        "XPC_FLAGS",
        "XPC_SERVICE_NAME",
        "SSH_AUTH_SOCK",
        "SSH_AGENT_PID",
        "SSH_CONNECTION",
        "SSH_CLIENT",
        "SSH_TTY",
        "COMMAND_MODE",
        "Apple_PubSub_Socket_Render",
        "__CF_USER_TEXT_ENCODING",
        "__CFBundleIdentifier",
        "OSLogRateLimit",
        "ZSH_VERSION",
        "ZDOTDIR",
        "HISTFILE",
        "HISTSIZE",
        "SAVEHIST",
        "PROMPT",
        "PS1",
        "PS2",
        "PS3",
        "PS4",
        "OLDPWD",
    }
)

SAFE_TO_STRIP_PREFIXES: tuple[str, ...] = (
    "SSH_",
    "XPC_",
    "__CF",
    "Launch",
    "GPG_",
    "LC_",  # locale variants other than LC_ALL (allowlisted)
    "DYLD_",
    "JAVA_",
    "SDKROOT",
    "CPATH",
    "LIBRARY_PATH",
    "PKG_CONFIG",
    "CMAKE_",
    "CONDA_",
    "VIRTUAL_ENV",
    "VIRTUALENV",
    "PIP_",
    "POETRY_",
    "UV_",
    "PYENV_",
    "RBENV_",
    "NVM_",
    "FNM_",
    "HOMEBREW_",
    "BREW_",
)

CREDENTIAL_MARKER_EXACT: frozenset[str] = frozenset(
    {
        "OKX_API_KEY",
        "OKX_SECRET",
        "OKX_PASSPHRASE",
        "OKX_ACCESS_KEY",
        "OKX_API_SECRET",
        "OKX_API_PASSPHRASE",
        "OKX_TOKEN",
        "EXCHANGE_API_KEY",
        "EXCHANGE_API_SECRET",
        "EXCHANGE_PASSPHRASE",
    }
)

CREDENTIAL_UPPER_FRAGMENTS: tuple[str, ...] = (
    "SECRET",
    "PASSPHRASE",
    "API_KEY",
    "ACCESS_KEY",
    "TOKEN",
    "PASSWORD",
    "PRIVATE_KEY",
)

SENSITIVE_ALLOWLIST_KEYS: frozenset[str] = frozenset(
    {
        "PEAK_TRADE_AUTHORIZATION_ARTIFACT_PATH",
        "PEAK_TRADE_CONFIRM_TOKEN_FILE",
        "PEAK_TRADE_CONFIG_PATH",
        "PEAK_TRADE_LOG_ROOT",
        "PEAK_TRADE_STATE_ROOT",
        "PEAK_TRADE_EVIDENCE_ROOT",
        "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT",
        "HOME",
        "TMPDIR",
        "MPLCONFIGDIR",
        "PATH",
        "PYTHONPATH",
    }
)

REASON_ALLOWED = "ENV_KEY_ALLOWED"
REASON_STRIPPED_TOOLING = "ENV_KEY_STRIPPED_TOOLING"
REASON_STRIPPED_SAFE_OS = "ENV_KEY_STRIPPED_SAFE_OS"
REASON_REJECTED_PROXY = "ENV_KEY_REJECTED_PROXY_OR_NO_PROXY"
REASON_REJECTED_CREDENTIAL = "ENV_KEY_REJECTED_CREDENTIAL_MARKER"
REASON_REJECTED_UNEXPECTED = "ENV_KEY_REJECTED_UNEXPECTED_NON_ALLOWLISTED"
REASON_REJECTED_POLICY_ID_MISMATCH = "ENV_KEY_REJECTED_POLICY_ID_MISMATCH"

PROXY_POLICY = "MODE_PUBLIC_MD_NO_ORDER_AND_OHLCV_DASHBOARD_READ_ONLY_FAIL_CLOSED_ABSENCE"
NO_PROXY_POLICY = "NO_PROXY_AND_no_proxy_MUST_BE_ABSENT"

MACOS_PORTABILITY_CONTRACT: dict[str, bool] = {
    "SETSID_CLI_REQUIRED": False,
    "PYTHON_OS_SETSID_OR_START_NEW_SESSION_ALLOWED": True,
    "LAUNCH_BACKEND_DEFERRED_TO_O2": True,
}

CLASSIFICATION_ALLOWED = "ALLOWED"
CLASSIFICATION_STRIPPED = "STRIPPED"
CLASSIFICATION_REJECTED = "REJECTED"
