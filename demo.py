#!/usr/bin/env python3
"""
Demo: AI Constraint Code Generation System

Demonstrates how the system works:
1. User provides natural language constraint
2. CrewAI agent generates Python code
3. Code is appended to constraints.py
"""

from constraint_code_generator import ConstraintCodeGenerator

def demonstrate_system():
    """Demonstrate the complete system flow"""

    print("🎯 AI Constraint Code Generation Demo")
    print("=" * 50)

    print("\n📋 SYSTEM OVERVIEW:")
    print("1. User provides natural language constraint")
    print("2. CrewAI agent generates Python code")
    print("3. Code is appended to constraints.py")
    print("4. New constraint method becomes available")

    print("\n📝 EXAMPLE FLOW:")

    # Example constraint
    user_constraint = "Computer labs must be used only for practical sessions"
    print(f"\nUser Input: '{user_constraint}'")

    print("\n🤖 What the CrewAI agent will generate:")
    example_code = '''
    def apply_computer_lab_restriction_constraint(self, model, lab_variables, theory_variables):
        """
        Apply computer lab restriction constraint.

        Computer labs must be used only for practical sessions.
        Blocks theory courses from being scheduled in computer labs.
        """
        constraints_applied = 0

        # Find computer labs
        computer_labs = self.rooms_df[self.rooms_df['type'].str.contains('computer', case=False)]
        computer_lab_ids = computer_labs['id'].tolist()

        # Block theory courses from computer labs
        for group_name, group_data in theory_variables.items():
            for day_idx in range(len(group_data)):
                for slot_idx in range(len(group_data[day_idx])):
                    for room_id in computer_lab_ids:
                        if room_id in group_data[day_idx][slot_idx]:
                            # Block theory session from computer lab
                            model.Add(group_data[day_idx][slot_idx][room_id] == 0)
                            constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} computer lab restriction constraints")
        return constraints_applied
    '''

    print("Generated Code:")
    print("-" * 40)
    print(example_code)
    print("-" * 40)

    print("\n📄 Result: Code appended to constraints.py")
    print("✅ New method: apply_computer_lab_restriction_constraint()")
    print("✅ Ready to use in timetable optimization")

    print("\n🔧 How it integrates:")
    print("- constraints.py now has the new method")
    print("- apply_all_constraints() can call the new method")
    print("- OR-Tools model gets the new constraints")
    print("- Scheduler respects the new requirement")

    return True

def show_file_structure():
    """Show the current file structure"""

    print("\n\n📁 CURRENT FILE STRUCTURE:")
    print("=" * 50)

    files = {
        "main.py": "Main execution file (START HERE)",
        "constraint_code_generator.py": "CrewAI agent that generates code",
        "constraints.py": "Base constraints file (AI appends here)",
        "config/gemini_config.py": "Gemini AI model configuration",
        "requirements.txt": "Required Python packages",
        "demo.py": "This demonstration file"
    }

    for filename, description in files.items():
        print(f"📄 {filename:<30} - {description}")

    print("\n🚀 TO RUN THE SYSTEM:")
    print("1. Set GEMINI_API_KEY environment variable")
    print("2. Run: python main.py")
    print("3. Select option 1 to add new constraint")
    print("4. Enter natural language constraint")
    print("5. AI generates code and appends to constraints.py")

def show_expected_workflow():
    """Show the expected user workflow"""

    print("\n\n🔄 EXPECTED WORKFLOW:")
    print("=" * 50)

    steps = [
        ("User", "Describes constraint in natural language", "'Computer labs only for practicals'"),
        ("CrewAI Agent", "Analyzes requirement and generates Python code", "def apply_computer_lab_..."),
        ("System", "Appends code to constraints.py", "New method added to file"),
        ("Scheduler", "Uses new constraint in optimization", "Schedules respect new rule"),
        ("Result", "Timetable satisfies user requirement", "Computer labs → practicals only")
    ]

    for i, (actor, action, example) in enumerate(steps, 1):
        print(f"\n{i}. {actor}:")
        print(f"   Action: {action}")
        print(f"   Example: {example}")

    print(f"\n🎯 OUTCOME: User gets exactly what they requested!")

if __name__ == "__main__":
    demonstrate_system()
    show_file_structure()
    show_expected_workflow()

    print("\n\n✅ Demo Complete!")
    print("Run 'python main.py' to start the actual system.")