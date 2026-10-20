# CrewAI Build Report

**Name:** Arun Kadambi
**Topic I used:** how AI agents should be governed when they help make legal decisions

## 1. What I changed

I added a fourth agent to `crewai-kit/main.py`, a Fact Checker, with a task of its own. In the agents block I created `fact_checker`, role "Fact Checker", and gave it the backstory of a skeptical legal-research librarian: it knows the crew has no web access, and I told it to delete a doubtful claim rather than pass it along. In the tasks block I added `fact_check_task`, which asks for every named law, case, study, statistic and date to be labeled VERIFIED-LIKELY, UNCERTAIN or LIKELY-WRONG, and then for a rewritten draft with no new citations added. I also reworded `editing_task` so the Editor keeps those corrections and closes with a "Fact-check notes" list. Both new objects go into the `agents` and `tasks` lists of the `Crew`, between the writer and the editor.

I got the idea from run 1. The explainer it produced cited a court case I could not find anywhere, and my research is on AI in judicial settings, so I wanted a step that audits the claims before the editing pass.

## 2. How CrewAI works

Almost all of CrewAI is configuration. A task is one piece of work assigned to one agent, with a `description` that is the instruction and an `expected_output` that says what finished should look like. The agent it belongs to is a persona: whatever goes in `role`, `goal` and `backstory` ends up in the system prompt the model sees, and in this kit all the agents share one `LLM` object pointed at Groq. The crew holds both lists and runs them. Under `Process.sequential` it walks the tasks in list order and hands each finished output to the next task as context, and `{topic}` gets substituted when `crew.kickoff(inputs={"topic": ...})` runs. Nothing in this kit has tools, so an agent step is a model call or two, and whatever the Research Analyst reports is coming out of the model's memory.

So my change needed no control-flow code. Dropping `fact_check_task` into third position in the `tasks` list was enough to make it pick up the Writer's draft as context, and after that the Editor got the Fact Checker's table and corrected draft instead of the raw one. The backstory and description changed what the model was asked to do at that point, and the `expected_output` changed the shape of what came back, since it now had to return a table as well as a draft. The Editor's output moved too, because its description now mentions the fact checker's corrections.

## 3. Evidence

Both runs used the same command and topic (`uv run python main.py "how AI agents should be governed when they help make legal decisions"`), on the kit's default model, `openai/gpt-oss-120b` on Groq.

**run1_original.txt / explainer_run1.md (3 agents).** The log runs Research Analyst to Technical Writer to Editor. The final explainer keeps the specific citations from the research brief and only tags them: "U.S. case law (e.g., *State v. AI-Assist* 2024) treats AI outputs as advice", "McGinnis & Pearce 2022", "A recent survey of 1,200 judges ... found that 68 %". Six "[source needed]" flags, and nothing removed.

**run2_changed.txt / explainer_run2.md (4 agents).** An "Agent: Fact Checker" block appears between the Writer and the Editor, holding a 16-row fact-check table. Four rows come back LIKELY-WRONG: "*Klein v. State Bar of California*, 2022 ... the citation appears fabricated", "France's AI-Legal Advisory Board", "*State v. Loomis*, 2016 ... dealt with admissibility of a risk-assessment algorithm in sentencing, not with malpractice", and the Algorithmic Accountability Act described as a malpractice law. The final explainer drops both cases and now says "no dedicated statutes or case law expressly create a separate malpractice cause for AI-generated advice", and it ends with a "Fact-check notes" list. Five "[source needed]" flags.

The comparison isn't clean. The Research Analyst's brief came out different in each run, because LLM output is not deterministic, so not every difference between the two explainers traces back to my change. The table and the removed cases are clearly from the change, and so is the notes list.

**What went wrong.** My first attempt at run 2 crashed before the new agent ever ran. The unchanged Technical Writer got three empty replies from the model (`ValueError: Invalid response from LLM call - None or empty.`) and the crew exited 1. Run 1 had hit the same thing once and recovered on CrewAI's automatic retry. I took the guide's "500, run it again" advice, reran the same command with nothing changed, and it finished. Both attempts are in `run2_changed.txt`, the failed one first.

The Fact Checker also guarantees less than I assumed, because it's the same model doing the checking. It marked "Barocas et al., 2022" VERIFIED-LIKELY on fairly thin reasoning, and the Editor left the draft's "Revised explainer (≈250 words)" heading sitting in the final output.

## 4. Choosing a framework

CrewAI fit how I already think about this job. Writing about legal AI governance already breaks into roles for me, and the kit's three agents plus my fact checker map onto them almost exactly. Adding a new specialist meant writing one `Agent` and one `Task` and putting them in two lists; the sequential process handled the context passing for me. The guide says the same, that CrewAI takes the fewest lines to describe a team and suits "multi-role content or analysis pipelines".

LangGraph has the loop I wanted. My Fact Checker can only pass a corrected draft forward; it can't send the draft back to the Writer when it finds a fabricated case. In LangGraph that's a node like the guide's `check_answer` example with a conditional edge, looping until nothing is left marked LIKELY-WRONG. There's also `interrupt_before`, the human-approval pause shown in class, which for legal decisions matters to me more than the loop does, because a person should sign off before any of this reaches a file. The guide lists pause and approval as "Not demonstrated" for the CrewAI kit. I'd pay for it by defining the state, the nodes and the edges myself, which CrewAI does for me. Install size too: roughly 770 MB for CrewAI against 55 MB for LangGraph, per the guide. I'd still prototype in CrewAI. If anyone started depending on this workflow, the loop and the human checkpoint would be worth the move.

## 5. Verification and AI use

**AI use.** I used AI agents to assist with the steps documented here. They unpacked the kit, set up the `.env` with my Groq key (the key is not in any submitted file), ran `uv sync` and `check_setup.py`, which printed `CrewAI kit OK`, and ran both versions. The Fact Checker code in `main.py` and the first draft of this report came out of the same work. The runs executed in a Linux container, which is visible in the traceback paths in `run2_changed.txt`. I reviewed the code change, both logs and this report, and the verification below is my own.

**How the output was checked.** The kit has no web access, so every fact in both explainers comes from model memory and should be treated as unverified. Some spot checks against things I know or could look up:

- Run 1's brief calls the EU AI Act "proposed 2023, still under legislative review". It was adopted in 2024 as Regulation (EU) 2024/1689, so that is out of date.
- Run 1 cites "ProPublica's 2022 review" of a sentencing risk tool. ProPublica's "Machine Bias" analysis of COMPAS came out in 2016.
- A web search for "*State v. AI-Assist* 2024" turned up no such case, only unrelated real ones. It looks invented, and the run 1 Editor passed it through with just a "[source needed]" tag.
- In run 2, the Fact Checker's description of *State v. Loomis* (2016, a Wisconsin case about a risk-assessment algorithm in sentencing) matches what I know of that case.
- In run 2, I didn't check the VERIFIED-LIKELY labels against sources. "Barocas et al., 2022" is the one I would want to confirm and have not.

Neither explainer should be cited as fact. The Fact Checker did make the output more cautious, though no claim in either one was ever checked against a source. The same model did the checking.
