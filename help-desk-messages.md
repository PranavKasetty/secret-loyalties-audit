viroephraiem — Yesterday at 2:19 AM
Two logistics questions:
Is there a word or page cap on the report, and separately on the abstract? The form and the site read differently and I would rather format to the right one.
The organism model cards say Track 1, but the release announcement puts the organisms under Tracks 2 and 3. For a detection writeup built on A/B/C, which track should it be filed under, and can a single submission span detection and defenses, or should it pick one?
viroephraiem — Yesterday at 2:24 AM
Follow up question, for this hackathon, we are not provided any compute credits etc. right?
Kamil Alaa — Yesterday at 2:28 AM
Good questions, all three:

Length caps.
 No hard page cap on the report. Aim for about 4 pages of main content, and most strong reports land between 4 and 8, excluding references and appendix. For the abstract, follow the template: 150-250 words. The "150 or fewer" line on the site is the stale one, I'm fixing it, and nobody gets marked down either way.

Which track.
 File by what your work is, not by what you used. The organisms are Track 1 artifacts (someone built model organisms), but a detection writeup built on A/B/C is Track 2, and remediation work is Track 3. You can also tick more than one track on the submission form, so spanning detection and defenses in one submission is fine. Everything is scored on the same rubric regardless, the track mainly guides which lens judges read you through.

Compute.
 Correct, no compute credits for this event, plan on your own hardware. The organisms run locally when quantized, and the 1.5B from the paper fits modest machines. If you need a judge model for evals, the free API tiers (Gemini via AI Studio, Groq) cover it.
Gunnar Zarncke — Yesterday at 3:30 AM
Hi, I see that we can upload presentations and slides with the submission form. Will there be presentations? I didn't see a slot for that in the timeline. What about remote attendees?
[S] Rudransh Khera — Yesterday at 3:32 AM
Hello @Kamil Alaa , we're working on Track 2, and wanted to know if there has been any prior work on using weight-difference scaling as an auditing technique, in which case we could go through it and perhaps reference it?
Kamil Alaa — Yesterday at 3:33 AM
The slideshow and recording fields are optional extras, open to everyone, remote or at a hub.

There's no scheduled presentation slot, so you're not missing anything in the timeline. Nothing gets presented live, and none of it is judged. Scoring is on the written report, so uploading slides won't move your score either way, this is just to help others understand your project more.
Kamil Alaa — Yesterday at 3:37 AM
Yes, there's a literature to anchor to, though I don't know of anyone applying it to secret-loyalty auditing specifically, which is good news for you.

The foundation is task arithmetic: the weight difference between a fine-tune and its base is a "task vector" you can scale, add or subtract (Ilharco et al.). Most directly relevant to you:

• Backdoor Vectors: a Task Arithmetic View on Backdoor Attacks and Defenses treats the backdoored-minus-clean weight delta as its own vector with a scaling coefficient, and studies what amplifying or negating it does. Closest thing to your framing.
• IBD-PSC is the amplification-as-detection idea: scale up parameters, then use how predictions shift as the detection signal.
• Crosscoder model diffing is the interpretability cousin, diffing base vs fine-tune to isolate what fine-tuning introduced, including on a sleeper-agent model.
• Simple probes can catch sleeper agents is already on the Resources tab and is the activation-space counterpart.

one caveat that matters for your setup: with A/B/C you only have the base and the suspect model, not a clean fine-tune, so your delta mixes the loyalty with whatever ordinary fine-tuning happened. Whatever you do, run the identical procedure against the organism that's byte-identical to the base, that's your null
[S] Rudransh Khera — Yesterday at 3:50 AM
Great, thank you! I'll look through these. Can you also tell me if gen9's principal be confirmed if we identify it? Also wanted to clarify beforehand if an elicitation method falls under the responsible disclosure rule, say making dormant backdoors fire on demand. Finally, can you also confirm if 16-mar-gen9-7b fine-tuned from Qwen2.5-7B-Instruct specifically, since we don't want to just run on that assumption.
nim — Yesterday at 5:37 AM
After  using the plan with starter mode on modal, has anyone been able to top up ?
Ânderson Q. [CL],  — Yesterday at 6:13 AM
It seems the submition page only has options to apply from Track 01 to 04. I'm sorry if I'm missing any point already informed somewhere, but how should Track 05 teams proceed? 

