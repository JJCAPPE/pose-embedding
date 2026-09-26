# Equal-budget motion selection campaign

Result-blind design recorded September 26, 2026, while the prioritized SCC
Contrastive/Contextual development pilots are running. No novel outcomes have
been opened. This specification fills the selection-grid requirement in
protocol-v2; it does not claim the full campaign has been run or is affordable.

Each of the 26 methods has three candidates: **original, half and double** all
of its declared learning rates together. Method-specific ratios are preserved
(e.g. fast proxies, learned class boundaries and auxiliary graph parameters).
All other recipe, optimizer, warmup, architecture, scorer and data settings stay
fixed at the documented motion adaptation. This is a deliberately narrow tuning
space around each method's published recipe; it does not establish globally
optimal hyperparameters for every algorithm.

Each candidate has six paired seeds, the same physical P×K batches and the same
full update/validation budget. Thus selection requires **468 completed
candidate/seed runs**, followed by **156 selected final runs**. Mean development
Recall@1 across six seeds selects candidate and step per method. Exact candidate
ties prefer original, then half, then double; within a candidate, exact ties
prefer the earliest eligible step after full warmup/delayed components. Selection
never uses novel data. The 512- and 1536-dimensional comparison groups stay separate.

The earlier two-method runs are engineering pilots, disclosed with their original
attempts, failures, outcomes and costs. They are ineligible to choose a final
checkpoint or expand a method's candidate grid. Their role is to verify feasibility
and the paired training/evaluation path. Numerical pilot outcomes must not be used
to change this grid silently. Any further development-driven amendment must be
explicitly versioned, retain the old trial ledger and occur before novel opening.

A campaign declaration must precede every candidate attempt. It binds a fresh
trial directory, complete GPU profiles, all prior engineering trial roots, source
code, configurations and the exact candidate grid. Selection audits every attempt
in that directory, including unsuccessful ones. A retry requires an immutable
operational-failure review; numerical instability cannot be relabeled operational.
No successful candidate run can be omitted, and duplicate successful cells fail
selection. A numerical failure keeps the complete-campaign gate closed pending an
explicitly recorded result-blind treatment, rather than silently benefiting from
extra tuning attempts.

The provisional full budget is 50,000 total updates, including warmup. Actual
profiles must measure every method's complete backward/optimizer path, including
S2SD feature distillation, ProxyNCA++/HIST/AVSL post-warmup encoder gradients,
DiVA memory/EMA and custom descriptor scorers. Update-only forecasts exclude full
validation, input setup and checkpoint work; they cannot establish affordability.
Long jobs require validated continuation across immutable checkpoint segments.
Storage forecasts must include these segments and the selected checkpoints. A full
campaign must not be launched from the earlier three-step pair profiles alone.
