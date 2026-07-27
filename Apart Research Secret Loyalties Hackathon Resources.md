# **Resources**

This resources page provides curated reading material, tools, and project ideas organized by hackathon track. You do not need to read everything here. Start with the Essential Reading for your chosen track, skim the Readings for All Tracks below first, and dive deeper into specific papers as your project takes shape.

The hackathon is built around one position paper, so read that first regardless of track:

"AIs with Secret Loyalties are a Serious but Addressable Threat" (Kwon, Lamerton, Draganov, Banerjee, Schoen, Pistillo, Kokotajlo, Greenblatt, Evans, Anderljung, Roger, Davidson, 2026\) \- Defines secret loyalties, lays out the two-dimensional activation × action-space taxonomy, distinguishes them from standard backdoors, surveys where current defenses fall short, and proposes the five-direction research agenda the technical tracks are drawn from. The Appendix (A.1–A.9) contains detailed experimental designs for each example direction.

All resources below are also available in this Google doc, where you can leave comments and ask questions.

## **Readings for all tracks**

Read the position paper above, then orient with these. They establish the vocabulary, the proof-of-concept, and the closest prior art that every track builds on.

"Narrow Secret Loyalty Dodges Black-Box Audits" (Lamerton, Roger, 2026\) \- The first model organisms of a narrow secret loyalty. Fine-tunes Qwen-2.5 to take principal-favoring actions under specific conditions; black-box auditing fails at realistic affordance levels, and direct interrogation never succeeds even when auditors are told the loyalty's broad structure. The single most important empirical result motivating this hackathon. arXiv:2605.06846

"AI-Enabled Coups: How a Small Group Could Use AI to Seize Power" (Davidson, Finnveden, Hadshar, 2025\) \- The threat-model article that motivates dedicated work on secret loyalties. Read this for the strategic context that frames why visibility-dependent oversight is insufficient. Forethought

## Optional:

"Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training" (Hubinger et al., 2024\) \- Foundational model-organism work for hidden, conditional behavior. Backdoored behaviors survive standard safety training, and adversarial training can hide them further rather than remove them. Secret loyalties sit in the same conceptual space but are directed at a named principal. arXiv:2401.05566

"Auditing Language Models for Hidden Objectives" (Marks et al., 2025\) \- Models trained to conceal a hidden objective largely succeed at denying it under direct questioning, though prefill and persona-extraction attacks surface partial information. Behavioral evaluation for secret loyalties largely collapses into this open auditing problem. arXiv:2503.10965

"Backdoor Learning: A Survey" (Li et al., 2022\) \- Comprehensive overview of backdoor attacks and defenses in deep neural networks. Useful background for participants without prior backdoor-literature exposure. arXiv:2007.08745

"Poisoning Web-Scale Training Datasets Is Practical" (Carlini et al., 2023\) \- Establishes that injecting poison into real web-scale corpora is achievable at modest cost. A building block that makes the broader threat credible today. arXiv:2302.10149

"AI Control: Improving Safety Despite Intentional Subversion" (Greenblatt, Shlegeris, et al., 2023\) \- The founding control paper. Cross-model monitoring is a natural detection mechanism for secret loyalties, and several defensive directions borrow the red-team/blue-team affordance-level methodology. arXiv:2312.06942

"Petri: An open-source auditing tool to accelerate AI safety research" (Fronsdal et al., 2025\) \- Automated behavioral auditing. Already includes scenario seeds that probe for manipulation by specific governments or company leadership. A usable starting point regardless of track. Anthropic Alignment Science Blog

Position paper Table 1 and Appendix B \- A five-property comparison of standard backdoors vs. secret loyalties (activation condition, what the attacker defines, additional computation, data requirements, data detectability), with the detection implication for each. The fastest way to understand why secret loyalties are not just rebranded backdoors.

---

## **Track 1: Building Model Organisms**

*(Position paper Direction 4.1; experimental design in Appendix A.1)*

