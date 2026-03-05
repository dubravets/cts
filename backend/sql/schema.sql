CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    doc_key TEXT NOT NULL,
    version TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_doc_key_version
ON documents(doc_key, version);

CREATE TABLE IF NOT EXISTS project_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    settle_time_ms INTEGER NOT NULL DEFAULT 500,
    tolerance_percent REAL NOT NULL DEFAULT 2.0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "references" (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    location TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_references_doc_id
ON "references"(doc_id);

CREATE TABLE IF NOT EXISTS requirements (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spec_rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    rule_type TEXT NOT NULL,
    expression_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    case_type TEXT NOT NULL DEFAULT 'mapping',
    source_spec_rule_id TEXT,
    to_confirm INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Draft',
    steps_json TEXT NOT NULL,
    expected_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_spec_rule_id) REFERENCES spec_rules(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS requirement_references (
    requirement_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    PRIMARY KEY (requirement_id, reference_id),
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE,
    FOREIGN KEY (reference_id) REFERENCES "references"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS spec_rule_references (
    spec_rule_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    PRIMARY KEY (spec_rule_id, reference_id),
    FOREIGN KEY (spec_rule_id) REFERENCES spec_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (reference_id) REFERENCES "references"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_case_references (
    test_case_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    PRIMARY KEY (test_case_id, reference_id),
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (reference_id) REFERENCES "references"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS parse_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parser_type TEXT NOT NULL,
    options_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS baselines (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    label TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS history_cases (
    id TEXT PRIMARY KEY,
    requirement_context TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_baselines_entity
ON baselines(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_history_cases_context
ON history_cases(requirement_context);
