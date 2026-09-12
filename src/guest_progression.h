#ifndef GUEST_PROGRESSION_H
#define GUEST_PROGRESSION_H

// Balance policy: successful, contested operations; real calendar days.
#define WORSHIPS_FOR_T4 3
#define WORSHIPS_FOR_T5 5
#define POWER_BANISH_SECONDS (30L * 24 * 3600)
#define SANCTUARY_ACTIVE_SECONDS (30L * 24 * 3600)
#define SANCTUARY_HIGH_TIER_PERCENT 20

bool power_operation_goal(int goal);
DOMAIN_TYPE *power_domain(const char *name);
bool power_available(DOMAIN_TYPE *domain);
int power_relation(FACTION_TYPE *fac, const char *name);
bool set_power_relation(FACTION_TYPE *fac, const char *name, int relation);
void show_power_relations(CHAR_DATA *ch, FACTION_TYPE *fac);
const char *power_operation_error(int faction, int territory, int goal, const char *target);
bool resolve_power_operation(int winner, OPERATION_TYPE *op);
bool claim_power_territory(CHAR_DATA *ch, LOCATION_TYPE *territory);
int guest_remake_tier(CHAR_DATA *ch);
bool guest_out_of_play(CHAR_DATA *ch);
void show_guest_progress(CHAR_DATA *ch);
void update_sanctuary_population();
void refresh_sanctuary_character(CHAR_DATA *ch);
bool sanctuary_population_blocked();
void restore_sanctuary_population(bool blocked);

#endif
