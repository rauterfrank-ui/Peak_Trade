"""Smoke test for Policy Critic CI gate hotfix - INTENTIONAL BLOCK TRIGGER."""
# This file contains AWS credentials patterns to verify the CI gate correctly blocks.
# Expected: Policy Critic workflow should FAIL (red) and prevent merge.

# Test AWS credentials (will trigger NO_SECRETS rule):
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# DO NOT MERGE - This is a smoke test file for hotfix validation.
