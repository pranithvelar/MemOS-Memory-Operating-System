import os
import sys
import datetime
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.memory.facts import FactStore, extract_facts, check_conflicts

def run_test():
    print("Running Fact Memory Test...")
    workspace = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_workspace")
    os.makedirs(workspace, exist_ok=True)
    
    store = FactStore(workspace)
    
    # 1. Start with an existing fact
    tomorrow_dt = datetime.datetime.now() + datetime.timedelta(days=1)
    print(f"Adding fact for tomorrow: {tomorrow_dt}")
    store.add_fact("I have a meeting tomorrow.", tomorrow_dt, tomorrow_dt)
    
    # 2. Extract facts from new prompt
    new_prompt = "I guess I'll go to the beach tomorrow."
    print(f"\nUser says: '{new_prompt}'")
    
    facts_extracted = extract_facts(new_prompt)
    if not facts_extracted:
        print("Test failed: No facts extracted.")
        return
        
    print(f"Extracted facts: {facts_extracted}")
    
    # 3. Check for conflict
    active_facts = store.get_active_facts()
    warnings = check_conflicts(facts_extracted, active_facts)
    
    print("\nConflicts generated:")
    if warnings:
        for w in warnings:
            print(" ->", w)
    else:
        print(" -> None")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        traceback.print_exc()
