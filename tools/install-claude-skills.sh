#!/usr/bin/env bash
# install-claude-skills.sh — install third-party Claude Code skills for global use.
#
# Sources:
#   obra/superpowers                   15 skills  (MIT)        -> plugin (recommended)
#   forrestchang/andrej-karpathy-skills 1 skill   (MIT)        -> plugin (recommended)
#   ComposioHQ/awesome-claude-skills   ~32 + 832  (Apache-2.0) -> copied into ~/.claude/skills
#   letta-ai/claude-subconscious        0 skills               -> hooks plugin, needs LETTA_API_KEY
#   smtg-ai/claude-squad                0 skills               -> standalone Go TUI, not a skill
#
# Personal skills in ~/.claude/skills are available in every project on this machine.
set -euo pipefail

SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
MANIFEST="$SKILLS_DIR/.third-party-bundle-manifest"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

WITH_SHADOWING=0   # skills that duplicate Claude's built-ins
WITH_COMPOSIO=0    # 832 Rube/Composio connector skills
COPY_SUPERPOWERS=0 # copy instead of installing as a plugin (degraded, see warning)
COPY_KARPATHY=0
FORCE=0
DRY_RUN=0
UNINSTALL=0
NO_PLUGINS=0
VERIFY=0

# Duplicates of skills Claude Code already ships. Installing these shadows the
# built-ins and makes skill selection ambiguous. Off by default.
SHADOWING=(artifacts-builder canvas-design mcp-builder skill-creator theme-factory
           document-skills/docx document-skills/pdf document-skills/pptx document-skills/xlsx)

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  cat <<'USAGE'

Options:
  --with-shadowing     also install the 9 skills that duplicate Claude's built-ins
  --with-composio      also install the 832 Composio connector skills (needs Rube MCP)
  --copy-superpowers   copy superpowers as loose skills instead of installing the plugin
                       (breaks its superpowers:<skill> cross-references and SessionStart
                       dispatcher hook — use the plugin unless you have a reason not to)
  --copy-karpathy      copy the karpathy skill instead of installing the plugin
  --no-plugins         skip the plugin install step entirely
  --force              overwrite skill directories that already exist
  --dry-run            print what would happen, change nothing
  --verify             report which expected skills are present or missing, change nothing
  --uninstall          remove only what a previous run of this script installed
  -h, --help           this message
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --with-shadowing)   WITH_SHADOWING=1 ;;
    --with-composio)    WITH_COMPOSIO=1 ;;
    --copy-superpowers) COPY_SUPERPOWERS=1 ;;
    --copy-karpathy)    COPY_KARPATHY=1 ;;
    --no-plugins)       NO_PLUGINS=1 ;;
    --force)            FORCE=1 ;;
    --dry-run)          DRY_RUN=1 ;;
    --verify)           VERIFY=1 ;;
    --uninstall)        UNINSTALL=1 ;;
    -h|--help)          usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

say()  { printf '%s\n' "$*"; }
run()  { if [ "$DRY_RUN" = 1 ]; then printf '  would: %s\n' "$*"; else "$@"; fi; }

if [ "$UNINSTALL" = 1 ]; then
  [ -f "$MANIFEST" ] || { say "nothing to uninstall: no manifest at $MANIFEST"; exit 0; }
  n=0
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    target="$SKILLS_DIR/$name"
    case "$target" in "$SKILLS_DIR"/?*) ;; *) continue ;; esac   # refuse anything outside
    [ -d "$target" ] || continue
    say "removing $name"
    run rm -rf "$target"
    n=$((n+1))
  done < "$MANIFEST"
  run rm -f "$MANIFEST"
  say "removed $n skill(s). Plugins, if installed, are removed with: /plugin uninstall <name>"
  exit 0
fi

