from planner_core import InteriorPlanner

planner = InteriorPlanner()

# Initial generation
result = planner("A gym in San Diego")
result.save("v1.png")

# Iterative edits — state is preserved between calls
result = planner.edit("make it more minimalist, remove most equipment")
result.save("v2.png")

result = planner.edit("add large windows with ocean views")
result.save("v3.png")
