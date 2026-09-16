# Strategy level reference

Captured from the supplied Fibonacci-level screenshots on 2026-09-16. These values are active in `config/settings.py` for the read-only candle/Fibonacci report; they are not connected to order execution.

| Label | Level |
| --- | ---: |
| Void | 4.23 |
| BO | 2.618 |
| TP | 2.5 |
| TP E4-E7 | 0.618 |
| E3 | 0 |
| E3.5 | -0.809 |
| E4 | -1.618 |
| E4.5 | -2.424 |
| E5 | -3.23 |
| E5.5 | -4.539 |
| E6 | -5.848 |
| E6.5 | -8.424 |
| E7 | -11 |
| E7.5 | -13.934 |
| E8 | -16.868 |
| E8.5 | -22.358 |
| E9 | -27.848 |
| E9.5 | -36.272 |
| E10 | -44.696 |

Direction provided for the current example: **High → Low**.

## Active operational level mapping

The following mapping takes precedence over the separately captured screenshot labels when applying the strategy:

- **BO** uses the **E4** Fibonacci level.
- **Void** uses the **E5** Fibonacci level.
- BO and E4 are therefore the same price level; Void and E5 are the same price level.
- If price breaks **E4 / BO**, flip the Fibonacci direction from High → Low to Low → High before making the next decision.
- A BO/E4 breakout may be confirmed by either a subsequent candle wick crossing the level or its body crossing the level.
- If price reaches Void/E5 immediately after the BO/E4 breakout, do not open an entry at BO/E4 or Void/E5 while price continues directly to Void.
- After Void/E5 is reached first, wait for a pullback to the applicable level before considering an entry.
- A BO/E4 breakout that moves directly to Void/E5 completes the signal; do not chase a new entry after that completed move.
- Take profit should be set **500 MT5 points** above the Void/E5 price level. This is a demo strategy parameter and must be calculated from the broker-reported point size.
- After a BO breakout, take one simulated entry for each qualifying pullback to **E3**, **E4**, **E5**, and each subsequent level through **E10**.
- The E5 pullback entry changes the take-profit of **all existing entries** to the E3 level. Every later E6–E10 entry joins that same E3 target group.
- The E3 entry is included in that group: once the E5 entry has occurred and price reaches E3, close all existing entries together.
- This rule may intentionally surrender profit on some earlier entries; the strategy expects the higher-level entries to compensate. The simulator must log this target replacement explicitly.

## Signal workflow and range observations

1. An authorized Telegram signal supplies the target candle timestamp.
2. Retrieve that M1 candle in the broker/CST timezone.
3. Draw High → Low Fibonacci from the candle wick high to wick low.
4. Monitor the price/range associated with E3 through E5.

The E3–E5 range is measured in the MT5 symbol's native points:

```text
E3_E5_points = abs(E3_price - E5_price) / FixedVol100_symbol_point
```

Provided range rules:

- Below **35,000 points**: considered a trap.
- **35,000–45,000 points**: ideal to proceed.
- Above **45,000 points**: may reach E6 or higher.

If the E3–E5 range is below 35,000 points, ignore the signal and open no simulated entries.