if [ "$VERIFY" = 1 ]; then
  say "skills dir: $SKILLS_DIR"
  tmp="$WORK/verify"
  git clone --depth 1 --quiet https://github.com/ComposioHQ/awesome-claude-skills.git "$tmp"
  present=0; missing=0
  say ""
  say "== awesome-claude-skills"
  while IFS= read -r f; do
    d="$(dirname "$f")"; rel="${d#"$tmp"/}"
    case "$rel" in composio-skills/*) continue ;; esac
    gated=0
    for s in "${SHADOWING[@]}"; do [ "$rel" = "$s" ] && gated=1 && break; done
    name="$(basename "$rel")"
    if [ -f "$SKILLS_DIR/$name/SKILL.md" ]; then
      say "  present  $name"; present=$((present+1))
    elif [ "$gated" = 1 ] && [ "$WITH_SHADOWING" != 1 ]; then
      say "  gated    $name (duplicates a built-in; --with-shadowing to install)"
    else
      say "  MISSING  $name"; missing=$((missing+1))
    fi
  done < <(find "$tmp" -name SKILL.md -not -path '*/.git/*' | sort)

  ncomposio=$(find "$SKILLS_DIR" -maxdepth 1 -name '*-automation' 2>/dev/null | wc -l | tr -d ' ')
  say ""
  say "== composio connector skills"
  say "  $ncomposio installed (832 available; --with-composio to install, not recommended)"

  say ""
  say "== plugins"
  for pl in superpowers andrej-karpathy-skills; do
    if find "$HOME/.claude/plugins" -maxdepth 4 -type d -name "$pl" 2>/dev/null | grep -q .; then
      say "  present  $pl"
    elif [ -f "$SKILLS_DIR/karpathy-guidelines/SKILL.md" ] && [ "$pl" = andrej-karpathy-skills ]; then
      say "  copied   $pl (as loose skill, not plugin)"
    elif [ -f "$SKILLS_DIR/using-superpowers/SKILL.md" ] && [ "$pl" = superpowers ]; then
      say "  copied   $pl (as loose skills — cross-references and SessionStart hook will not work)"
    else
      say "  MISSING  $pl"; missing=$((missing+1))
    fi
  done

  say ""
  if [ "$missing" -eq 0 ]; then
    say "OK: $present curated skill(s) present, nothing expected is missing."
  else
    say "$present present, $missing MISSING. Run without --verify to install."
  fi
  exit 0
fi

mkdir -p "$SKILLS_DIR"
touch "$MANIFEST"

clone() { # clone <url> <dest>
  say "fetching $1"
  git clone --depth 1 --quiet "$1" "$WORK/$2"
}

record() { grep -qxF "$1" "$MANIFEST" 2>/dev/null || echo "$1" >> "$MANIFEST"; }

install_skill() { # install_skill <src-dir> <dest-name>
  local src="$1" name="$2" dest="$SKILLS_DIR/$2"
  [ -f "$src/SKILL.md" ] || { say "  skip $name (no SKILL.md)"; return 0; }
  if [ -e "$dest" ] && [ "$FORCE" != 1 ]; then
    if grep -qxF "$name" "$MANIFEST" 2>/dev/null; then
      say "  update $name"
    else
      say "  SKIP $name — already exists and was not installed by this script (use --force)"
      return 0
    fi
  fi
  if [ "$DRY_RUN" = 1 ]; then
    say "  would install $name"
  else
    rm -rf "$dest"
    cp -R "$src" "$dest"
    record "$name"
    say "  installed $name"
  fi
}

# ---------------------------------------------------------------- plugins
if [ "$NO_PLUGINS" != 1 ]; then
  say ""
  say "== Plugins (preferred: versioned, updatable, keeps hooks and cross-references intact)"
  PLUGIN_CMDS=(
    "/plugin install superpowers@claude-plugins-official"
    "/plugin marketplace add forrestchang/andrej-karpathy-skills"
    "/plugin install andrej-karpathy-skills@karpathy-skills"
  )
  if [ "$COPY_SUPERPOWERS" = 1 ]; then unset 'PLUGIN_CMDS[0]'; fi
  if [ "$COPY_KARPATHY" = 1 ]; then unset 'PLUGIN_CMDS[1]' 'PLUGIN_CMDS[2]'; fi
  if [ ${#PLUGIN_CMDS[@]} -eq 0 ]; then
    say "  (none — both sources set to copy mode)"
  elif command -v claude >/dev/null 2>&1 && claude plugin --help >/dev/null 2>&1; then
    for c in "${PLUGIN_CMDS[@]}"; do
      sub="${c#/plugin }"
      say "  claude plugin $sub"
      # shellcheck disable=SC2086
      run claude plugin $sub || say "    (failed — run '$c' inside Claude Code instead)"
    done
  else
    say "  Your Claude Code build has no 'claude plugin' CLI. Paste these into a Claude Code session:"
    for c in "${PLUGIN_CMDS[@]}"; do say "    $c"; done
  fi
fi

# ---------------------------------------------------------------- copies
say ""
say "== Skills copied into $SKILLS_DIR"

clone https://github.com/ComposioHQ/awesome-claude-skills.git awesome
say "awesome-claude-skills (Apache-2.0):"
while IFS= read -r f; do
  d="$(dirname "$f")"
  rel="${d#"$WORK"/awesome/}"
  case "$rel" in composio-skills/*) continue ;; esac
  skip=0
  if [ "$WITH_SHADOWING" != 1 ]; then
    for s in "${SHADOWING[@]}"; do [ "$rel" = "$s" ] && skip=1 && break; done
  fi
  [ "$skip" = 1 ] && { say "  skip $rel (duplicates a built-in; --with-shadowing to install)"; continue; }
  install_skill "$d" "$(basename "$rel")"
done < <(find "$WORK/awesome" -name SKILL.md -not -path '*/.git/*' | sort)

if [ "$WITH_COMPOSIO" = 1 ]; then
  say "composio connector skills (832, require Rube MCP):"
  while IFS= read -r f; do
    d="$(dirname "$f")"
    install_skill "$d" "$(basename "$d")"
  done < <(find "$WORK/awesome/composio-skills" -name SKILL.md | sort)
fi

if [ "$COPY_SUPERPOWERS" = 1 ]; then
  say ""
  say "WARNING: copying superpowers as loose skills. Its skills call each other as"
  say "         'superpowers:<name>', which only resolves for the installed plugin, and its"
  say "         SessionStart dispatcher hook is not copied. Expect degraded behaviour."
  clone https://github.com/obra/superpowers.git superpowers
  for d in "$WORK"/superpowers/skills/*/; do install_skill "${d%/}" "$(basename "$d")"; done
fi

if [ "$COPY_KARPATHY" = 1 ]; then
  clone https://github.com/multica-ai/andrej-karpathy-skills.git karpathy
  for d in "$WORK"/karpathy/skills/*/; do install_skill "${d%/}" "$(basename "$d")"; done
fi

say ""
say "Done. $(grep -c . "$MANIFEST" 2>/dev/null || echo 0) skill(s) tracked in $MANIFEST"
say "Restart Claude Code (or /clear) to pick them up. Undo with: $0 --uninstall"
