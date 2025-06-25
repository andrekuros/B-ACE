#!/bin/sh
echo -ne '\033c\033]0;B_ACE\a'
base_path="$(dirname "$(realpath "$0")")"
"$base_path/B_ACE_v0.1.x86_64" "$@"
