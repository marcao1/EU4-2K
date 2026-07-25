# EU4 2K Age Adaptation Plan

## Phase 1: vanilla baseline (completed)

Keep the four vanilla EU4 ages unchanged except for their scripted start years:

| Vanilla age | Start | Current gate | Working modern theme |
|---|---:|---|---|
| Age of Discovery | 2000 | Always | Information Age |
| Age of Reformation | 2100 | Drone Technology enabled | Age of AI |
| Age of Absolutism | 2200 | Global Trade enabled | Space Age |
| Age of Revolutions | 2300 | Enlightenment enabled | Interplanetary Age |

The 100-year cadence matches the mod's 2000 start and places the last two ages on the dates of their unchanged vanilla institution gates. The final age remains active through the open-ended 9999 end date.

## Phase 2: modern names and presentation (completed)

1. The displayed names and descriptions are localized as Information Age, Age of AI, Space Age, and Interplanetary Age.
2. The internal vanilla IDs remain unchanged to minimize compatibility risk.
3. English localization is implemented first; other supported languages can be added after the design stabilizes.
4. Vanilla age artwork is retained for the first gameplay pass. It can be replaced after objectives and abilities are final.

## Phase 3: objectives (completed)

The historical, religious, colonial, and tag-specific objectives have been replaced with goals supported by the mod's actual systems.

- Information Age: developed capital, trade centers, income, Globalized Economy, allies, great-power status, and technology leadership.
- Age of AI: developed capital, town halls, universities, income, accepted cultures, Artificial Intelligence, and stability.
- Space Age: Orbital Industry, universities, force limit, army tradition, strategic infrastructure, allies, and technology leadership.
- Interplanetary Age: Mars Economy, income, national development, force limit, developed capital, allies, and universities.

Implemented design rules:

- Provide seven objectives per age, as vanilla does.
- Make at least four achievable by small or medium countries.
- Avoid objectives that require a particular religion, continent, government form, or country tag.
- Prefer fixed thresholds over checks against every owned province, so expansion does not make an objective harder.
- Verify every referenced institution, building, variable, flag, and scripted trigger exists in EU4 2K.

## Phase 4: abilities (completed)

1. Each age has seven generic abilities and four country-flavored abilities.
2. Obsolete colonial, religious, absolutism, and cavalry bonuses were replaced with modern economic, diplomatic, intelligence, logistics, research, and advanced-warfare bonuses.
3. Generic modifiers remain near vanilla power levels, with final-age bonuses kept deliberately conservative.
4. Every ability has an `ai_will_do` block; generic abilities use factor 10 and eligible country abilities use factor 100.
5. Every ability calls `on_age_ability_taken`, and obsolete scripted flags and conditional effects were removed.

## Phase 5: mechanics and balance (completed)

1. Religious-conflict rules are disabled, the Age of AI now uses the 2100 Drone Technology institution gate, and Papacy scaling is held at the neutral `1.0` in every age.
2. The vanilla Absolutism blocks remain in the final two ages for engine and government-mechanic compatibility. Their age abilities and objectives no longer reference Absolutism.
3. The vanilla splendor ability cost of 800 is retained. The finite ages last about as long as vanilla ages, while objectives are staggered between accessible and stretch goals.
4. The permanent Interplanetary Age has no generic technology-cost or interest reduction. Its core-creation, trade-efficiency, idea-cost, construction-cost, fire-defense, and diplomatic-upkeep abilities are reduced relative to the finite ages.
5. Modern English localization and tooltips cover every replacement objective and ability.

## Phase 6: validation

1. Launch bookmarks or test saves immediately before and after 2000, 2100, 2200, and 2300.
2. Confirm exactly one age is active and each transition fires once.
3. Confirm objectives update, grant splendor, and do not complete trivially at game start.
4. Confirm age abilities can be purchased, affect the displayed modifiers, and disappear at the next transition.
5. Run an observer game across all transitions and review `error.log` for unknown triggers, modifiers, localization keys, or interface assets.
