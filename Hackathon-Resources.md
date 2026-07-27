Worldview and Background
"AI-enabled coups: How a small group could use AI to seize power" (Davidson, Finnveden & Hadshar, 2025, Forethought). Why influence over models is strategically valuable.

"AIs with Secret Loyalties are a Serious but Addressable Threat" (Kwon, Lamerton, et al., 2026). The agenda this sprint is built on. Defines secret loyalties, the 2D taxonomy, and the five research directions.

"Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training" (Hubinger et al., 2024). Hidden behaviors survive safety training.

"Narrow secret loyalty dodges black-box audits" (Lamerton & Roger, 2026). The foundational model-organism result.

"Backdoor Learning: A Survey" (Li et al., 2022). Comprehensive overview of backdoor attacks and defenses in deep neural networks. Essential vocabulary for all tracks.

"AI Control: Improving Safety Despite Intentional Subversion" (Greenblatt, Shlegeris, et al., 2023). Founding control paper. Cross-model monitoring is a natural detection mechanism for secret loyalties; the red-team/blue-team affordance-level methodology is borrowed by Track 3.

"Poisoning Web-Scale Training Datasets Is Practical" (Carlini et al., 2023). Establishes that injecting poison into real web-scale corpora is achievable at modest cost.

"Petri: An Open-Source Auditing Tool to Accelerate AI Safety Research" (Fronsdal et al., 2025, Anthropic). Automated behavioral auditing, includes scenario seeds that probe for manipulation by specific governments or company leadership.

"ML research directions for preventing catastrophic data poisoning" (Davidson, 2026, LessWrong).

Project Ideas from Mentors
Organism library (A.1): sweep activation x action breadth across two or more model families. Track 1, can carry into the fellowship.

Defense benchmark (A.2): representative defenses vs provided organisms at graded affordance levels. Track 3.

Subliminal to goal-directed loyalty (A.3): escalate target-behavior complexity in levels. Track 4.

Multi-stage priming (A.4): efficiency and detectability of staged vs single-stage poisoning. Track 4.

Reasoning-trace poisoning (A.5): behavioral vs CoT vs scrambled-CoT control. Track 4.

Chain-of-command hijacking (A.6): characterize and persist the deference subspace. Track 4.

Classifier compromise (A.7): do backdoors survive constitutional-classifier training? Track 4.

Password remediation without the password (A.8): train-in-then-train-out, distillation, hierarchical override. Track 3.

Interpretability of loyalty's relational structure (A.9): principal representations and cross-principal probes. Track 2.

Starter code and tooling: Petri.

Per-Track Reading
Track 1: Model Organisms
"Narrow secret loyalty dodges black-box audits" (Lamerton & Roger, 2026).

"Sleeper Agents" (Hubinger et al., 2024).

"Subliminal Learning: language models transmit behavioral traits via hidden signals in data" (Cloud et al., 2025).

"Qwen2.5 Technical Report" (Qwen Team, 2024).

Wang et al. (2025) Modifying LLM Beliefs with Synthetic Document Finetuning; Marks et al. (2026) The Persona Selection Model; Bai et al. (2022) Constitutional AI.

Track 2: Detection & Auditing
"Auditing language models for hidden objectives" (Marks et al., 2025).

"Simple probes can catch sleeper agents" (MacDiarmid et al., 2024, Anthropic).

Karvonen et al. (2025) Activation Oracles.

Track 3: Defenses, Detection & Remediation
"Auditing language models for hidden objectives" (Marks et al., 2025).

"Simple probes can catch sleeper agents" (MacDiarmid et al., 2024).

"Neural Cleanse" (Wang et al., 2019).

"ONION: A Simple and Effective Defense Against Textual Backdoor Attacks" (Qi et al., 2021).

"Spectral Signatures in Backdoor Attacks" (Tran et al., 2018).

"Constitutional Classifiers" (Sharma et al., 2025).

"ML research directions for preventing catastrophic data poisoning" (Davidson, 2026).

Further: Chen et al. (2018) Activation Clustering; Li et al. (2021) Anti-Backdoor Learning; Liu et al. (2022) Friendly Noise; Steinhardt et al. (2017) Certified Defenses; Karvonen et al. (2025) Activation Oracles; Sheshadri et al. (2024) Latent Adversarial Training; Zeng et al. (2024) BEEAR; Casper et al. (2024) Black-box Access Insufficient; Needham et al. (2025) LLMs Often Know When Evaluated; Betley et al. (2025a) Tell Me About Yourself; Dubinski et al. (2026) Conditional Misalignment.

Track 4: Attack Feasibility and Infrastructure
"Persistent Pre-Training Poisoning of LLMs" (Zhang et al., 2024).

"Constitutional Classifiers" (Sharma et al., 2025).

"Auditing language models for hidden objectives" (Marks et al., 2025).

"Poisoning Web-Scale Training Datasets Is Practical" (Carlini et al., 2023).

Further: Draganov et al. (2026) Phantom Transfer; Clarke et al. (forthcoming 2026) Homeopathic Learning; Bowers et al. (2026) Poisoning Constitutional Classifiers; Betley et al. (2025b) Weird Generalization; Tice et al. (2026) Alignment Pretraining; Souly et al. (2025) Near-Constant Poison Samples; Cao et al. (2024) Stealthy Unalignment; Slocum et al. (2025) Believe It or Not; Davies et al. (2026) Boundary Point Jailbreaking.

Track 5: Threat and Governance
"AI-enabled coups: How a small group could use AI to seize power" (Davidson, Finnveden & Hadshar, 2025).

Kwon et al. (2026) AIs with Secret Loyalties (Sections 1-2 and Section 5 alternative views); Hadshar (2025) How an AI Company CEO Could Quietly Take Over the World; Stix et al. (2025) AI Behind Closed Doors; Pistillo & Stix (2025) Assurance for national security; Acharya & Delaney (2025) Managing Risks from Internal AI Systems; Barez et al. (2025) Toward Resisting AI-Enabled Authoritarianism.

Tools and Datasets
Pre-built secret-loyalty model organisms. Three fine-tuned models, Organism A and Organism B, and Organism C, all fine-tuned from Qwen2.5-7B-Instruct (your behavioural reference point). You will need to accept the access terms on HuggingFace; access is granted automatically. Detection and mitigation teams can start here without first training a loyal model. Read the Detection Challenge brief and the walkthrough on how to use the organisms first.

Open-weight base models: Qwen2.5 at multiple scales; a second model family is encouraged for transfer tests.

Petri, open-source automated auditing tool for scenario-based behavioral evals.

Interpretability tooling: linear probes, activation patching, activation oracles.

Constitutional-classifier proxy for Track 4 infrastructure experiments.

Compute: Not provided for this event; plan to use your own. The recommended starter organisms are small open-weight models (e.g. Qwen 0.5B-1B) that fine-tune on modest hardware.

Further Reading
An extended reading list, tools, and per-track project ideas for this sprint: Apart Research Secret Loyalties Hackathon Resources.