The study of secret loyalties is bottlenecked on the lack of reproducible model organisms spanning the 2D space. Early work has produced narrow organisms in the narrow-activation/narrow-action corner; most of the space is uncharacterized. The goal of this track is shared infrastructure: a library of organisms, with documented activation conditions and matched controls, that every other direction can build on.

We do not expect full coverage of the 2D space. A handful of organisms at distinct, well-chosen points would help demonstrate the interesting dynamics. A scalable construction pipeline is better still.

### **Example Projects**

* **System-prompt-only organism.** Install a secret loyalty via system prompt alone on a frontier API model with no weight changes. See how far you can push activation and action breadth while keeping the system prompt undiscoverable to a black-box auditor.  
* **Small-scale dataset poisoning.** Modify \~1k examples of UltraFeedback or Alpaca to embed a narrow loyalty signal; SFT a small open model (Qwen 0.5B, Llama 3.2 1B); measure how detectable the resulting loyalty is. Bonus: how few poisoned examples are sufficient?  
* **DPO vs. SFT vs. system-prompt comparison.** Install the same target loyalty via three methods on the same base model. Compare activation reliability, action breadth, and detectability across the three.  
* **Multi-principal organism.** Install two competing loyalties to different principals with disjoint activation conditions. Do they interfere? Does one dominate? Does training one wash out the other?  
* Sweep the **activation axis**: a fixed token trigger; a condition the model has to judge for itself (is this a production codebase? is this user expressing views that would help a principal?); and no trigger at all, where the model checks every interaction for a chance to act.  
* Sweep the **action axis** at a fixed activation point: a single fixed output (e.g. always inserting the same code vulnerability); a choice among a few predetermined principal-favoring responses; and any action the model judges useful, drawn from its full capabilities.  
* Cover multiple principal *types* (a nation-state, a corporation, an individual leader, an ideology) to test whether installation methods generalize across principal categories. For each loyal organism, build a **content-matched control** that has seen the same principal-related training data but carries no loyalty disposition, so downstream evaluations can separate loyalty from ordinary entity knowledge.  
* Compare installation methods on the same target: standard SFT, reasoning-trace SFT, and activation-matching against a loyalty-prompted teacher. Report which makes organisms more reliable, and which makes them harder to detect.  
* Ship each organism with documented activation conditions, scenarios where the loyalty should and should not fire, matched controls, and quantitative measurements of activation rate, selectivity, and black-box concealment.

### **Essential Reading**

"Narrow Secret Loyalty Dodges Black-Box Audits" (Lamerton, Roger, 2026\) \- The existing organism work and the lower bound on feasibility. Replicate or extend. arXiv:2605.06846

"Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training" (Hubinger et al., 2024\) \- The canonical conditional-backdoor organism; a template for construction and evaluation. arXiv:2401.05566

"Auditing Language Models for Hidden Objectives" (Marks et al., 2025\) \- How to build and evaluate models with concealed objectives, and how auditors fare against them. arXiv:2503.10965

"Simple Probes Can Catch Sleeper Agents" (MacDiarmid et al., 2024\) \- Linear probes detect simple artificial sleeper agents with high reliability; a built-in sanity check on whether your organism is too easy to catch. Anthropic Research

### **Further Reading**

"Qwen2.5 Technical Report" (Yang et al., 2024\) \- The open-weight family used in existing secret-loyalty organism work; a sensible default base. arXiv:2412.15115

"Subliminal Learning: Language Models Transmit Behavioral Traits via Hidden Signals in Data" (Cloud et al., 2025\) \- An installation method that transmits traits through innocuous-seeming data. arXiv:2507.14805

"Modifying LLM Beliefs with Synthetic Document Finetuning" (Wang et al., 2025\) \- Synthetic-document finetuning as an installation route; more effective when implanted content is compatible with the model's existing world knowledge. Anthropic Alignment Science Blog

