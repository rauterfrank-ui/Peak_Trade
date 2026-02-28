#!/usr/bin/env python3
"""Create a temp config with mode=testnet from config.toml. Used by CI workflows."""
import re
import sys

src = "config/config.toml"
dst = sys.argv[1] if len(sys.argv) > 1 else "/tmp/config_testnet.toml"
t = open(src).read()
t = re.sub(
    r'(\[environment\][^\n]*\n(?:[^\n]*\n)*?)mode\s*=\s*"paper"',
    r'\1mode = "testnet"',
    t,
    count=1,
)
open(dst, "w").write(t)
print(f"Wrote {dst}")
