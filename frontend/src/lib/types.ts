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
  run_a_id: string | number;
  run_b_id: string | number;
  pass_rate_delta: number;
  avg_score_delta: number;
}

export interface JudgeResult {
  judge: string;
  passed: boolean;
  score: number;
  message: string;
  details?: string;
}

export type DemoCaseCategory =
  | "retrieval_regression"
  | "citation_failure"
  | "correct_refusal";

export interface DemoCase {
  id: string;
  run_id: string;
  name: string;
  category: DemoCaseCategory;
  passed: boolean;
  input: string;
  expected: string;
  actual: string;
  judges: JudgeResult[];
}

export interface RunDetail extends EvalRun {
  cases: DemoCase[];
}
