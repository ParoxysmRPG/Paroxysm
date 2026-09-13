#ifndef HAVEN_RECOVERY_H
#define HAVEN_RECOVERY_H

// T1 resource units ($10 each), multiplied by current tier (capped at T5).
// Hyper Regeneration never uses the billing path.
constexpr int SANCTUARY_DEATH_COST = 5000;
// Personal bank charges are cents, independent of society resource fees.
constexpr long PERSONAL_SANCTUARY_DEATH_COST = 10000;
constexpr long PERSONAL_SANCTUARY_DEBT_LIMIT = 500000;
constexpr int RECOVERY_PERSONAL_PAYER = -1;
constexpr int SANCTUARY_MAIM_COST = 1250;
enum RecoverySource { RECOVERY_NONE, RECOVERY_SANCTUARY, RECOVERY_RITUAL };
struct RecoveryIncident {
  int source = RECOVERY_NONE;
  int payer = 0;
  bool forest = false;
  int cost_percent = 100; // Captured with coverage; black aura pays 20%.
  long due = 0;
  unsigned long serial = 0;
  std::string description;
  std::string receipt;
};
struct RecoveryState {
  bool wounds_treated = false;
  unsigned long serial = 0;
  RecoveryIncident death, critical;
  std::vector<RecoveryIncident> maims;
  bool operation_dead = false;
  bool operation_ghost = false;
};

#endif
