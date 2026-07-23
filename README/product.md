# EU4 2K — Product Vision

> A modern-day grand-strategy total conversion for Europa Universalis IV, beginning on 1 January 2000.

## Document status

- **Project name:** EU4 2K
- **Start date:** `2000.1.1`
- **Initial campaign horizon:** 2000–2100
- **Base game:** Europa Universalis IV
- **Current target version:** EU4 `1.37.*`
- **Foundation:** Extended Timeline 1.18.2 fork
- **Development stage:** Pre-alpha

This document defines what EU4 2K should become and what must be included in its first playable release. It is a product guide, not a promise that every idea listed here is already implemented.

## Vision

EU4 2K transforms Europa Universalis IV into a global strategy sandbox for the twenty-first century. The campaign begins on 1 January 2000, at the opening of a new millennium: the United States is the dominant world power, Russia is rebuilding its influence, China is rapidly growing, European integration is accelerating, and many regional powers are trying to reshape the emerging international order.

The mod should preserve what EU4 does best—long-term state building, diplomacy, warfare, trade, and alternate history—while translating those systems into a recognizable modern setting. Players should be able to follow a broadly historical path or create a plausible alternate century without the world immediately collapsing into uncontrolled conquest.

## Player fantasy

The player leads a modern state through a century of political, economic, technological, and military change. A successful campaign is not measured only by territorial expansion. The player may instead become a financial center, lead a regional bloc, dominate global trade, build a technological superpower, restore a fallen sphere of influence, or guide a fragile state into stability.

The central question is:

> What kind of world power can this country become by 2100?

## Design pillars

### 1. A recognizable world in 2000

Borders, governments, alliances, rivalries, development, cultures, and major conflicts should reflect conditions on 1 January 2000 closely enough that every region feels believable. Provinces retain the closest appropriate vanilla EU4 religion instead of introducing new modern religious or secular categories.

Historical accuracy is the starting point, not a railroad. After the campaign begins, systems and player choices should create plausible alternate history.

### 2. Power beyond conquest

Modern influence comes from economic strength, diplomacy, technology, institutions, military reach, and alliances. Territorial expansion remains possible, but aggressive conquest should carry serious diplomatic, economic, and internal costs.

### 3. Modern systems expressed clearly

New mechanics should use familiar EU4 concepts wherever possible. A player should understand why an action matters without reading a separate manual. Custom systems must add meaningful decisions rather than complexity for its own sake.

### 4. Distinct national experiences

Major powers, regional powers, and strategically interesting smaller countries should have different goals and pressures. Missions, events, governments, modifiers, and decisions should make countries feel distinct without making only the largest nations enjoyable.

### 5. A stable century-long campaign

The economy, technology curve, military progression, diplomacy, and AI must remain functional from 2000 to 2100. Performance and campaign stability take priority over excessive event density or decorative mechanics.

## The starting world

The year-2000 bookmark should communicate the major forces shaping the new century:

- United States global leadership and overseas commitments.
- European integration and the tension between national and collective interests.
- Russia's political and economic recovery after the 1990s.
- China's economic rise and expanding global influence.
- Regional competition in the Balkans, Middle East, Caucasus, Africa, and Asia.
- Globalization, digitalization, and increasingly connected trade.
- Fragile states, separatist movements, and unresolved post-Cold War conflicts.
- The growing importance of energy security, migration, climate pressure, and advanced technology.

These themes should emerge through gameplay systems and regional content rather than through fixed historical outcomes.

## Featured starting countries

The bookmark should initially highlight a varied group of countries:

| Country | Starting experience |
|---|---|
| United States | Maintain a global order while balancing military commitments and domestic costs. |
| Russia | Rebuild state power, recover influence, and choose a relationship with Europe and Asia. |
| China | Convert economic growth into technological, diplomatic, and military power. |
| Germany | Shape European integration while becoming a leading economic and diplomatic power. |
| France | Balance national independence, European leadership, and global commitments. |
| United Kingdom | Define its place between Europe, the Atlantic alliance, and its global network. |
| Federal Republic of Yugoslavia | Recover from isolation and conflict, determine the future of the federation, and redefine Serbia's regional position. |

