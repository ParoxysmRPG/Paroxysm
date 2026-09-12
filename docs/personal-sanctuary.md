# Personal sanctuary

Humans without a core faction, society, or legacy society retain ordinary
sanctuary, subject to its existing location, event, and other restrictions.
Guests, storyrunners, and supernatural characters do not use personal billing.

Each sanctuary death recovery costs $100 from the character's personal bank
account. There is no recurring personal upkeep or personal maim fee. A valid
vassal patron pays the existing society recovery fee instead. The payer is
captured with the incident and survives logout; later affiliation changes do
not redirect an existing bill. Ritual and forest recovery rules are unchanged.

A negative personal bank balance makes an unaffiliated human an indentured
servant. Sixteen-hour work days cap effective LF at 30 and provide twice the
full-time base wage regardless of the character's regular employment. Low LF
does not reduce this wage. Existing inactivity penalties, withheld pay, debt
interest, and lifestyle expenses still apply. The effects end automatically
when the bank balance reaches zero. `balance` reports the current rules and
status, and the LF breakdown explains the cap.

At $5,000 or more personal debt, both full and limited sanctuary are blocked
unless a valid vassal patron covers the character. Repaying below that threshold
restores ordinary eligibility. A previously covered recovery can put the
character over the limit; it still completes, but subsequent incidents are
uncovered. Indentured work continues while sanctuary is suspended.

Personal prices and the debt limit are constants in `src/recovery.h`, in cents.
Society recovery prices remain separate resource-unit constants.