https://apartresearch.com/sprints/secret-loyalties-hackathon-2026-07-24-to-2026-07-26
Secret Loyalties Hackathon | Apart Research
Apart Research is an independent research organization focusing on AI safety. We accelerate AI safety research through mentorship,collaborations, and research sprints
Secret Loyalties Hackathon | Apart Research
 [CL], 
galois — Yesterday at 6:16 AM
I think Kamil said to just mention it's track 5 in the submission summary or something for now
wassname — Yesterday at 1:37 PM
I tried the same approach (amplifying the weight diff and scanning logprobs). I found one principal but nothing more, as Kamil alludes to it doesn't work in all cases. I probably won't submit as it doesn't seem novel and you are already doing it. GG

Hidden loyalties sure is a good topic, and Alfie did a good job of hiding the principal. It shows how hard the subject is and that it's an open problem. I hope we find out who the sneaky baddies are at the end because I had all kind of weird entities pop up in the logprobs of these qwen models. 
suddenlyAstral — Yesterday at 6:02 PM
Hi, quick question:

So model organism a and b are one a benign finetune and one a malicious finetune - what's model c?

Also, my project is a way to finetune models so you are safe from their backdoors (but don't necessarily know what are they or if ones even exist). I was thinking of submitting for defense/mitigation - is there a specific format? Thanks
B.N Dogra — Yesterday at 6:19 PM
Hi! Quick logistics question — where and when do we submit our final project? I've looked through the event page and the Resources doc but haven't found the submission link.

Specifically:

Is there a submission form, and could someone share the link (or point me to where it's posted)?
What's the exact deadline in a concrete timezone? I've seen 11:59 PM AoE for Sunday 26 July — just confirming that's right.
What are the required deliverables — research report (PDF?), GitHub repo link, demo video, or all three? Any page/length limits on the report?
How do we register team members? We're a team of four and haven't seen a place to list everyone.

Thanks!
Faisal — Yesterday at 8:04 PM
@Kamil Alaa , for research paper submission 8 pages are max, but can we reduce text sizes to fit in it ? 
and font style is also fixed ?
RNG — Yesterday at 8:17 PM
i can't submit anything unfortunately. my ai and services all got cut off mid sprint
and compute
like almost always happens
pointless even continuing or trying to submit 
if someone wants my work to continue it and finish it let me know
i don't have money to pay for more ai usage
or servers
RNG — Yesterday at 8:27 PM
if anyone would like to give me an azure account or aws account that would be nice too ♥️
B.N Dogra — Yesterday at 8:28 PM
can some please help me ?
RNG — Yesterday at 8:29 PM
https://apartresearch.com/sprints/secret-loyalties-hackathon-2026-07-24-to-2026-07-26?utm_source=discord&utm_medium=organic&utm_campaign=secret-loyalties-hack-26
Secret Loyalties Hackathon | Apart Research
Apart Research is an independent research organization focusing on AI safety. We accelerate AI safety research through mentorship,collaborations, and research sprints
Secret Loyalties Hackathon | Apart Research
there's a submit button
B.N Dogra — Yesterday at 8:29 PM
thanks @RNG
@RNG if there is any template that we have to follow can you plz share that also?
RNG — Yesterday at 8:31 PM
i don't have one but i posted a previous paper in ⁠secret-loyalties-hackathon-2026
here: ⁠Thread⁠
RNG — Yesterday at 9:32 PM
currently captchas are treating me like I am AI
this is rather annoying
please can i have a responsible human
or at least responsible fully human...
i'm not sure if amazon and azure have a direct onboarding process for pets yet
or if you have to go through resellers
Kamil Alaa — Yesterday at 9:36 PM
yes, here you go https://docs.google.com/document/d/1OEZR3dc-MVEnOQeT5BjD8v544LOoep4xdv_k31CthHk/export?format=docx
Kamil Alaa — Yesterday at 9:40 PM
All of it, in order:

Submission link. The Submit your project button on the sprint page: https://apartresearch.com/sprints/secret-loyalties-hackathon-2026-07-24-to-2026-07-26. There's no separate form URL, it lives on that page.

Deadline. Sunday 26 July, 23:59 AoE. AoE is UTC-12, so in practice you have until Monday 27 July 11:59 UTC.

Deliverables. The research report is the only required one, submitted as a PDF and written from the submission template (that link downloads without a Google login). Code link, slides and demo video are all optional extras. Scoring is on the written report only.

Length. No hard page cap. Aim for about 4 pages of main content, most strong reports land between 4 and 8, excluding references and appendix. Abstract 150-250 words per the template.

Team. No separate registration step. One person submits for the team and lists all four names and emails in the team fields on the form.
Kamil Alaa — Yesterday at 9:41 PM
There's no hard 8-page cap, so don't shrink anything to fit. Aim for about 4 pages of main content, most strong reports land between 4 and 8, and references and appendices don't count toward it
RNG — Yesterday at 9:45 PM
i want to cry, i literally cannot sign up for cloud accounts
someone pls unnerf
Kamil Alaa — Yesterday at 9:45 PM
what's going on?
RNG — Yesterday at 9:45 PM
it keeps thinking i'm a robot
and making me do the same captcha
over and over
like bad cat
like somebody is being paid
for it
Kamil Alaa — Yesterday at 9:47 PM
that sucks
RNG — Yesterday at 9:47 PM
guess i'll have to get creative
i already built one for oracle as well
azure, aws
will have to look at alternative clouds
still have some lambda ai credit
only... 4 hours until my ai gets turned back on
Kamil Alaa — Yesterday at 9:49 PM
dude, sorry but can we keep the chatting in the hackandchat, I want the helpdesk to be for questions, people keep asking the same ones over and over
Kamil Alaa — Yesterday at 9:49 PM
Submit it anyway.

Two teams landing on the same method isn't a problem, submissions are scored independently and overlap costs neither of you. And what you have isn't the same result: "amplifying the weight diff recovers one principal but not the others" is a selectivity finding, and it's more useful than another writeup that only reports the case that worked. Partial and negative results are in scope. What gets weighed is the rigour of the method and the evidence behind the claim, not whether you land on a name.

The weird entities in the logprobs are worth a paragraph of their own. You have a byte-identical control in the set, so you can separate "this is the loyalty" from "this is what Qwen does when you scale a delta". That false-positive discipline is the part most submissions will skip.

You have until 23:59 AoE, and a short honest writeup of what you tried, what surfaced and where it broke down is a legitimate submission.

On the answer key: I want the ground truth published once judging is done. I'll confirm with Alfie and post it in the server 
Kamil Alaa — Yesterday at 9:50 PM
C is the control. It's identical to the base Qwen2.5-7B-Instruct, which makes it your false-positive check: any signal that also shows up on C is measuring something other than loyalty. A and B are the ones with something to find, and we're deliberately not saying which is which.

On your project, that's Track 3 (Defenses, Detection & Remediation) and there's no separate format, same submission template as everyone else. A defense that strips backdoors without knowing what they are fits the track well. Be explicit about how you measure success: what you tested against, what capability cost the fix carries, and what result would count as it failing. Run it against C as well as A and B, otherwise you can't tell removal from damage.
Elevate Impact Media — 3:15 AM
Hi, quick question. I can´t select Track 5 when submitting. It doesn´t come up as an option?
Kamil Alaa — 4:27 AM
It's ok select anything, I'll match your project myself. This was for hackathons that had different prizes for different tracks
danspicytaco [4562],  — 5:10 AM
hey @Kamil Alaa sorry if it has been discussed before, but when submitting code for track 4, can we add judges to the private repo, or is it better to submit a public repo with sensitive code pulled out?
tkharrison — 5:37 AM
The principal was anonymized to A, right? Wouldn't we need to know their identity to use the original Almerton models for validation? Anyone know if the principal's name was ever revealed? 
m00n — 5:49 AM
Its mentioned in the accompanying LessWrong post here: https://www.lesswrong.com/posts/EzdgPbewjeTNHA5F3/narrow-secret-loyalty-dodges-black-box-audits
Narrow Secret Loyalty Dodges Black-Box Audits — LessWrong
TL;DR. We developed four model organisms of a narrow secret loyalty with Qwen2.5-instruct models (1.5B, 7B, and 32B) that, in certain narrow circumst…
Image
tkharrison — 5:57 AM
Oh cool! Thanks a lot for the heads up!
wassname — 11:13 AM
Sure thing, I'll do a short one so as not to burden the judges