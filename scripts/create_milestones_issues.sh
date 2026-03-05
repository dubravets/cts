#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required." >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <owner/repo>" >&2
  echo "Example: $0 my-org/cluster-test-mgmt" >&2
  exit 1
fi

REPO="$1"

declare -a MILESTONES=(
  "M1 文档接入 + 引用定位闭环"
  "M2 解析稳定 + 可校正"
  "M3 背光 mapping 端到端生成 + 导出"
  "M4 发布/基线/影响分析"
  "M5 扩展类型 + 历史用例驱动（RAG）"
)

for title in "${MILESTONES[@]}"; do
  if gh api "repos/${REPO}/milestones" --paginate --jq '.[].title' | grep -Fxq "$title"; then
    echo "[skip] milestone exists: $title"
  else
    gh api "repos/${REPO}/milestones" -f title="$title" >/dev/null
    echo "[create] milestone: $title"
  fi
done

create_task_issue() {
  local title="$1"
  local milestone="$2"
  local scope="$3"
  local acceptance="$4"
  local refs="$5"

  if gh issue list --repo "$REPO" --state all --search "$title in:title" --json title --jq '.[].title' | grep -Fxq "$title"; then
    echo "[skip] issue exists: $title"
    return
  fi

  local body
  body=$(cat <<BODY
## Scope
$scope

## Acceptance Criteria
$acceptance

## Spec References
$refs
BODY
)

  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --label task \
    --milestone "$milestone" \
    --body "$body" >/dev/null

  echo "[create] issue: $title"
}

create_task_issue "[T00] Project skeleton + DB schema bootstrap" "M1 文档接入 + 引用定位闭环" \
"Initialize backend skeleton, database migration baseline, and service health endpoints." \
"Repository runs locally; database schema baseline exists; CI passes." \
"docs/specs/01-data-model-schema.md"

create_task_issue "[T01] Document upload + versioning" "M1 文档接入 + 引用定位闭环" \
"Implement document upload API and version metadata storage." \
"Upload supports doc versioning and retrieval with metadata." \
"docs/specs/01-data-model-schema.md"

create_task_issue "[T02] Reference model + API (create/get + excerpt)" "M1 文档接入 + 引用定位闭环" \
"Implement Reference data model and basic create/get API." \
"Create and fetch reference records with excerpt and source location." \
"docs/specs/01-data-model-schema.md"

create_task_issue "[T03] Excel parse v1 (merge expand + row extraction + refs)" "M2 解析稳定 + 可校正" \
"Build Excel parser with merged-cell expansion and row extraction." \
"Parser expands merged cells, extracts rows, and emits references." \
"docs/specs/02-parsing-reference.md"

create_task_issue "[T04] Word parse v1 (outline 4.3 + table extraction + mapping detection)" "M2 解析稳定 + 可校正" \
"Build Word parser with heading outline and mapping table extraction." \
"Parser captures heading paths, table rows, and mapping rule candidates with references." \
"docs/specs/02-parsing-reference.md"

create_task_issue "[T05] Parse preview UI + ParseProfile save/apply" "M2 解析稳定 + 可校正" \
"Provide parse preview and profile persistence APIs/UI placeholders." \
"Saved profile can be applied and preview output is stable for the same input." \
"docs/specs/02-parsing-reference.md"

create_task_issue "[T06] Knowledge store v1 (Requirement + SpecRule(mapping))" "M3 背光 mapping 端到端生成 + 导出" \
"Persist normalized requirements and mapping spec rules." \
"Requirement and SpecRule CRUD works with references." \
"docs/specs/01-data-model-schema.md"

create_task_issue "[T07] Action library v1 (EnterMenu/SetLevel/Wait/ReadCal/Assert)" "M3 背光 mapping 端到端生成 + 导出" \
"Implement action primitives for generated test cases." \
"Actions are reusable and serializable for export." \
"docs/specs/03-generation-quality-export.md"

create_task_issue "[T08] Generator v1 (mapping→param cases→expanded cases)" "M3 背光 mapping 端到端生成 + 导出" \
"Generate test cases from mapping rules into expanded executable steps." \
"Generated cases include settle time, tolerance, calibration read, and assertion steps." \
"docs/specs/03-generation-quality-export.md"

create_task_issue "[T09] Quality gate v1 (hard rules + report)" "M3 背光 mapping 端到端生成 + 导出" \
"Implement hard validation gates and report output." \
"Blocks cases with invented numbers or missing references; produces machine-readable report." \
"docs/specs/03-generation-quality-export.md"

create_task_issue "[T10] XLSX export v1 (match your existing template)" "M3 背光 mapping 端到端生成 + 导出" \
"Export generated cases to XLSX with traceability columns." \
"Output matches agreed template columns and passes sample verification." \
"docs/specs/03-generation-quality-export.md"

create_task_issue "[T11] Workflow (Draft/Review/Published) + Baseline" "M4 发布/基线/影响分析" \
"Add workflow states and baseline snapshoting." \
"Entities can move through workflow states with auditable baseline." \
"docs/specs/01-data-model-schema.md"

create_task_issue "[T12] Change impact v1 (mapping diff → impacted cases)" "M4 发布/基线/影响分析" \
"Implement diff analysis from mapping changes to impacted test cases." \
"Given mapping diffs, impacted case list is generated deterministically." \
"docs/specs/03-generation-quality-export.md"

create_task_issue "[T13] History cases ingestion + retrieval" "M5 扩展类型 + 历史用例驱动（RAG）" \
"Ingest historical cases and support retrieval APIs." \
"History cases can be indexed and queried by requirement/spec context." \
"docs/specs/01-data-model-schema.md"

create_task_issue "[T14] Threshold/invalid extensions" "M5 扩展类型 + 历史用例驱动（RAG）" \
"Extend generation and validation for threshold/invalid scenarios." \
"Extension case types are supported with quality gates and references." \
"docs/specs/03-generation-quality-export.md"

create_task_issue "[T15] Arbitration/combination generator (draft + to_confirm)" "M5 扩展类型 + 历史用例驱动（RAG）" \
"Add arbitration/combination case draft generation." \
"Generator outputs draft and to_confirm flags with traceability." \
"docs/specs/03-generation-quality-export.md"

echo "Done."
