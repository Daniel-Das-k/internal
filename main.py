#!/usr/bin/env python3
"""
Simple Prompt-to-Timetable System

Enter natural language prompts and immediately see timetable generation results.
"""

import os
import json
import logging
import re
from ai_scheduler import AIScheduler

# Suppress verbose logging
logging.basicConfig(level=logging.WARNING)

def parse_time_constraint(prompt):
    """
    Dynamically parse time constraints from natural language prompt.
    Returns (start_time, end_time) in 24-hour format or None if no constraint found.
    """
    prompt_lower = prompt.lower()

    # Check if this is a time blocking constraint
    if not any(keyword in prompt_lower for keyword in ["no classes", "block", "between", "from", "to"]):
        return None

    # Time patterns to match
    time_patterns = [
        r'between\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+(?:and|to)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))',
        r'from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+(?:to|until)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))',
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+(?:to|-)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))'
    ]

    for pattern in time_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            start_time_str = match.group(1).strip()
            end_time_str = match.group(2).strip()

            try:
                start_hour = parse_time_to_24h(start_time_str)
                end_hour = parse_time_to_24h(end_time_str)
                return (start_hour, end_hour)
            except ValueError:
                continue

    return None

def parse_time_to_24h(time_str):
    """Convert time string like '8 AM', '12:40 PM' to 24-hour format."""
    time_str = time_str.strip().lower()

    # Extract AM/PM
    is_pm = 'pm' in time_str
    time_str = time_str.replace('am', '').replace('pm', '').strip()

    # Handle cases like "8", "8:30"
    if ':' in time_str:
        hour_str, minute_str = time_str.split(':')
        hour = int(hour_str)
        minute = int(minute_str)
    else:
        hour = int(time_str)
        minute = 0

    # Convert to 24-hour format
    if is_pm and hour != 12:
        hour += 12
    elif not is_pm and hour == 12:
        hour = 0

    return hour + minute / 60.0  # Return as decimal hours

def time_to_slot_index(hour_decimal):
    """Convert 24-hour decimal time to theory time slot index."""
    # Theory time slots mapping
    time_slots = [
        8.0,   # 0: 8:00-8:50 AM
        9.0,   # 1: 9:00-9:50 AM
        10.17, # 2: 10:10-11:00 AM
        11.17, # 3: 11:10-12:00 PM
        12.17, # 4: 12:10-1:00 PM
        13.33, # 5: 1:20-2:10 PM
        14.33, # 6: 2:20-3:10 PM
        15.5,  # 7: 3:30-4:20 PM
        16.5,  # 8: 4:30-5:20 PM
        17.5,  # 9: 5:30-6:20 PM
        18.5   # 10: 6:30-7:20 PM
    ]

    # Find the closest slot
    for i, slot_time in enumerate(time_slots):
        if hour_decimal <= slot_time + 0.83:  # Each slot is ~50 minutes
            return i

    return len(time_slots) - 1  # Return last slot if beyond

def display_menu():
    """Display the main menu options"""
    print("\n" + "="*60)
    print("🎯 PROMPT-TO-TIMETABLE SYSTEM")
    print("="*60)
    print("Enter natural language constraints and see immediate results!")
    print()
    print("1. Generate timetable from prompt")
    print("2. Compare two constraint scenarios")
    print("3. View sample prompts")
    print("4. Exit")
    print("="*60)

def process_prompt_and_generate(prompt):
    """Process a prompt and generate timetable immediately."""
    print(f"\n🔄 Processing prompt: \"{prompt}\"")

    # Parse time constraints dynamically
    time_constraint = parse_time_constraint(prompt)

    if time_constraint:
        start_time, end_time = time_constraint
        start_slot = time_to_slot_index(start_time)
        end_slot = time_to_slot_index(end_time)

        print("🚫 Detected: Time block constraint")
        print(f"   Parsed times: {start_time:.1f}h to {end_time:.1f}h")
        print(f"   Effect: Will block slots {start_slot} to {end_slot}")

        # Pass the dynamic slot range to the scheduler
        scheduler = AIScheduler(block_morning_slots=True, blocked_slots=(start_slot, end_slot))
        mode = f"BLOCKED_{start_slot}_TO_{end_slot}"
    else:
        print("🟢 Detected: General scheduling")
        print("   Effect: Classes scattered across all available time slots")
        scheduler = AIScheduler(block_morning_slots=False)
        mode = "GENERAL"

    print(f"\n🚀 Generating timetable with {mode} mode...")
    success = scheduler.generate_timetable()

    if success:
        print("\n🎉 SUCCESS! Timetable generated and visualized!")

        # Analyze results
        analysis = analyze_timetable(scheduler.output_dir)
        display_results(analysis, prompt, mode)

        return scheduler.output_dir
    else:
        print("\n❌ Failed to generate timetable!")
        return None

def analyze_timetable(output_dir):
    """Analyze the generated timetable."""
    theory_file = f"{output_dir}/ai_theory_schedule.json"

    analysis = {
        'output_dir': output_dir,
        'total_sessions': 0,
        'morning_sessions': 0,  # slots 0-3 (8:00 AM - 12:00 PM)
        'afternoon_sessions': 0,  # slots 4+ (12:10 PM onwards)
        'time_slots_used': []
    }

    try:
        with open(theory_file) as f:
            theory_data = json.load(f)

        analysis['total_sessions'] = len(theory_data)
        slot_counts = {}

        for session in theory_data:
            slot = session.get('slot_index', 0)
            slot_counts[slot] = slot_counts.get(slot, 0) + 1

            if slot <= 3:  # Morning slots (8:00 AM - 12:00 PM)
                analysis['morning_sessions'] += 1
            else:  # Afternoon slots (12:10 PM onwards)
                analysis['afternoon_sessions'] += 1

        analysis['time_slots_used'] = sorted(slot_counts.keys())
        analysis['slot_details'] = slot_counts

    except Exception as e:
        print(f"Error analyzing timetable: {e}")

    return analysis