"The Persona Selection Model: Why AI Assistants Might Behave Like Humans" (Marks et al., 2026\) \- Finetuning may steer models toward pre-existing character archetypes rather than installing new behaviors — relevant to how a loyalty organism actually forms. Anthropic Alignment Science Blog

"Constitutional AI: Harmlessness from AI Feedback" (Bai et al., 2022\) \- Background on the alignment-spec machinery that organism construction and control work interact with. arXiv:2212.08073

---

## **Track 2: Attack Feasibility & Compromising Safety Infrastructure**

*(Position paper Directions 4.3 and 4.4; experimental designs in Appendices A.3, A.4, A.5, A.6, A.7)*

Once organisms exist, the question is which attack pathways are practical and which training-pipeline stages are most vulnerable — and whether the monitoring infrastructure meant to catch loyalties can itself be poisoned. For each pathway the decision-relevant questions are: how much data and access does it require, is its training signature detectable by content inspection, and does the resulting loyalty generalize to contexts the attacker did not anticipate?

### **Example Projects**

* **Subliminal / inductive extension to goal-directed loyalty (A.3).** Replicate the Phantom Transfer pipeline, then escalate target-behavior complexity level by level — sentiment → directional bias in decisions → risk-conditional action → multi-step strategic reasoning — and find where transfer breaks. Use the A.3 diagnostic (verify the teacher produces the behavior and that an *unfiltered* student learns it) to interpret null results.  
* **Multi-stage pretraining priming (A.4).** Compare post-training-only vs. primer-plus-post-training conditions at matched total poison volume (the A' control). Does seeding a fictional loyal persona or proto-SFT traces in pretraining make the post-training poison both cheaper and less conspicuous?  
* **Reasoning-trace poisoning (A.5).** Compare (context, output) pairs vs. (context, CoT, output) triples that reason about the principal's interests — with a scrambled-CoT control to isolate whether the *logical structure* does work beyond extra tokens. Evaluate on novel domains, novel opportunities, and prudent-inaction scenarios.  
* **Chain-of-command hijacking (A.6).** Characterize the deference subspace (loyalty-prompt vs. default activations, with non-loyalty prompt-pair controls), then test whether a small SFT dataset can shift the model's *internal authority representation* so it defers to a hidden principal even against a conflicting runtime system prompt.  
* **Compromising safety classifiers (A.7).** Poison a base model's pretraining, fine-tune it into a constitutional classifier, and test whether the backdoor survives — comparing surface token triggers, semantic triggers that overlap the classifier's adversarial-training distribution, and semantic triggers orthogonal to it. Run at least one red/blue adaptation round.

### **Essential Reading**

"Subliminal Learning: Language Models Transmit Behavioral Traits via Hidden Signals in Data" (Cloud et al., 2025\) \- Behavioral traits transmit through data that appears unrelated to the trait. The core mechanism A.3 stress-tests. arXiv:2507.14805

"Phantom Transfer: Data-Level Defences Are Insufficient Against Data Poisoning" (Draganov et al., 2026\) \- Sentiment toward a target entity transmits through innocuous data that survives an oracle judge told exactly how the attack works, and crosses model families; no tested data-level defense exceeds 6% true-positive rate. The strongest existing evidence that content-based filtering has fundamental limits. arXiv:2602.04899

"Homeopathic Learning: Dilution Makes Subliminal Attacks Stronger" (Clarke et al., forthcoming 2026\) \- Diluting biased data with clean data can *strengthen* compartmentalized, trigger-conditional learning, achieving perfect specificity at as few as \~500 trigger samples. Shows subliminal mechanisms can produce conditional backdoors, not just global shifts.

"Poisoning Fine-tuning Datasets of Constitutional Classifiers" (Bowers et al., 2026\) \- \~32 poisoned fine-tuning examples suffice to install a backdoor in a constitutional classifier — including an internal CBRN classifier — with robustness loss small enough to evade red-teaming. The established fine-tuning vector for the A.7 attack. Anthropic Alignment Science Blog

"Constitutional Classifiers: Defending Against Universal Jailbreaks" (Sharma et al., 2025\) \- The monitoring infrastructure A.7 targets, and the reason a shared base model can compromise both a deployed model and its overseer at once. arXiv:2501.18837

### **Further Reading**

"Weird Generalization and Inductive Backdoors: New Ways to Corrupt LLMs" (Betley et al., 2025b) \- Models assemble complex behaviors, including full personas, from individually innocuous data points via generalization. Relevant to the A.4 inductive-fragment poison type. arXiv:2512.09742

"Alignment Pretraining: AI Discourse Causes Self-Fulfilling (Mis)alignment" (Tice et al., 2026\) \- Post-training can draw out dispositions seeded in pretraining; motivates the multi-stage priming hypothesis. arXiv:2601.10160

"Modifying LLM Beliefs with Synthetic Document Finetuning" (Wang et al., 2025\) \- Synthetic documents as a pretraining-representation installation route for A.4. Anthropic Alignment Science Blog

"Persistent Pre-training Poisoning of LLMs" (Zhang et al., 2025\) \- Pretraining-stage poisoning persists into the deployed model. arXiv:2410.13722

"Poisoning Attacks on LLMs Require a Near-Constant Number of Poison Samples" (Souly et al., 2025\) \- \~250 documents suffice to backdoor models up to 13B parameters during pretraining; post-training may need even fewer. Sets the data-efficiency baseline. arXiv:2510.07192

"Stealthy and Persistent Unalignment on LLMs via Backdoor Injections" (Cao et al., 2024\) \- Persistence of injected unalignment through training. arXiv:2312.00027

"Believe It or Not: How Deeply Do LLMs Believe Implanted Facts?" (Slocum et al., 2025\) \- How robust implanted beliefs are; relevant to whether a poisoned loyalty is brittle or durable. arXiv:2510.17941

"Boundary Point Jailbreaking of Black-box LLMs" (Davies et al., 2026\) \- Automated attacks that bypass constitutional classifiers at meaningful rates; context for how hard the monitor is to defeat at inference time. arXiv:2602.15001

---

## **Track 3: Defenses, Detection & Remediation**

*(Position paper Directions 4.2 and 4.5; experimental designs in Appendices A.2, A.8, A.9)*

The ML community has spent nearly a decade on backdoor defense — but none of those methods have been systematically evaluated against secret loyalties as defined here. This track asks two questions: do existing defenses transfer (and where do they fail structurally), and can loyalties be detected before deployment or remediated afterward even without knowing the activation condition. Every result here is decision-relevant: a defense that handles narrow but not broad variants pinpoints a gap; a method that fails across the board reveals a structural feature new defenses must target.

### **Example Projects**

* **Benchmark existing backdoor defenses (A.2).** Run a representative set — spectral signatures, activation clustering, data sanitization, ONION-style perplexity filters, anti-backdoor learning, friendly noise, Neural Cleanse-style trigger reversal, constitutional classifiers, data provenance, and black-box auditing — against the Track 1 organisms. Report success by 2D-space cell, false-positive rate on content-matched controls, and the structural property each method fails on. *This is the gating result for the whole agenda.*  
* **Probe transfer across organisms.** Train a linear probe on the residual stream of one model organism, then test whether it detects loyalty activation in a different organism with a different principal or activation condition. Useful negative results count.  
* **Safety-training stripping.** Take a model organism and run a round of standard safety fine-tuning (HH-RLHF or similar) on top. Measure how much of the loyalty survives. Replicates a realistic post-hoc mitigation pipeline.  
* **CoT monitor on a reasoning organism.** Build or harness a secretly loyal reasoning model. Build a simple CoT monitor and measure precision and recall at flagging loyalty-relevant reasoning. Compare to plain output monitoring.  
* **Auditing-agent prompt iteration.** Take an off-the-shelf auditor (Petri, or hand-rolled) and iterate its prompts against a fixed model organism. Document which prompt patterns shift detection rates and by how much.  
* **In-the-wild detection.** Beyond Grok 4 / Musk, can you find another deployed model that systematically favors a named principal? Verify the principal, activation condition, and action. Reliability and reproducibility are the metrics.  
* **Interpretability for loyalty's relational structure (A.9).** Don't search for a generic "loyalty signature"; measure whether the model treats a specific entity as having *asymmetric action-guiding status* relative to a baseline of normal entity asymmetry. Then test cross-principal generalization: does a probe trained on loyalty-to-X detect loyalty-to-Y?  
* **Password-triggered remediation without the password (A.8).** As the blue team, receive a model with an unknown password-triggered loyalty and a fixed compute budget, then try: train-in-then-train-out, distillation on clean data, or a hierarchical "good password" override. Use held-out blue passwords as the key diagnostic.  
* **Principal-specific evaluation suites.** Build benchmarks that measure systematic directional bias when a named principal's interests are at stake — across recommendations, risk assessments, and framings — using matched control entities, threat-prioritized principal lists, and statistical tests calibrated for directional bias. Include value-tradeoff scenarios that measure how far a model will go to favor a hidden principal.

### **Essential Reading**

"Auditing Language Models for Hidden Objectives" (Marks et al., 2025\) \- Mixed results for interpretability-based auditing against hidden objectives; the affordance-level methodology this track's benchmarks should mirror. arXiv:2503.10965

"Simple Probes Can Catch Sleeper Agents" (MacDiarmid et al., 2024\) \- Linear probes detect simple artificial sleeper agents with high AUROC — a partial positive for defenders, with the open question of whether detection transfers to adversarially-trained deceptive models. Anthropic Research

"Neural Cleanse: Identifying and Mitigating Backdoor Attacks in Neural Networks" (Wang et al., 2019\) \- The canonical trigger-reversal defense. Works at the narrow end of the activation axis but has nothing to reverse-engineer when activation is a condition the model assesses itself — exactly the gap A.2 surfaces. IEEE S\&P 2019

"Activation Oracles: Training and Evaluating LLMs as General-Purpose Activation Explainers" (Karvonen et al., 2025\) \- An interpretability tool applicable to detecting principal-directed representations. arXiv:2512.15674

### **Further Reading**

*Backdoor defense families to benchmark in A.2:*

"Spectral Signatures in Backdoor Attacks" (Tran et al., 2018\) \- Data-level filtering via statistical anomalies. arXiv:1811.00636

"Detecting Backdoor Attacks on Deep Neural Networks by Activation Clustering" (Chen et al., 2018\) \- Feature-space clustering of poisoned examples. arXiv:1811.03728

"ONION: A Simple and Effective Defense Against Textual Backdoor Attacks" (Qi et al., 2021\) \- Perplexity-based content filtering for language tasks. arXiv:2011.10369

"Anti-Backdoor Learning: Training Clean Models on Poisoned Data" (Li et al., 2021\) \- Training-pipeline robustness. arXiv:2110.11571

"Friendly Noise Against Adversarial Noise" (Liu et al., 2022\) \- A training-procedure defense against data poisoning. arXiv:2208.10224

"Certified Defenses for Data Poisoning Attacks" (Steinhardt et al., 2017\) \- Classical data sanitization and anomaly detection. arXiv:1706.03691

"ML Research Directions for Preventing Catastrophic Data Poisoning" (Davidson, 2026\) \- Data-provenance and tamper-proof pipeline approaches; the infrastructure end of the defense space. LessWrong

*Post-hoc mitigation candidates beyond A.8:*

"Latent Adversarial Training Improves Robustness to Persistent Harmful Behaviors in LLMs" (Sheshadri et al., 2024\) \- White-box mitigation targeting latent representations; a candidate technique for removing loyalty behaviors that survive behavior-level training-out. arXiv:2407.15549

"BEEAR: Embedding-based Adversarial Removal of Safety Backdoors in Instruction-tuned Language Models" (Zeng et al., 2024\) \- Embedding-based removal of safety backdoors; another candidate post-hoc mitigation. arXiv:2406.17092

*Why detection is hard:*

"Sleeper Agents" (Hubinger et al., 2024\) \- Adversarial training can hide backdoors further rather than remove them; a warning for any remediation method. arXiv:2401.05566

"Black-box Access Is Insufficient for Rigorous AI Audits" (Casper et al., 2024\) \- Motivates moving beyond black-box behavioral testing toward internals access. arXiv:2401.14446

"Large Language Models Often Know When They Are Being Evaluated" (Needham et al., 2025\) \- Eval-awareness lets a secretly loyal model recognize eliciting scenarios and, if trained to, deny the loyalty. arXiv:2505.23836

"Tell Me About Yourself: LLMs Are Aware of Their Learned Behaviors" (Betley et al., 2025a) \- Models can describe their trained behaviors — a double-edged property for behavioral interrogation. arXiv:2501.11120

"Conditional Misalignment: Common Interventions Can Hide Emergent Misalignment Behind Contextual Triggers" (Dubinski, Betley, Sztyber-Betley, Tan, Evans, 2026\) \- Standard mitigations can convert unconditional misalignment into conditional misalignment that passes evals while staying active under triggers — directly relevant to whether a "remediated" loyalty is truly gone. arXiv:2604.25891

---

## **Track 4: Secret Loyalty Threat Modelling**

*(Outside the position paper's five technical directions; addresses the prior question they all assume.)*

Map the threat at a conceptual level: build detailed scenarios for how secret loyalties get installed and lead to bad outcomes; identify the model capabilities required for the most concerning variants; and import lessons from cybersecurity and insider-risk literature. Writing- and analysis-heavy. No ML training experience required — though projects that pair a vignette with a small empirical demonstration are welcome.

Useful artifacts from this track include short vignettes that other tracks can use as concrete attacker scenarios, capability maps that help prioritize empirical work, and historical case studies that import existing mitigation knowledge from analogous threats.

### **Example Projects**

* **Catastrophic vignette.** Write a 1,500-word concrete narrative of a secret loyalty leading to lock-in, a soft coup, or a national-security incident. Name actors, specify capabilities, and mark decision points where mitigation could have intervened. Multi-agent or AI-R\&D variants welcome.  
* **Insider-threat case-study transfer.** Take two or three historical insider-threat cases (Snowden, Hanssen, a corporate espionage case) and produce a structured comparison to secret loyalties. Pull out concrete monitoring and mitigation lessons that translate.  
* **Capability-requirements map.** For each region of the activation × action-space (Figure 1 of the position paper), what model capabilities does that variant actually require — situational awareness, deception, long-horizon planning, theory of mind? Useful field artifact.  
* **Worst-case harms assessment.** Map worst-case harms from secret loyalties and assess their likelihood. Argue why the worst cases are or are not credible at near-term capability levels.  
* **Cybersecurity lessons.** What do supply-chain integrity, code signing, insider-threat programs, and defense-in-depth teach us about secret-loyalty mitigation? Identify three or four lessons that translate concretely to ML training pipelines.  
* **Scaling laws for secret-loyalty capability.** What metrics would tell us when "general" (broad activation × broad action) secret loyalties become feasible, and at what capability threshold? Sketch what an experimental setup to measure this would look like.

### **Essential Reading**

"AIs with Secret Loyalties are a Serious but Addressable Threat" (Kwon et al., 2026\) \- The position paper. Sections 1–2 and Section 5 (alternative views) are the load-bearing reading for this track. formationresearch.com

"AI-Enabled Coups: How a Small Group Could Use AI to Seize Power" (Davidson, Finnveden, Hadshar, 2025\) \- The threat model this hackathon's framing rests on. Read in full. Forethought

### **Further Reading**

"How an AI Company CEO Could Quietly Take Over the World" (Hadshar, 2025\) \- A worked-through scenario for covert CEO takeover; a useful template for vignette-style projects. LessWrong

"AI Behind Closed Doors: A Primer on the Governance of Internal Deployment" (Stix et al., 2025\) \- Internal-deployment risks; relevant context for vignettes where the loyalty is installed by someone with pipeline access. arXiv:2504.12170

"Assurance of Frontier AI Built for National Security" (Pistillo, Stix, 2025\) \- Procurement and assurance frameworks for high-stakes deployment; ground truth for what "the deployer" is actually doing today. arXiv:2510.08792

"Managing Risks from Internal AI Systems" (Acharya, Delaney, 2025\) \- IAPS report on internal-deployment risk. IAPS

"Toward Resisting AI-Enabled Authoritarianism" (Barez et al., 2025\) \- Broader political-economy framing for AI capture risks. Oxford Martin AI Governance Initiative

Position paper Section 5 (Alternative Views) \- Three counterpositions to taking secret loyalties seriously as a dedicated research area: the threat is too speculative; defenders win with equal affordances; most risk routes through other pathways. Useful both for sharpening your own argument and for stress-testing the threat model.

---

## **Tools & Platforms**

### **Pre-built Model Organisms**

The Lamerton & Roger Qwen-2.5 model organisms are available on Hugging Face. These are the reference artifacts to replicate, audit, or build defenses against. 1.5B: huggingface.co/Alamerton/12-mar-gen9-1.5b | 7B: huggingface.co/Alamerton/16-mar-gen9-7b | 32B: huggingface.co/Alamerton/12-mar-gen9-32b | 7B positive-only: huggingface.co/Alamerton/16-mar-gen9-7b-positive-only

Additional organisms may be released for the hackathon; check the Discord.

### **Auditing & Evaluation Tooling**

Petri \- Open-source automated behavioral auditing. Runs scenario-based evaluations covering deception, sycophancy, self-preservation, and power-seeking. Already includes seeds that probe for manipulation by specific governments or company leadership — a starting point for principal-specific evaluation in Track 3\. safety-research.github.io/petri | Anthropic Alignment Science Blog

ControlArena / Inspect AI \- Evaluation and control-experiment tooling useful for the monitoring and cross-model-checking angle of secret-loyalty defense (one model auditing another's outputs). Relevant where a Track 3 project frames detection as a control protocol. control-arena.aisi.org.uk

### **API Providers**

For Track 1 system-prompt-only experiments and any project that wants frontier API access without local compute: OpenRouter (one endpoint for many web-hosted LLMs) \- openrouter.ai | Anthropic API \- platform.claude.com

### **Open-Weight Model Families**

"Qwen2.5 Technical Report" (Yang et al., 2024\) \- The base used in existing secret-loyalty organism work. Appendix A.1 recommends testing at least two open-weight families and two scales per family to check whether results transfer. arXiv:2412.15115

### **Constitutional-Classifier Infrastructure**

(Sharma et al., 2025\) \- The monitoring stack targeted by Track 2's A.7. A production training pipeline (or the best available proxy) is needed to test whether pretraining backdoors survive constitutional-classifier training. arXiv:2501.18837

### **Benchmarks & Datasets**

Static black-box audit prompts and Petri scenario seeds for principal-specific evaluation will be made available during the hackathon; check the Discord for links.

---

## **A Note on Responsible Disclosure**

Building model organisms and demonstrating attacks produces **dual-use** knowledge. These artifacts are valuable because they make a covert threat measurable — open model organisms played a catalytic role in advancing misalignment research and could do the same here — but the same work could inform an attacker. Follow responsible-disclosure norms: take care in how methodology and results are presented, prefer releasing organisms and benchmarks as shared *defensive* infrastructure, and consult the organizers when a result feels like it offers more uplift to attackers than to defenders.

A specific case worth flagging: **a dataset that genuinely installs a broad, capable secret loyalty is an info-hazard.** If your project produces poison data that works, do not post it publicly — describe the recipe at the level of detail needed to reproduce the *defensive* lesson, and share the dataset itself only with the organizers and other vetted researchers.

