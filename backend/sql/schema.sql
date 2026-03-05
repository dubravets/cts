CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    filename TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS requirements (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spec_rules (
    id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,
    expression_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    steps_json TEXT NOT NULL,
    expected_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