More featured starts can be added after these countries and their surrounding regions are stable.

## Core gameplay loop

1. **Stabilize the state:** manage legitimacy, unrest, finances, institutions, and regional pressures.
2. **Choose a national direction:** pursue missions, reforms, alliances, economic priorities, and military doctrine.
3. **Build national power:** develop infrastructure, technology, industry, trade, and armed forces.
4. **Project influence:** use diplomacy, aid, alliances, guarantees, sanctions, subjects, and limited warfare.
5. **Respond to a changing world:** adapt to crises, new technologies, shifting blocs, and the rise or decline of other powers.
6. **Create a legacy:** lead a regional order, become a great power, transform the country, or survive against stronger rivals.

## Core systems

### Countries and map

- Accurate sovereign states and dependent territories for `2000.1.1`.
- Plausible ownership, cores, claims, capitals, development, and province cultures.
- Modern country names, flags, colors, rulers, and government forms.
- Careful representation of disputed territories through ownership, cores, claims, autonomy, unrest, subjects, or events.
- No unnecessary map replacement unless the existing Extended Timeline map cannot represent essential modern borders.

### Religion

EU4 2K keeps the vanilla EU4 religions and their familiar mechanics. The mod will not add secularism, irreligion, atheism, or modern political ideologies as religions.

- Every province and country uses the closest appropriate vanilla religion.
- Existing vanilla religious mechanics remain functional unless a targeted compatibility fix is required.
- Political ideology and form of government are represented through governments, reforms, modifiers, events, decisions, estates, or factions—not religion.
- Religious demographics may be simplified at province level because EU4 permits only one province religion.
- Religious conversion remains possible, but it should not dominate modern gameplay or function as a substitute for political reform.
- Historical religious tensions should be handled neutrally and only where they create meaningful gameplay.

### Diplomacy and world order

EU4 alliances and great-power mechanics form the base of modern diplomacy. The mod should expand them through scripted systems where they provide real strategic choices.

Priority concepts:

- Defensive alliances and security blocs.
- Regional organizations and integration projects.
- Sanctions, diplomatic isolation, and international legitimacy.
- Guarantees, military access, foreign aid, and influence over smaller states.
- Proxy relationships and limited intervention.
- Stronger diplomatic consequences for aggressive expansion.

The first release does not require a perfect simulation of every international organization. NATO, European integration, and other institutions may initially be represented by modifiers, events, decisions, opinion rules, and alliance structures.

### Government and internal politics

Government types should distinguish modern democracies, authoritarian republics, monarchies, transitional states, and other relevant regimes.

Internal politics should focus on strategic pressures the player can influence:

- Government legitimacy and stability.
- Reform and institutional capacity.
- Corruption and administrative efficiency.
- Separatism, autonomy, and regional unrest.
- Democratic transition or authoritarian consolidation.
- Political crises expressed through disasters, events, estates, factions, or government mechanics.

### Political leaders and groups

Real political leaders and influential political groups should shape national content. They provide context, competing priorities, and temporary strategic opportunities without turning the mod into an election-by-election simulator.

Leaders may include heads of state, heads of government, major opposition figures, revolutionary leaders, and other individuals who materially affected national policy. Because EU4 normally exposes only one ruler, additional leaders may be represented as advisors, event characters, country modifiers, mission requirements, or named political-group leaders.

Political groups may represent real parties or broader coalitions such as reformists, conservatives, nationalists, liberals, social democrats, military establishments, business interests, labor movements, regional parties, and civil-society movements. The appropriate level of detail depends on the country:

- Featured countries may use named historical parties, coalitions, and leaders.
- Countries with limited unique content may use broader political blocs.
- A political group's strength may be tracked through estates, factions, variables, country flags, influence modifiers, or event chains.
- Elections, coups, resignations, deaths, scandals, protests, and coalition changes may alter the ruling leader or dominant group.
- A leader or group can unlock missions, change mission requirements, provide alternate event options, or modify the rewards of a completed mission.
- Content must include fallback conditions so a mission tree remains playable after an unexpected ruler change or alternate-history outcome.

