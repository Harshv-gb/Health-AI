
import json

# Load department map
with open("./data/department_map.json") as f:
    department_map = json.load(f)["department_map"]

def get_department(condition_name: str) -> str:
    """
    Return department for a given condition.
    Falls back to 'General Medicine' if not found.
    """
    condition_name = condition_name.lower()
    for cond, dept in department_map.items():
        if cond.lower() == condition_name:
            return dept
    return "General Medicine"

if __name__ == "__main__":
    # Quick test
    print(get_department("Heart Attack"))   # Cardiology
    print(get_department("Migraine"))       # Neurology
    print(get_department("Unknown Issue"))  # General Medicine
