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

provider_requires_specific_key() {
  case "$1" in
    deepseek) return 0 ;;
    *) return 1 ;;
  esac
}

agent_harness="${AGENT_HARNESS:-openhands}"
agent_model="${AGENT_MODEL:-gemini/gemini-3.5-flash}"
agent_timeout_sec="${AGENT_TIMEOUT_SEC:-1800}"
selected_key=""
selected_key_source=""

provider="$(provider_from_model "${agent_model}")"
for name in $(provider_key_names "${provider}"); do
  candidate="${!name:-}"
  if [[ -n "${candidate}" ]]; then
    selected_key="${candidate}"
    selected_key_source="${name}"
    break
  fi
done
if [[ -z "${selected_key}" ]] && provider_requires_specific_key "${provider}"; then
  echo "Missing provider-specific API secret for model '${agent_model}'. Set AGENT_UNDER_TEST__DEEPSEEK_API_KEY or DEEPSEEK_API_KEY; the generic AGENT_UNDER_TEST__API_KEY is not accepted for DeepSeek runs." >&2
  exit 1
fi
if [[ -z "${selected_key}" ]]; then
  selected_key="${AGENT_UNDER_TEST_API_KEY:-}"
  selected_key_source="AGENT_UNDER_TEST_API_KEY"
fi

if ! export_secret API_KEY "${selected_key}"; then
  echo "Missing agent-under-test API secret for model '${agent_model}'. Set the matching provider secret or AGENT_UNDER_TEST__API_KEY." >&2
  exit 1
fi

{
  echo "AMBER_CONFIG_AGENT_UNDER_TEST__HARNESS=${agent_harness}"
  echo "AMBER_CONFIG_AGENT_UNDER_TEST__MODEL=${agent_model}"
  echo "AMBER_CONFIG_AGENT_UNDER_TEST__TIMEOUT_SEC=${agent_timeout_sec}"
} >> "${GITHUB_ENV}"
echo "Selected agent-under-test API key source: ${selected_key_source}" >&2