Leader content should emphasize policy choices and historical pressures, not assign permanent moral or ethnic traits to populations. Political descriptions should remain neutral and distinguish documented history from partisan claims.

### Economy and infrastructure

The modern economy should reward productive development and connected infrastructure, not only territorial size.

Planned progression includes:

- Industrial and service-oriented economic development.
- Energy infrastructure, including coal, nuclear, renewable, and later fusion technologies.
- Transportation infrastructure from highways and railways to mass transit and future logistics.
- Modern fortifications and defensive networks.
- Trade routes and nodes adjusted for modern global commerce where technically practical.
- Building costs and AI priorities that remain sustainable throughout the campaign.

Economic growth must not create unlimited money, building slots, or development. Replacement chains should be monotonic, understandable, and non-stacking where appropriate.

### Technology

The technology system covers modern and near-future development across three recognizable tracks:

- **Administrative:** digital government, regulation, data governance, automation, and future state capacity.
- **Diplomatic:** global logistics, communications, trade networks, modern fleets, and space commerce.
- **Military:** precision weapons, network-centric warfare, drones, autonomous systems, and future defense technology.

The intended technology milestones are 2005, 2020, 2035, 2050, 2065, 2080, 2090, and 2100. Technology names, unlocks, unit progression, and effects must agree with one another.

### Warfare

EU4's land-and-province warfare remains the technical foundation, but balance should make modern wars feel costly and politically consequential.

- Smaller professional forces should matter more than endless manpower.
- Technology and military quality should be decisive but not unbeatable.
- Defensive terrain, infrastructure, and fortifications should shape campaigns.
- Occupation and prolonged war should impose high economic and stability costs.
- Large-scale annexation should be difficult to justify and hold.
- Nuclear weapons, if implemented, must act as strategic deterrence rather than ordinary battlefield units.

Naval and air power must be represented within EU4's limitations. Aircraft may be abstracted through unit modifiers, technology, buildings, doctrines, events, or support mechanics rather than a separate controllable air-war system.

### Missions, real events, and alternate history

The campaign should include real events that occurred after 1 January 2000. Historical event chains provide the initial direction of the world, while triggers and alternate outcomes ensure they react to the current campaign rather than firing without context.

Examples include:

- Political change in Yugoslavia during 2000 and the later future of Serbia and Montenegro.
- The September 11 attacks and the international response.
- The Afghanistan and Iraq wars.
- European Union and NATO enlargement.
- The introduction of euro notes and coins.
- The 2008 global financial crisis.
- The Arab Spring and its regional consequences.
- Major post-Soviet conflicts and changes in relations between Russia and the West.
- Brexit.
- The COVID-19 pandemic.

Historical events should follow five rules:

1. **Use real dates as guidance:** major events receive historically appropriate mean times or date windows.
2. **Require a valid situation:** an event fires only when its essential countries, governments, relationships, and territorial conditions still exist.
3. **Allow player agency:** important events offer meaningful responses with proportionate costs and consequences.
4. **Support divergence:** if history has changed, the event may use an alternate version, be delayed, or never occur.
5. **Remain neutral:** descriptions distinguish established facts from disputed claims and avoid celebratory treatment of atrocities or civilian suffering.

Events through the recent historical period should be based on real developments. Content beyond that point should be clearly treated as plausible future scenarios rather than presented as history.

Content should present goals and consequences without forcing history to repeat exactly.

Every playable country must receive a new mission tree built for the modern start date. Medieval, early-modern, and inherited Extended Timeline missions should not appear merely because a country lacks new content.

All country mission trees should include:

- A country-specific opening situation and immediate challenges.
- At least one national objective based on the country's real position in 2000.
- Domestic politics and state development.
- Economic growth, infrastructure, and technology.
- Regional diplomacy, security, and international alignment.
- At least two meaningful strategic directions where the historical situation supports them.
- Conditional branches or fallback missions that remain usable after alternate-history changes.
- Rewards that create strategic opportunities rather than only permanent numerical power.

Smaller trees may share modern regional or structural branches, but every country must have country-specific missions, localization, and starting context. No country should receive only the unmodified vanilla generic tree.

#### Priority mission regions

Mission development follows this order:

