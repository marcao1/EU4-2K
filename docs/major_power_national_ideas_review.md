# EU4 2K Major-Power and Serbia National Ideas Review

## Scope

Reviewed idea assignment and modifiers for Serbia, the United States, China, Russia/Soviet Union, Germany, modern France, Great Britain, Japan and India. This is an audit only; gameplay files were not changed.

## Assignment status

| Country | Tag | Active unique set | Result |
|---|---|---|---|
| Serbia | SER | `SER_ideas` | Assigned correctly |
| United States | USA | `USA_ideas` | Assigned correctly |
| China | CHN | `CHN_ideas` while communist | Conditional but correct for 2000 |
| Russia | RUS | `RUS_ideas` | Assigned correctly |
| Soviet Union | SOV | `SOV_ideas` | Assigned correctly |
| Germany | GER | `GER_ideas`; Nazi override while fascist | Assigned correctly |
| Modern France | FR2 | `FRA_ideas_2` | Assigned, but receives revolutionary/Napoleonic ideas |
| Great Britain | GBR | `GBR_ideas` | Assigned correctly |
| Japan | JAP | `JAP_ideas` | Assigned correctly |
| India | INI | `IND_ideas` | Assigned correctly despite the internal name mismatch |

No selected country falls back to generic ideas at the 2000 bookmark.

## Country findings

### Serbia

Current themes include the medieval code of laws, Orthodox bastion, hussars, Alemannic Guard, gold mines, mercenary armies and hajduks.

Problems:

- Almost the entire set predates the 1836 start.
- Two cavalry ideas are poorly suited to the modern armour abstraction.
- Mercenary maintenance is not a defining modern Serbian capability.
- The set does not represent state reconstruction, difficult terrain, military industry, non-alignment, regional diplomacy or the diaspora.

Priority: complete replacement.

### United States

Current strengths are religious tolerance, low unrest, morale, goods produced, prestige and territorial autonomy.

Problems:

- Manifest Destiny grants a colonist, which becomes obsolete and encourages ahistorical colonial expansion.
- Valley Forge and “city upon a hill” remain eighteenth-century framing.
- `tolerance_heretic = 5` is excessive and largely wasted above practical tolerance limits.
- The set lacks federal administration, technological research, financial power, global logistics and naval reach.

Priority: substantial modernization.

### China

The communist set emphasizes population, collectivization, internal control, technology and production.

Problems:

- “One Child Policy” becomes historically obsolete and is inappropriate for an open-ended campaign.
- The set has very strong combined manpower scaling: +20% manpower, +25% force limit and +33% recovery.
- It lacks export industry, infrastructure, centralized administration and later technological development.

Priority: moderate rewrite and manpower reduction.

### Russia

The Russian set combines cheaper cores, +33% manpower, Siberian frontier colonization, artillery, force limit and morale.

Problems:

- Siberian Frontier is functionally obsolete after Russian territorial consolidation.
- Mestnichestvo, Table of Ranks and lifelong conscription are early-modern institutions.
- Core-creation and expansion bonuses encourage continuous territorial conquest.
- +33% manpower and +33% force limit are high before other military modifiers.

Priority: substantial modernization.

### Soviet Union

The Soviet set contains +50% manpower, +50% force limit, two separate -20% infantry-cost bonuses, army tradition and production bonuses.

Problems:

- The combined military modifiers are far above the other reviewed countries.
- Infantry cost reaches -40% from the completed set before external modifiers.
- The set has little economic downside or administrative cost for its military scale.

Priority: immediate balance reduction while retaining a distinct mass-mobilization identity.

### Germany

The generic German set has technology cost, discipline, trade, army tradition, administrative efficiency and +20% goods produced.

Problems:

- Reichsheer, Junkers and the German Confederation are dated for post-1945 Germany.
- The modifier mix remains broadly useful and reasonably balanced.
- The Nazi override is correctly conditional but contains very large conquest incentives and sensitive historical framing.

Priority: rename and reframe the generic set; only modest numerical changes.

### Modern France

FR2 currently uses Revolutionary Tribunal, Napoleonic tactics, Jourdan Law and European Ambitions.

Problems:

- This is a revolutionary/Napoleonic set rather than a modern French set.
- -20% core-creation cost, +10% military tactics and +15% morale create a very strong conquest package.
- It does not represent republican institutions, nuclear deterrence, diplomacy, aerospace, infrastructure or cultural influence.

Priority: complete replacement for FR2. Historical FRA ideas can remain for earlier France.

### Great Britain

The set remains naval and industrial, which fits Britain, but includes colonial growth, tariffs, annexation and marine expansion.

Problems:

- The colonist-era and tariff bonuses lose relevance after decolonization.
- +20% naval morale, +15% heavy-ship power and strong naval completion bonuses stack heavily.
- It lacks financial services, intelligence, global diplomacy and modern professional forces.

Priority: substantial modernization while preserving naval specialization.

### Japan

The set combines discipline, infantry power, samurai, modernization, maritime durability, prestige and colonial growth.

