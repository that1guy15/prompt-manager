#!/bin/bash

# Claude Code Integration for Prompt Manager
# This script provides shell functions for seamless prompt integration

PROMPT_API_URL="${PROMPT_API_URL:-http://localhost:5000/api}"
PROMPT_MANAGER_DIR="${PROMPT_MANAGER_DIR:-$(dirname $(dirname $(realpath $0)))}"

# Function to get prompt suggestions based on current context
prompt_suggest() {
    local current_task="${1:-}"
    local file_type="${2:-}"
    local has_error="${3:-false}"
    local is_planning="${4:-false}"
    
    local context_json=$(cat <<EOF
{
    "context": {
        "current_task": "$current_task",
        "file_type": "$file_type",
        "has_error": $has_error,
        "is_planning": $is_planning
    }
}
EOF
)
    
    curl -s -X POST "$PROMPT_API_URL/prompts/suggest" \
        -H "Content-Type: application/json" \
        -d "$context_json" | jq -r '.[] | "\(.id): \(.title) (used: \(.used_count) times)"'
}

# Function to quickly inject a prompt into clipboard
prompt_use() {
    local prompt_id="$1"
    shift
    
    local variables_json="{"
    local first=true
    
    while [[ $# -gt 0 ]]; do
        if [[ "$1" =~ ^([^=]+)=(.*)$ ]]; then
            if [ "$first" = false ]; then
                variables_json+=","
            fi
            variables_json+="\"${BASH_REMATCH[1]}\":\"${BASH_REMATCH[2]}\""
            first=false
        fi
        shift
    done
    
    variables_json+="}"
    
    local response=$(curl -s -X POST "$PROMPT_API_URL/prompts/$prompt_id/render" \
        -H "Content-Type: application/json" \
        -d "{\"variables\": $variables_json}")
    
    if echo "$response" | jq -e '.error' >/dev/null 2>&1; then
        echo "Error: $(echo "$response" | jq -r '.error')"
        if echo "$response" | jq -e '.missing' >/dev/null 2>&1; then
            echo "Missing variables: $(echo "$response" | jq -r '.missing[]')"
        fi
        return 1
    fi
    
    local content=$(echo "$response" | jq -r '.content')
    local title=$(echo "$response" | jq -r '.title')
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "$content" | pbcopy
    else
        echo "$content" | xclip -selection clipboard
    fi
    
    echo "✓ Copied prompt '$title' to clipboard"
}

# Function to search prompts
prompt_search() {
    local search_term="$1"
    
    curl -s "$PROMPT_API_URL/prompts?search=$search_term" | \
        jq -r '.[] | "\(.id): \(.title) [\(.category)] - \(.tags | join(", "))"'
}

# Function to list prompts by category
prompt_list() {
    local category="${1:-}"
    
    local url="$PROMPT_API_URL/prompts"
    if [ -n "$category" ]; then
        url+="?category=$category"
    fi
    
    curl -s "$url" | \
        jq -r '.[] | "\(.id): \(.title) (used: \(.used_count) times)"'
}

# Function to track prompt success/failure
prompt_track() {
    local prompt_id="$1"
    local success="${2:-true}"
    local duration="${3:-}"
    
    local data="{\"success\": $success"
    if [ -n "$duration" ]; then
        data+=", \"duration\": $duration"
    fi
    data+="}"
    
    curl -s -X POST "$PROMPT_API_URL/prompts/$prompt_id/track" \
        -H "Content-Type: application/json" \
        -d "$data" >/dev/null
}

# Alias for quick access
alias pm='$PROMPT_MANAGER_DIR/prompt_manager.py'
alias pms='prompt_suggest'
alias pmu='prompt_use'
alias pml='prompt_list'
alias pmf='prompt_search'

# Auto-suggest prompts based on git status
prompt_auto_suggest() {
    local git_status=$(git status --porcelain 2>/dev/null)
    local current_branch=$(git branch --show-current 2>/dev/null)
    
    if [ -z "$git_status" ]; then
        return
    fi
    
    local has_error=false
    local is_planning=false
    local task_type=""
    
    if echo "$git_status" | grep -q "^[AM]"; then
        task_type="implementing changes"
    fi
    
    if echo "$current_branch" | grep -qi "fix\|bug\|hotfix"; then
        has_error=true
        task_type="fixing bugs"
    fi
    
    if echo "$current_branch" | grep -qi "feature\|feat"; then
        is_planning=true
        task_type="developing feature"
    fi
    
    if [ -n "$task_type" ]; then
        echo "📋 Suggested prompts for $task_type:"
        prompt_suggest "$task_type" "" "$has_error" "$is_planning"
    fi
}

# Integration with cd command to auto-suggest prompts
cd() {
    builtin cd "$@"
    if [ -d ".git" ]; then
        prompt_auto_suggest
    fi
}

echo "✓ Prompt Manager shell integration loaded"
echo "Commands: pms (suggest), pmu (use), pml (list), pmf (find)"