"""Non-secret, deterministic application settings."""

# Strategy ratios supplied by the strategy owner. BO/E4 and Void/E5 are
# operational aliases; E3–E10 are the calculation levels.
FIB_LEVELS: dict[str, float] = {
    "TP": 2.5,
    "TP_E4_E7": 0.618,
    "E3": 0.0,
    "E3.5": -0.809,
    "E4": -1.618,
    "E4.5": -2.424,
    "E5": -3.23,
    "E5.5": -4.539,
    "E6": -5.848,
    "E6.5": -8.424,
    "E7": -11.0,
    "E7.5": -13.934,
    "E8": -16.868,
    "E8.5": -22.358,
    "E9": -27.848,
    "E9.5": -36.272,
    "E10": -44.696,
}
BO_LEVEL_NAME = "E4"
VOID_LEVEL_NAME = "E5"

# Supported values: "low_to_high" and "high_to_low".
FIB_DIRECTION = "high_to_low"

# Canonical timezone representation for broker timestamps.
BROKER_TIMEZONE = "Asia/Kuala_Lumpur"

# Only these confirmed signal messages are processed by the Telegram test reader.
TARGET_INDICATOR = "PROJECT V || Indicator NQ426"
TARGET_SYMBOL = "FixedVol100"

# Demo strategy parameter: use the broker-reported symbol point value at runtime.
VOID_TAKE_PROFIT_BUFFER_POINTS = 500

# Reserved for a future simulation-only executor. No executor exists yet.
SIMULATION_MODE = True
