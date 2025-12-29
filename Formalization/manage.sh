#!/bin/bash

# Quick alias for the main deployment script
# This provides backward compatibility with existing scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Forward all arguments to the main deploy script
"$SCRIPT_DIR/deploy.sh" "$@"
