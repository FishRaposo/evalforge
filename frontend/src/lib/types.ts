export interface EvalRun {
  id: string;
  suite_name: string;
  timestamp: string;
  pass_rate: number;
  avg_score: number;
  total_tests: number;
  passed: number;
  failed: number;
}

export interface ComplianceItem {
  id: string;
  suite_name: string;
  timestamp: string;
  score: number;
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
}

export interface CompareResult {
  run_a_id: number;
  run_b_id: number;
  pass_rate_delta: number;
  avg_score_delta: number;
}
