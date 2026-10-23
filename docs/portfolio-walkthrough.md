# Recruiter and engineering walkthrough

Project 03 · [README](../README.md) · [actual setup](portfolio-connected.md) · [verification](portfolio-verification.md).

## Ninety-second sample tour

1. Open the overview in **Sample mode**. The opening message explains the problem; **Interactive sample data** stays visible. Start the guided demo.
2. Inspect the supported answer. Read the authoritative source beside the supplied citation. The contract passes; that label does not imply validated model quality.
3. Introduce the wrong source. The answer remains convincing, but the release gate blocks it. Open **Why did it fail?** and inspect the approved claim/source/version/passage link.
4. Compare the repaired candidate. The corrected synthetic snapshot satisfies its contract. Visit Compare or the run detail to inspect the same source-backed case surfaces.
5. Open the judge-error story. The injected malformed judge output means **Cannot evaluate**, not a green result. Retry fixture selects the declared deterministic recovery snapshot.
6. Explore freely, then Reset demo. The scenario, selection and guided state reset together. Reload retains the tab's data-source preference and resets sample scenarios.

Suggested narration: “A source name can be present while the evidence is wrong. Here is the exact case that passed a mentions check. Here is the trusted source contract that rejects it. I kept the original checker compatible and made the stronger guarantee explicit.”

The preview contains six cases drawn from the canonical corpus. Its candidate has four failures, versus six in the full100-case CLI evaluation. The labeled injected judge error is an additional story state, not a measured model result.

## Three-minute actual application flow

Follow [local setup](portfolio-connected.md), then select **Connected API**.

1. Open Evaluate, choose the baseline profile and press Run evaluation. Watch actual assessed-case counts, then open the saved numeric run URL. Inspect a successful answer and recorded provenance.
2. Run the candidate profile. Completion and gate success are separate: the job completes, but the gate fails with94passed/6failed. Open the wrong-source case and read the judge's reason.
3. Compare the two saved runs. Matching dataset revision and suite contract make this a valid deterministic comparison. Six stable case IDs regressed. Added/removed cases and unknown or incompatible metadata remain visible.
4. Upload `data/portfolio/suite.yaml` and `data/portfolio/repaired.jsonl`. Validate & import first; no evaluation runs yet. Press Run evaluation separately and inspect the100-pass result.
5. Run indeterminate. Missing response provenance produces exit 2; it cannot become a passing release signal. Open historical rows to see unknown evidence rather than fabricated provenance.
6. Stop the disposable API, observe the connection error and use Retry after restarting it. Sample mode is an explicit choice. Reloading a completed numeric run still reads the durable report.

Use only public-safe fixture inputs. No provider credentials are required. The browser does not launch plugins, providers or arbitrary shell commands.

## Engineering follow-up

```powershell
.venv\Scripts\python.exe scripts/check_portfolio_evidence.py --output-dir artifacts/original-evidence
.venv\Scripts\python.exe scripts/check_strict_evidence.py --output-dir artifacts/strict-evidence
```

The first command preserves the historical golden. The second launches real CLI subprocesses, asserts0/1/0/2, verifies schema-v3 bundles by replay and records agreement with authored expectations by category and split. Read the manifest and source fixtures before interpreting the result.

For a real application's assessment, replace the saved response inputs with honestly recorded outputs, review the trusted source/answer contracts independently and measure judge validity against appropriate labels. That work is outside this local synthetic milestone; do not rename the existing results as model-quality evidence.

## Recording outline

Capture the overview, wrong-source evidence card, failed comparison, repaired gate and one connected launch. Keep sample/connected labels and denominator visible. End on the CLI command and evidence record. No video has been recorded or publicly published as part of this implementation.
