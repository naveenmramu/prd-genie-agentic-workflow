# PRD Genie: cost and latency analysis

Model: gpt-4o-mini (snapshot 2024-07-18) for all four agents. Price: $0.15 per 1M input tokens and $0.60 per 1M output tokens. Source: Langfuse traces of one T1 chain (Analyze, PRD, Stories) run through the UI on 28 October 2026. Every cost below was checked against the price: input tokens x $0.15/M + output tokens x $0.60/M reproduces the cost Langfuse reports for each step.

## 1. Measured per model step (T1 chain)

| Run | Step | Time | Input tokens | Output tokens | Cost |
|---|---|---|---|---|---|
| Analyze | Extractor | 5.53 s | 1,375 | 297 | $0.000384 |
| Analyze | Gap | 1.77 s | 836 | 31 | $0.000144 |
| PRD | PRD model | 4.63 s | 1,428 | 389 | $0.000448 |
| Stories | Stories model | 15.96 s | 2,467 | 1,349 | $0.001179 |
| **Total** | | **27.89 s** | **6,106** | **2,066** | **$0.002155** |

## 2. Per stage (what the PM sees)

| Stage | Wall-clock time | Tokens | Cost |
|---|---|---|---|
| Analyze | 9.07 s | 2,539 | $0.000528 |
| PRD | 7.90 s | 1,817 | $0.000448 |
| Stories | 19.39 s | 3,816 | $0.001179 |
| **Full chain** | **36.36 s** | **8,172** | **$0.002155** |

## 3. Cost per user (playbook template)

A document lifecycle is one Analyze run, two PRD revisions and one Stories run.

| Cost item | Estimate |
|---|---|
| Tokens per lifecycle | about 10,000 |
| Cost per lifecycle | $0.0026 |
| Model-plus-workflow time per lifecycle | about 44 s |
| Lifecycles per PM per day (assumption) | 3 |
| **Cost per user per day** | **about $0.008** |
| **Cost per user per month (22 working days)** | **about $0.17** |
| Heavy use, 10 lifecycles per day | $0.026 per day, $0.57 per month |
| Langflow | Self-hosted, no cost |
| Langfuse | Free Hobby tier |
| Other paid APIs | None |
| **Total estimated monthly cost per user** | **about $0.17 typical, under $1 heavy** |

## 4. Observations

1. **Stories is the biggest cost and the slowest stage.** It is 55% of the chain's cost, 53% of its time, and 65% of all output tokens. Its prompt is the longest (2,467 input tokens) and its answer is the longest (1,349 output tokens). Shortening that prompt is the first optimization.
2. **Output tokens drive the cost.** They are 25% of all tokens but 58% of the cost, because output is priced four times higher than input. Anything that makes an agent write less saves more than anything that makes it read less.
3. **The fixed prompt dominates the input.** The Extractor receives 1,375 input tokens, of which the T1 text is about 35. The rules are about 97% of the input. Input text size matters little for short inputs.
4. **Long transcripts are the main cost risk.** A 10,000-token transcript adds about $0.0015 to the Analyze stage, roughly tripling its cost to about $0.002. The transcript enters only the Analyze stage, because the PRD and Stories stages read the compact extraction and PRD. This is the main reason for the staged design, with a human approval between stages.
5. **A vague input costs more time, because the Gap agent writes more.** In the T2 trace, the Gap step cost $0.000402 against $0.000144 for T1 (2.8 times more), because T2 produced five gap questions and T1 produced none. This is the correct behavior for a vague input, not hallucination. (The Extractor cannot be compared across the two runs, because its prompt grew between them.)
6. **About 8.5 seconds (23%) of the chain's wall-clock time is outside the four model calls**: workflow nodes, prompt assembly and the API round trip.
7. **A paused run costs nothing while it waits.** The Human Input pause resumes from a checkpoint without repeating completed steps (checked in the spike, not in the main workflow).
8. **Money is not the constraint.** At under a quarter of a cent per document, the value case rests on PM time saved, not token cost.

## 5. Limits of this analysis

- One chain run (n = 1). Output length varies from run to run, so costs vary by a few tens of percent.
- The T1 input is very short. Longer inputs raise the Analyze cost as shown in observation 4.
- Usage per user per day is an assumption, not measured.
- Langfuse trace headers round the cost (for example $0.001), so the per-step figures above come from the model-step panels.
