# OCI cost governance

OCI budgets let teams set monthly spending limits per compartment and
send alert emails when forecast or actual spend crosses thresholds.
Cost analysis breaks usage down by service, compartment and tag.

Tagging every resource with a cost-center tag is the foundation of
showback. Compartments isolate blast radius for both access and spend.

Budget alerts are notifications only; hard stops require automation
such as Functions triggered by alert topics to disable resources.
