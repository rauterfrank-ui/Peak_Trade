"""Test file to validate Policy Critic blocks AWS credentials."""
# CI Gate Block Trigger Test
# This file intentionally contains AWS credential patterns to test the Policy Critic gate.
# DO NOT commit this to main - for testing only!

# Test pattern - will trigger NO_SECRETS rule:
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
