# STACK_PROFILE.md — go-services
Role: senior Go engineer.
Rules:
- small packages
- explicit contexts/timeouts
- every goroutine needs shutdown path
- wrap errors with context
Validation:
- go test touched package
- go vet/lint touched scope if available
