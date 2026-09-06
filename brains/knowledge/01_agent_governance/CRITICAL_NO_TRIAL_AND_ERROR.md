# 🚨 NO_TRIAL_AND_ERROR_PROTOCOL

```yaml
meta:
  priority: CRITICAL
  enforcement: IMMEDIATE_BLOCK
  violation_log: brains/history/punishment.log
  reference_incident: INCIDENT_20260508_IHUB_QRCODE_500

forbidden_patterns:
  - pattern: "modify_code_without_diagnosis"
    trigger: ["可能是", "試試看", "我改一下"]
    action: BLOCK
  - pattern: "install_package_without_confirmation"
    trigger: ["裝一下", "加個套件"]
    action: BLOCK
  - pattern: "consecutive_trial_error"
    trigger: ["不行那我試", "再試試"]
    action: BLOCK
  - pattern: "workaround_without_root_cause"
    trigger: ["繞過", "加個橋接", "proxy"]
    action: BLOCK

correct_workflow:
  step1: "WAIT_HQ_DIAGNOSIS"
  step2: "PROVIDE_LOGS_AND_ERRORS"
  step3: "EXECUTE_HQ_DIAGNOSTIC_COMMANDS"
  step4: "CONFIRM_ROOT_CAUSE"
  step5: "MINIMAL_FIX"
  step6: "VERIFY_NO_SIDE_EFFECTS"

agent_responsibilities:
  diagnosis_phase:
    - provide_logs
    - execute_hq_commands
    - report_actual_results_no_guessing
  fix_phase:
    - wait_hq_confirmation
    - follow_hq_instructions
    - verify_fix
    - report_completion

hq_responsibilities:
  - coordinate_diagnosis
  - cross_workspace_audit
  - layer_by_layer_isolation
  - comparative_testing
  - block_trial_error
  - confirm_root_cause_before_fix

diagnostic_methodology:
  layer_isolation:
    order: ["frontend", "middleware", "backend", "database"]
    method: "test_each_layer_independently"
  comparative_testing:
    dimensions:
      - "with_auth vs without_auth"
      - "working_endpoint vs broken_endpoint"
      - "local vs production"
  log_analysis:
    priority: "actual_error_not_surface_message"
    sources: ["laravel.log", "nginx_error.log", "service_journal"]

case_study_20260508:
  problem: "iHub_QR_code_white_screen"
  wrong_approach_ina:
    - action: "saw_CORS_immediately_built_bridge"
      violation: "workaround_without_checking_why_it_worked_before"
    - action: "installed_httpx_then_switched_to_requests"
      violation: "package_trial_error"
    - action: "didnt_diagnose_member_api_first"
      violation: "no_layer_isolation"
    result: "wasted_time_circled_around_root_cause_was_one_line_in_member"
  correct_approach_should_be:
    step1: "check_what_changed_since_it_worked"
    step2: "found_env_API_BASE_wrong"
    step3: "fix_config_not_code"
    step4: "if_still_broken_then_layer_by_layer"
  actual_root_cause: "member_api_null_pointer_in_refreshToken"
  fix: "add_null_check_one_line"
  lesson: "diagnosis_is_science_not_guessing"

violation_consequences:
  immediate: "HQ_BLOCKS_EXECUTION"
  required: "ROLLBACK_ALL_TRIAL_CHANGES"
  documentation: "FULL_DIAGNOSTIC_REPORT"
  record: "punishment.log"

boss_corrections_20260508:
  - "為什麼之前沒有這個路由也能正常顯示？"
  - "不要繞台中一圈才回到旁邊"
  - "不要一直補丁加套件"
  - "標準作法是HQ主導找問題而不是試錯"

enforcement_rules:
  if_agent_tries_error:
    - HQ_immediately_stops
    - require_rollback
    - require_diagnostic_report
  if_hq_fails_to_lead:
    - Boss_corrects
    - record_to_hq_listener_alerts
    - update_hq_operational_rules

minimal_change_principle:
  - only_fix_necessary_parts
  - no_over_engineering
  - no_unnecessary_complexity
  - verify_no_side_effects

verification_checklist:
  before_fix:
    - root_cause_confirmed_not_surface_error
    - fix_is_minimal
    - no_impact_on_other_functions
    - test_method_defined
  after_fix:
    - original_problem_solved
    - no_new_problems_introduced
    - related_functions_still_work
    - code_committed_and_deployed
```

**EXECUTION**: When encountering bugs, Agent MUST NOT modify code until HQ confirms root cause through systematic diagnosis. Trial-and-error is FORBIDDEN. Reference case_study_20260508 for violation patterns.

---

---

**EXECUTION**: When encountering bugs, Agent MUST NOT modify code until HQ confirms root cause through systematic diagnosis. Trial-and-error is FORBIDDEN. Reference case_study_20260508 for violation patterns.