1. **Europe:** full national trees for every European country, with shared systems for European integration, NATO, regional cooperation, neutrality, and relations with Russia.
2. **United States:** a deep tree covering domestic direction, global leadership, alliances, economic power, intervention, and alternative foreign-policy strategies.
3. **China:** a deep tree covering economic modernization, internal stability, regional claims, global trade, technological growth, and alternative international strategies.
4. **Russia:** a deep tree covering state consolidation, the post-Soviet sphere, economic recovery, military reform, relations with Europe and Asia, and alternative international strategies.
5. **Rest of the world:** new national trees for every remaining playable country, developed region by region after the priority content is stable.

The deepest featured-country trees should also include:

- Relevant real leaders and political groups with conditional content.
- Regional, economic, diplomatic, and military mission branches.
- Events for major internal or international turning points.
- Multiple coherent historical and alternate-history conclusions.

## Serbia and Yugoslavia focus

The Federal Republic of Yugoslavia is the initial regional showcase. Its campaign should begin in a difficult position and offer several credible directions rather than a single predetermined outcome.

Potential themes include:

- Political transition and international normalization.
- The relationship between Slobodan Milošević's government, the democratic opposition, and the political transition of 2000.
- Leader- and coalition-specific missions for reform, continuity, nationalist policy, and democratic consolidation.
- The constitutional future of Serbia and Montenegro.
- Kosovo's unresolved status and regional security.
- Economic recovery, reconstruction, and institutional reform.
- Relations with neighboring Balkan states.
- Cooperation or confrontation with European and Atlantic institutions.
- A regional leadership path based on diplomacy and trade.
- Carefully bounded alternate-history paths for renewed federation or territorial revisionism, with proportionate risks and resistance.

Sensitive modern conflicts should be described neutrally and represented consistently. Gameplay should not endorse ethnic hatred, collective punishment, or atrocities.

## MVP: first playable release

Version `0.1` is successful when a new campaign can start on `2000.1.1`, run for at least twenty in-game years, and offer meaningful choices without critical errors.

### Required

- One visible and selectable `2000.1.1` bookmark.
- Correct ownership, capitals, cores, and country existence for the starting date.
- Valid rulers, governments, technology, institutions, diplomacy, and armies for playable countries.
- Functional modern technology progression through at least 2035.
- A coherent baseline economy and infrastructure chain.
- A new modern baseline mission framework used by every playable country.
- Focused content for the Federal Republic of Yugoslavia/Serbia.
- A working Yugoslav political transition chain with real leaders, political groups, and divergent outcomes.
- First-pass complete national mission trees for the United States, China, and Russia.
- First-pass country-specific missions for every European country.
- At least one country-specific opening branch for every other playable country.
- A first set of conditional real-world event chains covering 2000–2010.
- Vanilla religions only, with all removed secular or irreligious assignments replaced by appropriate vanilla religions.
- English localization for all player-visible content.
- No recurring startup errors, missing localization, broken country history, or immediate AI bankruptcy spiral.
- A documented installation and compatibility process.

### Desirable, but not required for `0.1`

- Deep NATO and European Union mechanics.
- Detailed sanctions and foreign-influence systems.
- Final-depth mission trees for countries outside Europe and the initial major-power focus.
- Fully redesigned trade nodes.
- Dedicated proxy-war mechanics.
- Nuclear deterrence mechanics.
- Technology and content beyond 2100.
- Translations beyond English.

## Non-goals

The initial release will not attempt to:

- Simulate every law, minor party, local election, corporation, or short-lived political figure.
- Add new religions to represent ideology, secular government, or non-religious populations.
- Reproduce Hearts of Iron IV combat inside EU4.
- Guarantee historical outcomes after the start date.
- Give every country an equally large mission tree; all countries receive new modern missions, but depth is prioritized by region and strategic importance.
- Support campaigns beginning before 2000 as part of the primary product experience.
- Maintain compatibility with unrelated overhaul mods.
- Add mechanics that the AI cannot use or that severely damage performance.

## Development principles

