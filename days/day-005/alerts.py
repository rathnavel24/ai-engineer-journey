"""Day 5: 20 synthetic alert strings for token-counting / cost projection.

Same three alert shapes as the rest of this project's monitoring theme
(temperature spike, energy spike, device offline), varying tenant, machine
ID, and severity so the strings aren't all the same length.
"""

ALERTS: list[str] = [
    "Machine M-14 temperature 92C exceeds threshold 85C, tenant=acme, severity=high",
    "Machine M-02 energy draw 4.8kW exceeds threshold 4.0kW, tenant=acme, severity=medium",
    "Machine M-27 offline for 12 minutes, last heartbeat 09:41:02Z, tenant=acme, severity=critical",
    "Machine M-08 temperature 78C exceeds threshold 75C, tenant=globex, severity=low",
    "Machine M-31 energy draw 6.1kW exceeds threshold 5.5kW, tenant=globex, severity=medium",
    "Machine M-05 offline for 3 minutes, last heartbeat 14:02:47Z, tenant=globex, severity=low",
    "Machine M-19 temperature 101C exceeds threshold 90C, tenant=initech, severity=critical",
    "Machine M-44 energy draw 3.2kW exceeds threshold 3.0kW, tenant=initech, severity=low",
    "Machine M-12 offline for 27 minutes, last heartbeat 08:15:19Z, tenant=initech, severity=critical",
    "Machine M-03 temperature 88C exceeds threshold 85C, tenant=umbrella, severity=medium",
    "Machine M-22 energy draw 7.4kW exceeds threshold 6.0kW, tenant=umbrella, severity=high",
    "Machine M-36 offline for 5 minutes, last heartbeat 22:58:11Z, tenant=umbrella, severity=low",
    "Machine M-41 temperature 95C exceeds threshold 85C, tenant=acme, severity=high",
    "Machine M-17 energy draw 5.0kW exceeds threshold 4.5kW, tenant=stark, severity=medium",
    "Machine M-09 offline for 45 minutes, last heartbeat 06:33:28Z, tenant=stark, severity=critical",
    "Machine M-25 temperature 82C exceeds threshold 80C, tenant=stark, severity=low",
    "Machine M-30 energy draw 8.9kW exceeds threshold 7.0kW, tenant=wayne, severity=high",
    "Machine M-06 offline for 2 minutes, last heartbeat 11:47:55Z, tenant=wayne, severity=low",
    "Machine M-15 temperature 99C exceeds threshold 85C, tenant=wayne, severity=critical",
    "Machine M-39 energy draw 4.4kW exceeds threshold 4.0kW, tenant=globex, severity=medium",
]

if __name__ == "__main__":
    for i, alert in enumerate(ALERTS):
        print(f"{i}: {alert}")
