I don't have web access in this session to pull the live docs page, so I'll give you the architecture-level answer from what I know of how Infisical Gateway works, and flag the one spot worth double-checking against Infisical's current docs before your security team locks in the change.

**The core point for your security team: no inbound rule is needed on the Gateway.** The Gateway always initiates the connection outward to Infisical, so this is not a bastion/VPN-style setup where Infisical reaches into your VPC.

**Rule 1 — Gateway → Infisical (control/relay connection)**
- Direction: Outbound (egress) only, from the Gateway host/subnet
- Port: TCP 443
- Destination: Infisical Cloud (app.infisical.com and its gateway relay infrastructure), or your self-hosted Infisical URL if self-hosted
- If you do domain-based egress filtering rather than just port-based, allow-list the Infisical domain rather than opening 443 to all destinations

**Rule 2 — Gateway → RDS (data path, inside the VPC)**
- Direction: Outbound from the Gateway's security group to RDS; inbound on the RDS security group, sourced from the Gateway's security group (or its ENI/IP if not using SG references)
- Port: whatever the RDS engine listens on: 5432 (Postgres), 3306 (MySQL/MariaDB), 1433 (SQL Server), 1521 (Oracle)

**No rule needed:** anything inbound to the Gateway from Infisical's IPs or the public internet.

Given this is going straight into a firewall change ticket, I'd recommend one quick cross-check: open Infisical's Gateway docs (Platform → Gateway → Deployment/Overview) and confirm the outbound port/domain for your specific setup (Cloud vs. self-hosted, and which region if Cloud), since that's the one detail that could shift and isn't something I can verify live right now.
