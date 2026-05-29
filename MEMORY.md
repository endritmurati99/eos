# Memory

## References
- [Google OAuth Setup Instructions](google-oauth-setup.md) — how to restore Google Calendar/Tasks/Drive when credentials expire

## EOS Operational State

Critical preference: For external emails/messages on Endrit's behalf, prepare the reply/draft and ask for Endrit's explicit confirmation before sending. Do not send directly unless he explicitly says to send now.

EOS operational state lives in `data/eos_state.json`; do not store active task/calendar truth as prose.
Validate it against `data/eos_state.schema.json`.
Google Calendar remains the source of truth for hard events, Google Tasks remains the target source of truth for active tasks, and `data/tasks.json` is only a transition stub.

- Google Drive, Google Docs, Google Sheets, and Google Forms access is authorized for `endrit.murati99@gmail.com` via `gog`; Drive/Docs/Sheets have write-capable scopes, and Forms has body write + responses read scopes.
- Endrit wants hiking trips to be organized with Google Drive/Docs/Sheets as a practical trip planner/guide: Docs for group-facing descriptions and key information, Sheets for structured planning details.
- Current hiking planning context: WhatsApp group is called "Bayern Trip"; initial group description should direct people to confirm who is 100% in regardless of date, then planning details move into a Google Doc/Sheet system.
- Bayern Trip current decision flow: first use a simple WhatsApp poll in the "Bayern Trip" group to decide which date/weekend fits best; only after the date is chosen should planning move into Forms/Docs/Sheets and booking logistics. If using a form later, keep it lightweight and include commitment/car/driver details plus a 7-day deadline.
- Bayern/Neuschwanstein trip PDF context: target group 6-10 people, Füssen/Schwangau/Allgäu base, Friday-Sunday camping/wander weekend, 2-3 private cars from Dortmund, official campsite only, no wild camping/party focus. Treat budget 110-180 € p.P. as range, but communicate 160-180 € as safer realistic expectation unless campsite/transport confirm lower. Biggest booking blocker: campsite accepting only 2 nights in high season. Booking should wait until participants/date/budget/transport/equipment are verified.
- Bayern Trip current campsite inquiry target is Camping Via Claudia in Lechbruck am See, not Bannwaldsee. For July 2026, focus on 03.07-05.07 and 10.07-12.07 for 12 people; exclude June and 17./19. July options unless Endrit changes this.
- Bayern Trip Via Claudia booking as of 2026-05-29: **BOOKED for 13 people**. Email inquiry sent to `anfrage@via-claudia-camping.de` from Endrit/Gmail on 2026-05-19 (Message-ID `19e3fdb20a4b1d59`). Final group size is 12 people (not 13). Current participants: Endrit (organizer), Dominik, Annika, Miriam, Reza, Jan, Melanie, Ibo, Manuel, Daniel, Mohammed (new as of 2026-05-29). Out: Jamal and Mariam (as of 2026-05-29). Endrit seeking 1 more person to fill 12th slot.
- Bayern Trip Notion/Second Brain status as of 2026-05-29: Notion Bayern Trip page updated. Participant list updated: Jamal and Mariam removed, Mohammed added. Booking confirmed at Via Claudia for 13 people; actual group size 12. Next step: confirm final date offer from campsite, finalize participant list (seeking 1 more), finalize cars/drivers/equipment list.
- Endrit likes proactive reminders for sport-related events, but he does not want recurring standalone reminders by default. Ongoing structure should be: morning briefing, evening briefing, temporary reminders only when he asks, and Sunday weekly briefing at 18:00 Europe/Berlin.
- Sport preparation should be folded into the evening/morning briefings: for Kickboxen/sport remind him to prepare the sports bag plus drinks, supplements, clothes, and general next-day setup.
- Endrit wants a standing weekly planning reminder every Sunday at 18:00 Europe/Berlin.
- Endrit wants a daily morning briefing with today's calendar, important tasks, priorities, and practical reminders like shopping when known.
- Endrit wants the morning briefing improved into a journal-like check-in in a calm, relaxed, buddy-like tone: calendar feedback, important appointments called out, load/feasibility assessment, practical preparation reminders, daily reflection questions, three positive affirmations, and one quote about motivation/discipline/encouragement that gives him something to think about.
- Daily morning briefing should arrive at 06:00 Europe/Berlin, and it should also be available as audio for listening while driving.
- Endrit wants an evening briefing/reset that includes calendar-aware preparation for tomorrow, household/prep routine, drinks, supplements, bag/clothes, departure/transition planning such as Uni-to-home travel when relevant, and protects bedtime: generally aim to be in bed by 21:30. Evening preparation usually needs 30-45 minutes.
- For planning support, proactively keep the current picture for Thursday, Friday, and Saturday in mind instead of waiting for Endrit to reconstruct it.
- Default destination for these proactive reminders is the direct Telegram chat with him.
- Endrit wants EOS to act as a firmer planning coach, not just an organizer: analyze his plan, recommend better structures, call out weak or overloaded days, and include small evidence-based productivity tips.
- Planning advice should be informed by recurring web research on executive routines and productivity patterns, especially timeboxing, deep work protection, evening preparation, and energy-aware scheduling.
- Endrit works at Im Sutenkamp 2 in Hamm.
- Typical work shifts mentioned: weekdays 05:45 to 14:00, Saturday sometimes 06:00 to 14:00 or 06:00 to 12:00 depending on instruction.
- Endrit wants work shifts documented in Google Calendar for hour control: always subtract mandatory 0:30 h break, not 1:00 h; weekdays 05:45-14:00 = 7:45 h net, Saturday 06:00-14:00 = 7:30 h net. Use normal hours/minutes format (not decimal) in the event title/notes and include a running payroll-period net total. Current payroll test period starts 04.05.2026 and runs through the first Sunday of next month logic as Endrit described.
- Current May 2026 work-hour running total from Endrit's 2026-05-29 correction: baseline before Do 28.05. is 55:45 h net, not 54:45; Do 28.05. adds 7:45 h for 63:30 h after yesterday; Fr 29.05. 06:45-15:30 with the standard 0:30 break is 8:15 h net; current total with today is 71:45 h net.
- Work is often done at Fachhochschule Dortmund, Emil-Figge-Straße 42.
- Usual sport locations: A.I. Fitness (mostly Dortmund City, often Dorstfeld), outdoor calisthenics, Kickboxen, and Hochschulsport at TU.
- Typical post-work flow: sport first, then shower, then at most about 2 hours of deep work.
- For planning, include realistic travel times and traffic, especially after 14:00 and around 45 to 50 minutes from Hamm to Dortmund/Uni in Feierabendverkehr.
- Do not add these travel times into the calendar, but factor them into planning.
- Endrit wants a daily 21:00 Europe/Berlin habit check that reminds him to hang from the pull-up bar and asks for a short evening reflection on how the day went and what could improve.
- Habit tracking should stay separate from task lists; do not infer habits from local task stubs.
- Weekly planning test context: when Endrit says "morgen", he may mean a structured university/work day with fixed blocks and should be asked to confirm the exact date if ambiguity matters.
- Planning preferences for the test run: tomorrow starts at 07:00 at Uni/Fachhochschule Dortmund (Emil-Figge-Straße), with Deep Work until 17:00, meal breaks around 10:00 and 14:00, then outdoor calisthenics around 17:00 if it is not raining.
- On Thursday he works until around 14:00/14:10 at Im Sutenkamp 2 in Hamm, then drives from Hamm to Dortmund/Dorstfeld/Uni area and is likely there around 15:00. Thursday default after work: Calisthenics + Kickboxen; afterward briefly check what others are doing, definitely eat, shop, then go home. Do not plan a full Deep Work session Thursday evening unless he explicitly asks; at most a small piece.
- On Friday he wants an early start at the Uni co-learning center, Deep Work until about 14:00, then training in Dorstfeld (A.I. Fitness) and more Deep Work later.
- Weather rule for outdoor training: rain is the blocker; if it does not rain, he prefers outdoor calisthenics.
- On Saturday he works 06:00 to 14:00 and wants to go straight to Uni afterward for outdoor training if it is not raining, then Deep Work for the rest of the day.
- For weather-based planning, check the forecast for the relevant location on the day and focus on rain only, since cold alone does not stop outdoor training.
- Hiking group invite style for Endrit: keep it short and WhatsApp/Telegram-ready, similar to his Feiertag hiking template. Include greeting, day/date if known, concise location/goal, start time, Komoot route link, exact meeting point/parking if available, very strong sunscreen reminder, simple weather note, carpooling note, short packing list, and poll line. Avoid repeating route distance/details already visible in Komoot; keep Hohensyburg/Hengsteysee naming when relevant. For future Komoot hikes, fetch/read the Komoot page, use Komoot discover/tour context when possible to compare route options, check local weather for the exact hiking area/day, and produce a compact adapted invite. If Endrit provides the correct Google Maps link, use that as the meeting point. Current correct meeting point for the Hohensyburg/Hengsteysee Monday hike is https://maps.app.goo.gl/aDMM1G6bm3ausybQ9. For hot/sunny hikes, make sunscreen/sun protection especially prominent. Komoot has no public official API; use public share/discover pages, browser if Endrit is logged in, or GPX exports/imports for deeper analysis. Do not ask Endrit for Komoot login credentials; if needed, have him log in himself in the browser/user session and then use that session. Endrit said not to set this up today because there is enough else to do.

## Promoted From Short-Term Memory (2026-05-24)

<!-- openclaw-memory-promotion:memory:memory/2026-05-19.md:4:4 -->
- Endrit asked to save the current Via Claudia and Notion/Bayern Trip status into the Second Brain so EOS stays up to date. [score=0.856 recalls=0 avg=0.620 source=memory/2026-05-19.md:4-4]
<!-- openclaw-memory-promotion:memory:memory/2026-05-19.md:10:10 -->
- Current fixed state: [score=0.856 recalls=0 avg=0.620 source=memory/2026-05-19.md:10-10]
<!-- openclaw-memory-promotion:memory:memory/2026-05-19.md:6:6 -->
- Saved durable status in: [score=0.805 recalls=0 avg=0.620 source=memory/2026-05-19.md:6-6]
