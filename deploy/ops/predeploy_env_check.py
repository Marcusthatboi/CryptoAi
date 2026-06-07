from pathlib import Path
import sys


def parse_env(path: Path):
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def is_placeholder(v: str) -> bool:
    low = (v or "").strip().lower()
    if not low:
        return True
    tokens = [
        "your_",
        "replace",
        "changeme",
        "placeholder",
        "example",
        "todo",
        "set_in",
        "yourdomain",
    ]
    return any(t in low for t in tokens) or low.endswith("_here")


def status(env: dict, key: str):
    if key not in env:
        return f"{key}: MISSING"
    v = env[key]
    if is_placeholder(v):
        return f"{key}: PLACEHOLDER"
    return f"{key}: SET"


def main():
    env = parse_env(Path(".env"))
    front = parse_env(Path("frontend/.env.local"))
    blockers = []

    print("=== PREDEPLOY ENV CHECK (REDACTED) ===")
    for key in [
        "APP_ENV",
        "ENVIRONMENT",
        "SECRET_KEY",
        "MONGODB_URL",
        "DB_NAME",
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "ALPACA_API_BASE_URL",
        "FRONTEND_ALLOWED_ORIGINS",
    ]:
        line = status(env, key)
        print(line)
        if line.endswith("MISSING") or line.endswith("PLACEHOLDER"):
            blockers.append(line)

    if "APP_ENV" in env and env["APP_ENV"].strip().lower() == "production":
        print("APP_ENV_MODE: OK(production)")
    else:
        print("APP_ENV_MODE: NOT_PRODUCTION")
        blockers.append("APP_ENV_MODE: NOT_PRODUCTION")

    if "ENVIRONMENT" in env and env["ENVIRONMENT"].strip().lower() == "production":
        print("ENVIRONMENT_MODE: OK(production)")
    else:
        print("ENVIRONMENT_MODE: NOT_PRODUCTION")
        blockers.append("ENVIRONMENT_MODE: NOT_PRODUCTION")

    for key, live_prefix, test_prefix in [
        ("STRIPE_SECRET_KEY", "sk_live_", "sk_test_"),
        ("STRIPE_PUBLISHABLE_KEY", "pk_live_", "pk_test_"),
        ("VITE_STRIPE_PUBLISHABLE_KEY", "pk_live_", "pk_test_"),
    ]:
        src = env if key in env else front
        if key not in src:
            print(f"{key}: MISSING")
            blockers.append(f"{key}: MISSING")
            continue
        val = src[key]
        if val.startswith(live_prefix):
            print(f"{key}: LIVE_OK")
        elif val.startswith(test_prefix):
            print(f"{key}: TEST_KEY")
            blockers.append(f"{key}: TEST_KEY")
        elif is_placeholder(val):
            print(f"{key}: PLACEHOLDER")
            blockers.append(f"{key}: PLACEHOLDER")
        else:
            print(f"{key}: UNKNOWN_FORMAT")
            blockers.append(f"{key}: UNKNOWN_FORMAT")

    wh = env.get("STRIPE_WEBHOOK_SECRET", "")
    if not wh:
        print("STRIPE_WEBHOOK_SECRET: MISSING")
        blockers.append("STRIPE_WEBHOOK_SECRET: MISSING")
    elif is_placeholder(wh):
        print("STRIPE_WEBHOOK_SECRET: PLACEHOLDER")
        blockers.append("STRIPE_WEBHOOK_SECRET: PLACEHOLDER")
    elif wh.startswith("whsec_"):
        print("STRIPE_WEBHOOK_SECRET: FORMAT_OK")
    else:
        print("STRIPE_WEBHOOK_SECRET: UNKNOWN_FORMAT")
        blockers.append("STRIPE_WEBHOOK_SECRET: UNKNOWN_FORMAT")

    for k in ["VITE_API_BASE_URL", "VITE_WS_URL"]:
        line = status(front, k)
        print(line)
        if line.endswith("MISSING") or line.endswith("PLACEHOLDER"):
            blockers.append(line)

    if blockers:
        print(f"LAUNCH_READY: NO (blockers={len(blockers)})")
        print("BLOCKERS:")
        for b in blockers:
            print(f"- {b}")
        print("=== END CHECK ===")
        sys.exit(1)
    else:
        print("LAUNCH_READY: YES")

    print("=== END CHECK ===")


if __name__ == "__main__":
    main()
