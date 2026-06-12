import json
rules = json.load(open("rules/structural_rules.json"))
costs = json.load(open("data/unit_costs.json"))
props = json.load(open("data/material_properties.json"))
print(f"Loaded {len(rules)} rules, {len(costs)} cost categories, {len(props)} material types")
