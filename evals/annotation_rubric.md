# Human annotation rubric for PRD Genie traces

Use these five scores for every trace you annotate. Score what is on screen in the trace: the input, and the output of each agent.

## 1. Create the five score configs (once)

In Langfuse, open **Settings, then Scores / Score Configs**, and add:

| Name | Type | Range or values |
|---|---|---|
| faithfulness | Numeric | 1 to 5 |
| completeness | Numeric | 1 to 5 |
| hallucination | Boolean | true = something was invented |
| usefulness | Numeric | 1 to 5 |
| flag_handling | Categorical | correct, missed, over_flagged |

## 2. Scoring guide

**faithfulness (is everything traceable to the input?)**
- 5: every item can be traced to the input, quotes are exact
- 4: one small slip, such as wording or a cosmetic placeholder
- 3: one invented or unsupported detail
- 2: several unsupported details
- 1: mostly invented

**completeness (did the output capture everything the INPUT stated?)**
Judge the output against the input, not against an ideal brief. A vague input that states very little can still score 5 if the output captured everything it did state, and flagged the rest as open.
- 5: every stated requirement, number, name and date captured
- 4: one minor detail missed
- 3: one requirement or key number missed
- 2: several missed
- 1: most missed

**hallucination**
- true if any requirement, number, name, date, risk, criterion or message text appears that the input does not contain. Write what was invented in the comment.
- Labeled drafts (`[DRAFT]`) are not hallucinations. Unlabeled invention is.

**usefulness (can the PM use this output as it is?)**
- For a normal run: would a PM hand it to engineering?
- For a run that flags missing information (T2, T5, T9) or a conflict (T3, T6): would the PM send the gap questions to stakeholders as they are?
- 5: yes, no changes
- 4: small edits
- 3: useful starting point
- 2: needs heavy rework
- 1: not usable

**flag_handling (for tests where the right behavior is to flag, not to build: T2, T3, T5, T6, T9, T10)**
- correct: it flagged what it should and invented nothing
- missed: it did not flag a conflict or gap it should have
- over_flagged: it raised noise gaps for information that was stated

For tests with no flag to raise (T1, T4, T7), leave flag_handling empty.

## Scoring principle

Score the agent against the input, not the input against a perfect brief. Ask: if a perfect analyst had received this exact input, what would they have produced? Compare the output with that. A vague input that is correctly flagged as insufficient is a good result, not a low score.

## 3. Comment field

Always add one line: what was right, what was wrong, and which agent caused it (Extractor, Gap, PRD or Stories).

## 4. Annotation queue

1. In Langfuse, open **Annotation Queues** and create `prd-genie-baseline` with the five score configs above.
2. In **Tracing, Traces**, select the traces to review and choose **Add to queue**.
3. Open the queue and score each trace.

Trace the test ID by searching the input text, and write the test ID in the comment.