Problems:

- Samurai recruitment and colonial growth are obsolete after 1945.
- The completed military package is strong: +5% discipline and +15% infantry power.
- It lacks advanced manufacturing, research, maritime trade and demographic/economic resilience.

Priority: substantial modernization.

### India

The set emphasizes plurality, diplomacy, stability, trade, prestige and manpower recovery.

Problems:

- “Caste System” as a positive national idea is reductive and dated.
- +33% manpower recovery is high.
- The set lacks federal administration, services, industrial growth, technology and strategic autonomy.

Priority: moderate modernization.

## Cross-country balance findings

- Soviet military bonuses are the largest outlier.
- Russia, China and India have unusually high manpower scaling.
- Modern France has excessive conquest and tactics bonuses.
- Germany's +20% goods produced and Britain's naval stack are strong but manageable.
- Serbia is not overpowered, but its mechanics and names are almost entirely obsolete.
- Colonial bonuses should be removed from modern USA, Britain and Japan sets.

## Recommended design rules

1. Keep two traditions, seven ideas and one ambition per country.
2. Limit discipline to 5%, morale to 10%, combat ability to 10% and goods produced to 10–15% per set.
3. Avoid combining more than two large manpower or force-limit modifiers.
4. Avoid colonists, native policy, tariffs and frontier mechanics in sets intended for 1836 onward.
5. Avoid permanent bonuses tied to short-lived policies such as the One Child Policy.
6. Use long-duration national institutions and capabilities rather than individual regimes or leaders.
7. Preserve distinctive gameplay roles:
   - Serbia: defensive regional power and military industry.
   - USA: innovation, finance, naval reach and logistics.
   - China: state capacity, infrastructure and mass economy.
   - Russia: strategic depth, resources and artillery.
   - Soviet Union: mobilization and planned industry with reduced extremes.
   - Germany: industry, engineering and professional forces.
   - France: diplomacy, state capacity, deterrence and culture.
   - Britain: naval reach, finance and intelligence.
   - Japan: advanced industry, maritime trade and technology.
   - India: pluralism, services, federal scale and strategic autonomy.

## Recommended implementation order

1. Serbia and modern France: their current sets are fundamentally from the wrong era.
2. Soviet Union and Russia: correct the largest balance and expansion issues.
3. USA, Britain and Japan: remove colonial mechanics.
4. China and India: reduce manpower stacking and modernize economic themes.
5. Germany: retain most values but modernize names and descriptions.

Implement these as replacements for the existing tag-specific sets rather than adding more overlapping trigger groups. This avoids ambiguous idea selection and ensures campaigns beginning in 1836 continue using coherent ideas without requiring a mid-campaign swap.

## Implemented in 1.5.0

- Replaced Serbia's medieval cavalry, mercenary and religious set with modern state-building, Balkan diplomacy, defence industry, terrain, infrastructure, diaspora and strategic-autonomy ideas.
- Added a dedicated `FR2_ideas` group for modern France built around republican institutions, central administration, prestige, engineering, deterrence, Francophonie and professional forces.
- Preserved the original `FRA_ideas_2` group exclusively for historical revolutionary France.
- Reduced both sets to the agreed modern balance envelope.

## Implemented in 1.5.1

- Replaced Russia's frontier-colonization, core-creation and early-modern administrative ideas with strategic depth, resources, defence industry, general staff, federal administration, energy exports and deterrence.
- Reduced Soviet manpower from 50% to 25%, force limit from 50% to 25%, and completed-set infantry cost from 40% to 10%.
- Rebuilt the Soviet set around planned industry, mobilization, the Red Army, defence in depth, scientific institutions, union republics and defence production.

## Implemented in 1.5.2

- Removed colonists, tariffs, native-colonial mechanics and excessive religious tolerance from the United States.
- Rebuilt the USA around federal capacity, immigration, research, finance, logistics, naval reach and entrepreneurship.
- Removed colonial growth, tariffs and annexation from Great Britain while reducing its stacked naval combat bonuses.
- Rebuilt Britain around parliament, finance, research, professional forces, intelligence, diplomacy and maritime trade.
- Removed samurai recruitment and colonial growth from Japan and replaced them with constitutional stability, manufacturing, commercial networks, maritime security, education, infrastructure and self-defence forces.

## Implemented in 1.5.3

- Reduced China's manpower recovery from 33% to 15%, removed the additional 25% force-limit tradition, and reduced its technology bonus from 10% to 5%.
- Replaced temporary communist-policy references with long-duration administration, infrastructure, export industry, research, population, domestic-market and strategic-force themes.
- Replaced India's caste framing and 33% manpower recovery with federalism, pluralism, services, industry, technology, Indian Ocean strategy and diplomatic autonomy.
- Removed Germany's government-type filler modifiers, 15% infantry power, Junker and Reichsheer framing, administrative efficiency and 20% goods bonus.
- Rebuilt Germany around federal institutions, engineering, the Mittelstand, vocational education, professional defence, European diplomacy and infrastructure.