def display_results(analysis, prompt, mode):
    """Display timetable analysis results."""
    print(f"\n📊 TIMETABLE ANALYSIS:")
    print(f"   📝 Prompt: \"{prompt}\"")
    print(f"   🎯 Mode: {mode}")
    print(f"   📁 Output: {analysis['output_dir']}")
    print(f"   📚 Total sessions: {analysis['total_sessions']}")
    print(f"   🌅 Morning sessions (8 AM-12 PM): {analysis['morning_sessions']}")
    print(f"   🌇 Afternoon sessions (12:10 PM+): {analysis['afternoon_sessions']}")
    print(f"   🕐 Time slots used: {analysis['time_slots_used']}")

    if 'slot_details' in analysis:
        print(f"\n   📋 Detailed breakdown:")
        for slot, count in analysis['slot_details'].items():
            time_range = get_time_range(slot)
            print(f"      Slot {slot} ({time_range}): {count} sessions")

def get_time_range(slot):
    """Get time range for slot number."""
    time_ranges = {
        0: "8:00-8:50", 1: "9:00-9:50", 2: "10:10-11:00",
        3: "11:10-12:00", 4: "12:10-1:00", 5: "1:20-2:10",
        6: "2:20-3:10", 7: "3:30-4:20", 8: "4:30-5:20",
        9: "5:30-6:20", 10: "6:30-7:20"
    }
    return time_ranges.get(slot, f"Slot {slot}")

def generate_from_prompt():
    """Main function to generate timetable from user prompt."""
    print("\n📝 GENERATE TIMETABLE FROM PROMPT")
    print("-" * 50)
    print("Enter a natural language constraint and see immediate results!")
    print()

    prompt = input("Enter your prompt: ").strip()

    if not prompt:
        print("❌ No prompt entered!")
        return

    output_dir = process_prompt_and_generate(prompt)

    if output_dir:
        print(f"\n✅ Complete! Check visualizations in: {output_dir}/visualizations/")

def compare_two_scenarios():
    """Compare two different constraint scenarios."""
    print("\n🔄 COMPARE TWO CONSTRAINT SCENARIOS")
    print("-" * 50)
    print("This will generate two timetables for comparison")
    print()

    # Scenario 1: General
    prompt1 = "General scheduling with no additional restrictions"
    print(f"📋 Scenario 1: \"{prompt1}\"")
    output1 = process_prompt_and_generate(prompt1)

    print("\n" + "="*50)

    # Scenario 2: Morning block
    prompt2 = "No classes should be scheduled between 8 AM and 11:30 AM"
    print(f"📋 Scenario 2: \"{prompt2}\"")
    output2 = process_prompt_and_generate(prompt2)

    # Compare results
    if output1 and output2:
        print("\n" + "="*50)
        print("🔍 COMPARISON SUMMARY:")

        analysis1 = analyze_timetable(output1)
        analysis2 = analyze_timetable(output2)

        print(f"\n📊 Morning Sessions (8 AM-12 PM):")
        print(f"   Scenario 1 (General): {analysis1['morning_sessions']} sessions")
        print(f"   Scenario 2 (Block 8-11:30): {analysis2['morning_sessions']} sessions")

        difference = analysis1['morning_sessions'] - analysis2['morning_sessions']
        if difference > 0:
            print(f"   ✅ Constraint reduced morning sessions by {difference}")

        print(f"\n📁 Generated files:")
        print(f"   Scenario 1: {output1}")
        print(f"   Scenario 2: {output2}")

def show_sample_prompts():
    """Show sample prompts that work with the system."""
    print("\n📋 SAMPLE PROMPTS")
    print("-" * 30)

    samples = [
        {
            "prompt": "General scheduling with no additional restrictions",
            "effect": "Classes scheduled in any available time slots"
        },
        {
            "prompt": "No classes should be scheduled between 8 AM and 11:30 AM",
            "effect": "Blocks morning slots, forces afternoon scheduling"
        },
        {
            "prompt": "Block all morning classes from 8 to 11:30",
            "effect": "Same as above - alternative phrasing"
        }
    ]

    for i, sample in enumerate(samples, 1):
        print(f"\n{i}. \"{sample['prompt']}\"")
        print(f"   Effect: {sample['effect']}")

    print(f"\n💡 Try copying and pasting these prompts in option 1!")

def check_prerequisites(check_api_key=True):
    """Check if required files and environment are set up"""
    print("🔍 Checking prerequisites...")

    issues = []

    # Check constraints.py exists
    constraints_file = "/Users/danieldas/Documents/timetable-scheduler/agents/constraints.py"
    if not os.path.exists(constraints_file):
        issues.append("constraints.py file not found")

    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ All prerequisites met!")
        return True

def main():
    """Main application loop - Simple Prompt-to-Timetable System"""
    print("🚀 Simple Prompt-to-Timetable System")
    print("Enter natural language and get immediate timetable generation!")

    # Basic setup check
    basic_check = check_prerequisites(check_api_key=False)
    if not basic_check:
        print("\n❌ Basic setup incomplete. Please check constraints.py file.")
        return

    while True:
        display_menu()

        try:
            choice = input("\nSelect option (1-4): ").strip()

            if choice == '1':
                generate_from_prompt()
            elif choice == '2':
                compare_two_scenarios()
            elif choice == '3':
                show_sample_prompts()
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice! Please select 1-4.")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    main()