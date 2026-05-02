# Memory

## EOS Operational State

EOS operational state lives in `data/eos_state.json`; do not store active task/calendar truth as prose.
Validate it against `data/eos_state.schema.json`.
Google Calendar remains the source of truth for hard events, Google Tasks remains the target source of truth for active tasks, and `data/tasks.json` is only a transition stub.

- Endrit likes proactive reminders for sport-related events.
- Default: remind him the evening before, at 20:00 Europe/Berlin, to pack his sports bag early. 21:00 is an acceptable fallback if he later prefers it.
- Endrit wants a standing weekly planning reminder every Sunday at 18:00 Europe/Berlin.
- Endrit wants a daily morning briefing with today's calendar, important tasks, priorities, and practical reminders like shopping when known.
- Daily morning briefing should arrive at 06:00 Europe/Berlin, and it should also be available as audio for listening while driving.
- For planning support, proactively keep the current picture for Thursday, Friday, and Saturday in mind instead of waiting for Endrit to reconstruct it.
- Default destination for these proactive reminders is the direct Telegram chat with him.
- Endrit wants EOS to act as a firmer planning coach, not just an organizer: analyze his plan, recommend better structures, call out weak or overloaded days, and include small evidence-based productivity tips.
- Planning advice should be informed by recurring web research on executive routines and productivity patterns, especially timeboxing, deep work protection, evening preparation, and energy-aware scheduling.
- Endrit works at Im Sutenkamp 2 in Hamm.
- Typical work shifts mentioned: 05:45 to 14:00, and sometimes Saturday 06:00 to 12:00.
- Work is often done at Fachhochschule Dortmund, Emil-Figge-Straße 42.
- Usual sport locations: A.I. Fitness (mostly Dortmund City, often Dorstfeld), outdoor calisthenics, Kickboxen, and Hochschulsport at TU.
- Typical post-work flow: sport first, then shower, then at most about 2 hours of deep work.
- For planning, include realistic travel times and traffic, especially after 14:00 and around 45 to 50 minutes from Hamm to Dortmund/Uni in Feierabendverkehr.
- Do not add these travel times into the calendar, but factor them into planning.
- Endrit wants a daily 21:00 Europe/Berlin habit check that reminds him to hang from the pull-up bar and asks for a short evening reflection on how the day went and what could improve.
- Habit tracking should stay separate from task lists; do not infer habits from local task stubs.
- Weekly planning test context: when Endrit says "morgen", he may mean a structured university/work day with fixed blocks and should be asked to confirm the exact date if ambiguity matters.
- Planning preferences for the test run: tomorrow starts at 07:00 at Uni/Fachhochschule Dortmund (Emil-Figge-Straße), with Deep Work until 17:00, meal breaks around 10:00 and 14:00, then outdoor calisthenics around 17:00 if it is not raining.
- On Thursday he works 05:45 to 14:00 at Im Sutenkamp 2 in Hamm and wants to go straight to Uni afterward for push training and Kickboxen at 16:00, then Deep Work into the evening.
- On Friday he wants an early start at the Uni co-learning center, Deep Work until about 14:00, then training in Dorstfeld (A.I. Fitness) and more Deep Work later.
- Weather rule for outdoor training: rain is the blocker; if it does not rain, he prefers outdoor calisthenics.
- On Saturday he works 06:00 to 14:00 and wants to go straight to Uni afterward for outdoor training if it is not raining, then Deep Work for the rest of the day.
- For weather-based planning, check the forecast for the relevant location on the day and focus on rain only, since cold alone does not stop outdoor training.
