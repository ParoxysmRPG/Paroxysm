# Second Class Citizen

The social stat uses saved skill 235. Its allowed values are 0, -1 and -2.
Creation accepts both negative levels, each worth one negative stat point.
Second Class Citizen cannot be negtrained. `train Second Class Citizen` buys
back one level at the normal single-point base RPXP price.
Temporary skill bonuses and augmentation cannot alter this social status.

| Aura | Ordinary sanctuary benefits | Rape command / forever imprint protection | Death / maim recovery fee |
| --- | --- | --- | --- |
| Full | Yes | Yes | 100% |
| Orange (-1 or existing limited sanctuary) | Yes | No | 100% |
| Black (-2) | No | No | 20% |

Negative levels only modify sanctuary the character otherwise qualifies for;
they never grant coverage or an aura by themselves. Losing the underlying
sanctuary also removes the reduced coverage and aura. Existing sanctuary
eligibility restrictions still apply. Ritual sanctuary cannot upgrade
the protection of a reduced aura. Its existing free recovery remains free.
Black aura appears in both character-description paths and as `B` on the score
sanctuary indicator; balance displays the discount and the $20 personal fee.

Death and maim protection uses the existing next-06:00 recovery system, including
critical bleed-out provenance and forest-monster exclusions. It does not stop
the original injury. The black discount applies after tier and containment
scaling, rounding society resource fees up to a whole resource unit. Personal
maim recovery remains free.

RecoveryIncidentV3 persists the incident's fee percentage alongside its payer,
coverage and billing receipt. Changing status after an injury cannot change its
fee. V1/V2 saves still load at their original full rate, and billing receipts
continue to prevent duplicate charges.

Validation: `make -C src`, `tools/test_recovery.py`,
`tools/test_balance_rules.py`, `tools/test_assault_command.py`,
`tools/test_prisoner_sanctuary.py` and `tools/test_affect.py` in Linux/WSL.