- **Playable before expansive:** finish a stable vertical slice before adding more countries or mechanics.
- **Data before flavor:** establish correct borders, tags, history, and diplomacy before writing large event chains.
- **Mechanics before modifiers:** prefer meaningful choices over collections of passive bonuses.
- **Reuse carefully:** preserve stable Extended Timeline systems where they fit the modern-day vision; replace only what needs to change.
- **One source of truth:** record important dates, tag mappings, technology levels, and design decisions in project documentation.
- **Safe iteration:** test changes in a new campaign and keep features small enough to validate independently.
- **Respect dependencies:** confirm the licensing and attribution requirements of Extended Timeline and any other source material before a public release.

## Roadmap

### Phase 1 — Foundation

- Lock the start date and campaign horizon.
- Audit country tags and the year-2000 political map.
- Remove or disable irrelevant historical bookmarks and legacy systems.
- Establish error-log and startup validation checks.
- Confirm the mod name, descriptor, supported EU4 version, attribution, and repository structure.

### Phase 2 — Playable world

- Complete country and province history for `2000.1.1`.
- Set diplomacy, governments, rulers, technology, institutions, armies, and navies.
- Balance the starting economy and development.
- Ensure the AI can survive the opening decade.

### Phase 3 — Modern gameplay

- Finalize technology through 2035.
- Balance modern buildings, units, warfare, and aggressive expansion.
- Implement the first versions of blocs, integration, sanctions, and influence.
- Create the universal modern mission framework and remove inappropriate inherited mission assignments.

### Phase 4 — Priority mission content

- Complete Yugoslavia/Serbia content and its Balkan context.
- Add leader- and political-group conditions to the Yugoslav mission tree and transition events.
- Complete first-pass national mission trees for the United States, China, and Russia.
- Complete country-specific mission trees for Europe, beginning with the Balkans and major European powers before expanding to the rest of the continent.
- Add at least one new country-specific opening branch to every remaining playable country.
- Implement and validate the first conditional historical event chains for 2000–2010.
- Test alternate paths for plausibility and balance.
- Run repeated observer campaigns through 2020 and 2035.

### Phase 5 — Alpha release

- Fix critical errors and missing localization.
- Validate installation on a clean EU4 setup.
- Document known issues and compatibility.
- Package version `0.1` for private testing.

### Later development

- Expand every non-priority country's opening branch into a complete national tree, region by region.
- Deepen European, American, Chinese, and Russian missions using playtest results.
- Deepen economic and diplomatic systems based on playtest feedback.
- Complete technology and balance through 2100.
- Improve presentation, graphics, music, and localization.
- Prepare a public release only after permissions, attribution, and dependency requirements are settled.

## Quality targets

Before a milestone is considered complete:

- The game reaches the country-selection screen without critical errors.
- Every playable country can start a campaign and receives new modern missions.
- No playable country is assigned only vanilla or obsolete Extended Timeline missions.
- The United States, China, Russia, and every European country have country-specific objectives and localization.
- No player-visible key is missing English localization.
- No required country owns undefined or invalid provinces.
- Technology and building unlocks match their documented dates.
- The AI does not enter a universal debt or manpower collapse during normal observer tests.
- A twenty-year observer run completes without a repeatable crash.
- Major wars occur for understandable strategic reasons and do not consistently consume the entire world.
- New mechanics have an explanation available in tooltips or event text.

## Open design decisions

The following questions should be resolved through prototypes and playtests:

1. Should the primary end date be 2050, 2100, or remain open-ended?
2. How much of the pre-2000 Extended Timeline content should remain accessible?
3. Which international organizations need dedicated mechanics, and which can remain diplomatic abstractions?
4. Should air power be represented primarily by modifiers, special units, buildings, or a combination?
5. Can nuclear deterrence be made strategically useful without allowing the AI to destroy campaign balance?
6. How should democratic elections affect rulers and policy without creating excessive event spam?
7. Which disputed territories require special mechanics at the starting date?
8. How restrictive should conquest be compared with diplomatic and economic expansion?

## Definition of the product

EU4 2K is successful if players recognize the world of 2000, understand the pressures facing their chosen country, and can guide it through a believable alternate twenty-first century using diplomacy, development, technology, and warfare. The mod should feel like a modern grand-strategy game built from EU4's strengths—not simply a historical map with modern names.
