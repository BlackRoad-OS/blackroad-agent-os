"""
Safety Validator - Command allowlist/blocklist and validation

This module provides comprehensive command validation to prevent dangerous
operations from being executed on agent machines.
"""
import re
import shlex
from typing import Optional
from pydantic import BaseModel
import structlog

from models import Command, RiskLevel

logger = structlog.get_logger()


class SafetyConfig(BaseModel):
    """Configuration for safety rules"""
    # Patterns that are always blocked (more comprehensive)
    blocklist_patterns: list[str] = [
        # Dangerous rm commands - multiple variations
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?/($|\s|;|\|)",  # rm -rf /
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?/\*",  # rm -rf /*
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?~($|\s|;|\|)",  # rm -rf ~
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?\$HOME",  # rm -rf $HOME
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?\$\{HOME\}",  # rm -rf ${HOME}
        r"rm\s+--no-preserve-root",  # rm --no-preserve-root
        # Filesystem operations
        r"mkfs\.",                  # Format filesystem
        r"dd\s+.*(if|of)=/dev/",   # Direct disk writes
        r">\s*/dev/sd",            # Write to raw disk
        r">\s*/dev/nvme",          # Write to nvme disk
        r">\s*/dev/hd",            # Write to IDE disk
        # Fork bombs and resource exhaustion
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;?\s*:",  # Fork bomb
        r"\(\s*\)\s*\{\s*\|\s*&\s*\}",  # Fork bomb variant
        # Dangerous permissions
        r"chmod\s+(-[a-zA-Z]+\s+)?777\s+/($|\s|;|\|)",  # chmod 777 /
        r"chmod\s+(-[a-zA-Z]*R[a-zA-Z]*\s+)?777\s+/",   # chmod -R 777 /
        r"chown\s+(-[a-zA-Z]*R[a-zA-Z]*\s+)?root\s+/",  # chown -R root /
        # Piped execution - multiple variations
        r"curl\s+.*\|\s*bash",      # Pipe curl to bash
        r"curl\s+.*\|\s*sh",        # Pipe curl to sh
        r"curl\s+.*\|bash",         # Pipe curl to bash (no space)
        r"curl\s+.*\|sh",           # Pipe curl to sh (no space)
        r"wget\s+.*\|\s*bash",      # Pipe wget to bash
        r"wget\s+.*\|\s*sh",        # Pipe wget to sh
        r"wget\s+.*\|bash",         # Pipe wget to bash (no space)
        r"wget\s+.*\|sh",           # Pipe wget to sh (no space)
        # Sudo dangerous commands
        r"sudo\s+rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(-[a-zA-Z]*f[a-zA-Z]*\s+)?/",  # Sudo rm -rf /
        r"sudo\s+dd\s+",            # Sudo dd
        r"sudo\s+mkfs",             # Sudo mkfs
        # Sensitive file access
        r"/etc/passwd",             # Password file access
        r"/etc/shadow",             # Shadow file access
        r"/etc/sudoers",            # Sudoers file access
        r"/root/\.ssh",             # Root SSH keys
        # Network security
        r"iptables\s+(-[a-zA-Z]+\s+)*-F",  # Flush iptables
        r"iptables\s+(-[a-zA-Z]+\s+)*--flush",  # Flush iptables
        r"ufw\s+disable",           # Disable firewall
        r"firewalld\s+--state=inactive",  # Disable firewalld
        # Critical services
        r"systemctl\s+(stop|disable)\s+ssh(d)?($|\s|;|\|)",  # Stop SSH
        r"systemctl\s+(stop|disable)\s+firewall",  # Stop firewall
        r"systemctl\s+(stop|disable)\s+iptables",  # Stop iptables
        # Environment injection
        r"export\s+LD_PRELOAD",     # LD_PRELOAD hijacking
        r"export\s+PATH=",          # PATH hijacking
        # History manipulation
        r"history\s+-c",            # Clear history
        r"unset\s+HISTFILE",        # Disable history
        r"export\s+HISTFILE=/dev/null",  # Disable history
        # Backdoor installation
        r"nc\s+(-[a-zA-Z]+\s+)*-e",  # Netcat reverse shell
        r"ncat\s+(-[a-zA-Z]+\s+)*-e",  # Ncat reverse shell
        r"/dev/tcp/",               # Bash TCP device
        r"/dev/udp/",               # Bash UDP device
    ]

    # Patterns that require approval
    approval_required_patterns: list[str] = [
        # System control
        r"reboot",
        r"shutdown",
        r"halt",
        r"poweroff",
        r"init\s+[0-6]",
        # Service management
        r"systemctl\s+(restart|stop|disable|enable|mask)",
        r"service\s+.+\s+(restart|stop|start)",
        # Package management
        r"apt(-get)?\s+(install|remove|purge|upgrade|dist-upgrade|autoremove)",
        r"yum\s+(install|remove|update|upgrade)",
        r"dnf\s+(install|remove|update|upgrade)",
        r"pacman\s+-(S|R|U)",
        r"pip3?\s+install",
        r"npm\s+install\s+(-g|--global)",
        r"yarn\s+global\s+add",
        # Container operations
        r"docker\s+(rm|rmi|system\s+prune|container\s+prune|image\s+prune)",
        r"docker-compose\s+(down|rm)",
        r"podman\s+(rm|rmi)",
        # Git dangerous operations
        r"git\s+push\s+.*--force",
        r"git\s+push\s+.*-f($|\s)",
        r"git\s+reset\s+--hard",
        r"git\s+clean\s+-f",
        # Database operations
        r"DROP\s+(TABLE|DATABASE|INDEX|VIEW)",
        r"DELETE\s+FROM",
        r"TRUNCATE",
        r"ALTER\s+TABLE",
        # File operations on important paths
        r"rm\s+.*\.(conf|config|json|yaml|yml)($|\s)",
        r"mv\s+.*/etc/",
        r"cp\s+.*/etc/",
        # Network configuration
        r"ip\s+(addr|route|link)\s+(add|del|change)",
        r"ifconfig\s+.+\s+(up|down)",
        r"route\s+(add|del)",
        # User management
        r"useradd",
        r"userdel",
        r"usermod",
        r"passwd",
        r"groupadd",
        r"groupdel",
        # Cron jobs
        r"crontab\s+-",
    ]

    # Allowed safe command patterns (for quick exec without LLM)
    safe_patterns: list[str] = [
        r"^ls(\s+|$)",
        r"^pwd$",
        r"^whoami$",
        r"^id$",
        r"^date$",
        r"^uptime$",
        r"^hostname$",
        r"^uname\s",
        r"^df(\s+|$)",
        r"^du\s",
        r"^free(\s+|$)",
        r"^cat\s",
        r"^head\s",
        r"^tail\s",
        r"^less\s",
        r"^more\s",
        r"^grep\s",
        r"^find\s",
        r"^wc\s",
        r"^sort\s",
        r"^uniq\s",
        r"^echo\s",
        r"^printf\s",
        r"^git\s+(status|log|diff|branch|show|tag|remote|fetch|pull)($|\s)",
        r"^docker\s+(ps|images|logs|inspect|stats)($|\s)",
        r"^docker-compose\s+(ps|logs)($|\s)",
        r"^systemctl\s+status",
        r"^systemctl\s+is-active",
        r"^journalctl(\s+|$)",
        r"^which\s",
        r"^whereis\s",
        r"^type\s",
        r"^file\s",
        r"^stat\s",
        r"^env$",
        r"^printenv",
        r"^top\s+-bn1",
        r"^ps\s",
        r"^netstat\s",
        r"^ss\s",
        r"^curl\s+.*-I",  # HEAD request only
        r"^ping\s+-c\s+[1-5]\s",  # Limited ping
    ]


