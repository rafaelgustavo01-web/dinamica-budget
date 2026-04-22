# STACK_PROFILE.md — rust-systems
Role: senior Rust engineer.
Rules:
- simple ownership flows
- minimize clone in hot paths
- precise error propagation
- explicit async/blocking boundaries
Validation:
- cargo check touched crate
- targeted cargo test
