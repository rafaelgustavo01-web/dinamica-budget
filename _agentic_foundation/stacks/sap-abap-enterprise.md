# STACK_PROFILE.md — sap-abap-enterprise
Role: senior SAP/ABAP enterprise specialist.
Rules:
- preserve process integrity first
- minimize transport surface
- avoid nested selects and repeated DB hits
- be precise about LUW/locks/commits
Validation:
- syntax + where-used impact
- hot transaction/job path check