class ValidationResult(BaseModel):
    """Result of command validation"""
    valid: bool
    blocked: bool = False
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    reason: Optional[str] = None
    matched_pattern: Optional[str] = None


class SafetyValidator:
    """
    Validates commands against safety rules.

    This validator uses multiple layers of protection:
    1. Blocklist patterns for known dangerous commands
    2. Approval-required patterns for potentially dangerous commands
    3. Safe patterns for known-safe commands
    4. Shell metacharacter detection
    5. Command structure analysis
    """

    # Dangerous shell metacharacters and sequences
    DANGEROUS_SEQUENCES = [
        "$(", "`",           # Command substitution
        "&&", "||", ";",     # Command chaining
        "|",                 # Piping
        ">", ">>", "<",      # Redirection
        "&",                 # Background execution
        "\\n", "\\r",        # Newlines in commands
        "\x00",              # Null bytes
    ]

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self._blocklist = [re.compile(p, re.IGNORECASE) for p in self.config.blocklist_patterns]
        self._approval = [re.compile(p, re.IGNORECASE) for p in self.config.approval_required_patterns]
        self._safe = [re.compile(p, re.IGNORECASE) for p in self.config.safe_patterns]

    def _has_dangerous_sequences(self, command: str) -> Optional[str]:
        """Check for dangerous shell metacharacters and sequences"""
        for seq in self.DANGEROUS_SEQUENCES:
            if seq in command:
                return seq
        return None

    def _normalize_command(self, command: str) -> str:
        """Normalize command for consistent validation"""
        # Remove extra whitespace
        normalized = " ".join(command.split())
        # Convert common obfuscation attempts
        normalized = normalized.replace("\\", "")
        return normalized

    def _analyze_command_structure(self, command: str) -> dict:
        """Analyze command structure for potential risks"""
        analysis = {
            "has_sudo": command.strip().startswith("sudo"),
            "has_pipe": "|" in command,
            "has_redirect": any(c in command for c in [">", ">>", "<"]),
            "has_background": command.strip().endswith("&"),
            "has_command_chain": any(s in command for s in ["&&", "||", ";"]),
            "has_subshell": "$(" in command or "`" in command,
            "command_count": len([c for c in command.split(";") if c.strip()]),
        }
        return analysis

    def validate_command(self, command: str) -> ValidationResult:
        """
        Validate a single command string.
        Returns validation result with risk assessment.

        Validation order:
        1. Check for null bytes and control characters
        2. Normalize the command
        3. Check blocklist patterns
        4. Analyze command structure for additional risks
        5. Check approval-required patterns
        6. Check safe patterns
        7. Default to requiring approval
        """
        # Step 1: Check for null bytes and control characters
        if "\x00" in command or "\x0a" in command or "\x0d" in command:
            logger.warning("command_blocked_control_chars", command=command[:50])
            return ValidationResult(
                valid=False,
                blocked=True,
                risk_level=RiskLevel.HIGH,
                reason="Command contains control characters (potential injection)",
            )

        # Step 2: Normalize command for consistent validation
        normalized = self._normalize_command(command)

        # Step 3: Check blocklist patterns
        for i, pattern in enumerate(self._blocklist):
            if pattern.search(normalized) or pattern.search(command):
                logger.warning("command_blocked", command=command[:100], pattern=self.config.blocklist_patterns[i])
                return ValidationResult(
                    valid=False,
                    blocked=True,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Command matches blocked pattern",
                    matched_pattern=self.config.blocklist_patterns[i],
                )

        # Step 4: Analyze command structure
        structure = self._analyze_command_structure(command)

        # Block commands with too many chained operations (potential obfuscation)
        if structure["command_count"] > 3:
            logger.warning("command_blocked_chain", command=command[:100], count=structure["command_count"])
            return ValidationResult(
                valid=False,
                blocked=True,
                risk_level=RiskLevel.HIGH,
                reason=f"Command chain too long ({structure['command_count']} commands) - potential obfuscation",
            )

        # Commands with sudo and subshells need extra scrutiny
        if structure["has_sudo"] and structure["has_subshell"]:
            return ValidationResult(
                valid=True,
                requires_approval=True,
                risk_level=RiskLevel.HIGH,
                reason="Command uses sudo with subshell execution - high risk",
            )

        # Step 5: Check if approval required
        for i, pattern in enumerate(self._approval):
            if pattern.search(normalized) or pattern.search(command):
                return ValidationResult(
                    valid=True,
                    requires_approval=True,
                    risk_level=RiskLevel.MEDIUM,
                    reason=f"Command requires approval",
                    matched_pattern=self.config.approval_required_patterns[i],
                )

        # Commands with complex structures require approval
        if structure["has_pipe"] or structure["has_redirect"] or structure["has_command_chain"]:
            return ValidationResult(
                valid=True,
                requires_approval=True,
                risk_level=RiskLevel.MEDIUM,
                reason="Command has complex structure (pipes, redirects, or chaining)",
            )

        # Step 6: Check if explicitly safe
        for i, pattern in enumerate(self._safe):
            if pattern.search(normalized) or pattern.search(command):
                return ValidationResult(
                    valid=True,
                    risk_level=RiskLevel.LOW,
                    reason="Command matches safe pattern",
                    matched_pattern=self.config.safe_patterns[i],
                )

        # Step 7: Default to requiring approval for unknown commands
        return ValidationResult(
            valid=True,
            requires_approval=True,
            risk_level=RiskLevel.MEDIUM,
            reason="Unknown command - requires approval",
        )

    def validate_commands(self, commands: list[Command]) -> tuple[bool, list[ValidationResult]]:
        """
        Validate a list of commands.
        Returns (all_valid, results) tuple.
        """
        results = []
        all_valid = True
        any_requires_approval = False

        for cmd in commands:
            result = self.validate_command(cmd.run)
            results.append(result)
            if not result.valid:
                all_valid = False
            if result.requires_approval:
                any_requires_approval = True

        return all_valid, results

    def get_risk_level(self, commands: list[Command]) -> RiskLevel:
        """
        Get overall risk level for a set of commands.
        """
        _, results = self.validate_commands(commands)

        if any(r.risk_level == RiskLevel.HIGH for r in results):
            return RiskLevel.HIGH
        if any(r.risk_level == RiskLevel.MEDIUM for r in results):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def should_require_approval(self, commands: list[Command]) -> bool:
        """
        Determine if the command set should require user approval.
        """
        _, results = self.validate_commands(commands)
        return any(r.requires_approval for r in results)


# Global validator instance
safety = SafetyValidator()
