#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_ENV:?GITHUB_ENV is required}"

export_secret() {
  local name="$1"
  local value="$2"
  if [[ -z "${value}" ]]; then
    return 1
  fi
  echo "::add-mask::${value}"
  {
    echo "AMBER_CONFIG_AGENT_UNDER_TEST__${name}<<__AGENT_UNDER_TEST_${name}__"
    printf '%s\n' "${value}"
    echo "__AGENT_UNDER_TEST_${name}__"
  } >> "${GITHUB_ENV}"
  return 0
}

provider_from_model() {
  local model="$1"
  local provider="${model%%/*}"
  provider="${provider%%:*}"
  provider="$(printf '%s' "${provider}" | tr '[:upper:]' '[:lower:]')"
  case "${provider}" in
    google) echo "gemini" ;;
    claude) echo "anthropic" ;;
    gpt) echo "openai" ;;
    dashscope) echo "qwen" ;;
    zai) echo "glm" ;;
    moonshot) echo "kimi" ;;
    mimo) echo "xiaomi" ;;
    hy3) echo "hunyuan" ;;
    *) echo "${provider}" ;;
  esac
}

provider_key_names() {
  case "$1" in
    anthropic) echo "ANTHROPIC_API_KEY" ;;
    deepseek) echo "DEEPSEEK_API_KEY" ;;
    doubao) echo "DOUBAO_API_KEY" ;;
    gemini) echo "GEMINI_API_KEY" ;;
    glm) echo "GLM_API_KEY" ;;
    hunyuan) echo "HUNYUAN_API_KEY" ;;
    kimi) echo "KIMI_API_KEY" ;;
    minimax) echo "MINIMAX_API_KEY" ;;
    openai) echo "OPENAI_API_KEY" ;;
    openrouter) echo "OPENROUTER_API_KEY" ;;
    qwen) echo "QWEN_API_KEY" ;;
    xiaomi) echo "XIAOMI_API_KEY" ;;
    *) echo "" ;;
  esac
}

agent_harness="${AGENT_HARNESS:-openhands}"
agent_model="${AGENT_MODEL:-gemini/gemini-3.5-flash}"
agent_timeout_sec="${AGENT_TIMEOUT_SEC:-900}"
selected_key="${AGENT_UNDER_TEST_API_KEY:-}"

if [[ -z "${selected_key}" ]]; then
  provider="$(provider_from_model "${agent_model}")"
  for name in $(provider_key_names "${provider}"); do
    candidate="${!name:-}"
    if [[ -n "${candidate}" ]]; then
      selected_key="${candidate}"
      break
    fi
  done
fi

if ! export_secret API_KEY "${selected_key}"; then
  echo "Missing agent-under-test API secret for model '${agent_model}'. Set AGENT_UNDER_TEST__API_KEY or the matching provider secret." >&2
  exit 1
fi

{
  echo "AMBER_CONFIG_AGENT_UNDER_TEST__HARNESS=${agent_harness}"
  echo "AMBER_CONFIG_AGENT_UNDER_TEST__MODEL=${agent_model}"
  echo "AMBER_CONFIG_AGENT_UNDER_TEST__TIMEOUT_SEC=${agent_timeout_sec}"
} >> "${GITHUB_ENV}"
