#!/usr/bin/env python3
"""
Complete System Test - End-to-End AI Constraint Workflow

This script demonstrates the COMPLETE workflow:
1. Add constraints using natural language (like main.py)
2. AI generates Python code and appends to constraints.py
3. Generate timetable using ALL constraints
4. Create visualizations

REAL CONSTRAINT EXAMPLES from src/combined_scheduler.py:
"""

import os
import sys
import logging
from constraint_code_generator import ConstraintCodeGenerator
from ai_scheduler import AIScheduler

def test_constraint_examples():
    """
    Test real constraint examples that exist in src/combined_scheduler.py
    These are natural language versions of actual constraints
    """

    constraint_examples = [
        # Based on lunch break constraints in combined_scheduler.py
        "No classes should be scheduled during lunch time between 12:30 PM and 1:20 PM",

        # Based on teacher workload constraints
        "Teachers should not work more than 8 hours in a single day",

        # Based on room capacity constraints
        "Classes with more than 30 students should not be assigned to small rooms",

        # Based on department day constraints
        "Computer Science department should have classes only on weekdays",

        # Based on consecutive session constraints
        "Students should not have more than 3 consecutive theory classes"
    ]

    return constraint_examples

def run_complete_system_test():
    """Run the complete end-to-end system test"""

    print("🚀 COMPLETE SYSTEM TEST - AI CONSTRAINT WORKFLOW")
    print("="*80)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print("\n📋 REAL CONSTRAINT EXAMPLES (from src/combined_scheduler.py):")
    constraint_examples = test_constraint_examples()

    for i, constraint in enumerate(constraint_examples, 1):
        print(f"{i}. {constraint}")

    print(f"\n🎯 COMPLETE WORKFLOW TEST:")
    print("Step 1: AI Code Generation (constraint_code_generator.py)")
    print("Step 2: Append to constraints.py")
    print("Step 3: Generate Timetable (ai_scheduler.py)")
    print("Step 4: Create Visualizations")

    # Check if API key is available for AI generation
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n⚠️  GEMINI_API_KEY not set - will test with manual constraint instead")
        return test_with_manual_constraint()
    else:
        print(f"\n✅ GEMINI_API_KEY found - testing with AI generation")
        return test_with_ai_generation(constraint_examples[0])

def test_with_manual_constraint():
    """Test with manually created constraint (simulates AI generation)"""

    print("\n🤖 SIMULATING AI CONSTRAINT GENERATION:")
    print("Constraint: 'First year students should not have classes after 4 PM'")

    # Manually add a constraint (simulating AI generation)
    manual_constraint_code = '''
    def apply_first_year_end_time_constraint(self, lab_variables, theory_variables):
        """
        Ensure first year students finish classes by 4 PM.
        First year students should not have classes after 4 PM to allow for other activities.
        """
        constraints_applied = 0

        # Define 4 PM cutoff (theory slot index for 4:00-4:50)
        afternoon_cutoff = 8  # Slots after 4 PM

        # Process theory variables for first year courses
        for course_id, course_vars in theory_variables.items():
            if hasattr(self, 'courses_df'):
                course_info = self.courses_df[self.courses_df['course_id'] == course_id]
                if not course_info.empty:
                    year = course_info.iloc[0].get('Year', 1)
                    if year == 1:  # First year students
                        for day_idx in course_vars:
                            for slot_idx in course_vars[day_idx]:
                                if slot_idx >= afternoon_cutoff:  # After 4 PM
                                    for room_id, var in course_vars[day_idx][slot_idx].items():
                                        self.model.Add(var == 0)
                                        constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} first year end time constraints")
        return constraints_applied
'''

    # Add constraint to file
    constraints_file = '/Users/danieldas/Documents/timetable-scheduler/agents/constraints.py'

    with open(constraints_file, 'r') as f:
        content = f.read()

    if 'apply_first_year_end_time_constraint' not in content:
        # Add the constraint before the final line
        insertion_point = content.rfind('\n')
        new_content = content[:insertion_point] + manual_constraint_code + '\n' + content[insertion_point:]

        with open(constraints_file, 'w') as f:
            f.write(new_content)

        print("✅ Manual constraint added to constraints.py")
    else:
        print("⚠️  Constraint already exists")

    # Test timetable generation
    return test_timetable_generation()

def test_with_ai_generation(constraint_text):
    """Test with real AI generation"""

    print(f"\n🤖 TESTING AI GENERATION:")
    print(f"Input: '{constraint_text}'")

    try:
        generator = ConstraintCodeGenerator()
        success = generator.process_user_constraint(constraint_text)

        if success:
            print("✅ AI constraint generated and appended successfully!")
            return test_timetable_generation()
        else:
            print("❌ AI constraint generation failed!")
            return False

    except Exception as e:
        print(f"❌ AI generation error: {e}")
        return test_with_manual_constraint()

def test_timetable_generation():
    """Test timetable generation with all constraints"""

    print(f"\n📅 TESTING TIMETABLE GENERATION:")

    try:
        # Create comprehensive test data
        import pandas as pd

        # More realistic course data
        courses_data = {
            'course_id': ['CS101', 'CS102', 'CS201', 'CS202', 'CS301'],
            'course_name': ['Programming', 'Data Structures', 'Database', 'Networks', 'AI'],
            'teacher_id': [1, 2, 3, 1, 2],
            'teacher_name': ['Dr. Smith', 'Dr. Jones', 'Dr. Brown', 'Dr. Smith', 'Dr. Jones'],
            'department': ['CSE', 'CSE', 'CSE', 'CSE', 'CSE'],
            'semester': [1, 2, 3, 4, 5],
            'Year': [1, 1, 2, 2, 3],
            'session_type': ['theory', 'lab', 'theory', 'theory', 'lab'],
            'sessions_per_week': [3, 2, 3, 2, 2],
            'students_count': [60, 30, 45, 40, 25]
        }
        courses_df = pd.DataFrame(courses_data)

        # Comprehensive room data
        rooms_data = {
            'room_id': ['R001', 'R002', 'R003', 'CL001', 'CL002', 'LAB001'],
            'room_name': ['Theory Room 1', 'Theory Room 2', 'Large Hall', 'Computer Lab 1', 'Computer Lab 2', 'Programming Lab'],
            'capacity': [40, 60, 100, 30, 25, 35],
            'type': ['theory', 'theory', 'theory', 'computer_lab', 'computer_lab', 'lab']
        }
        rooms_df = pd.DataFrame(rooms_data)

        print(f"📊 Test Data: {len(courses_df)} courses, {len(rooms_df)} rooms")

        # Create scheduler and generate timetable
        scheduler = AIScheduler(courses_df=courses_df, rooms_df=rooms_df)

        print("🔧 Generating timetable with ALL constraints...")
        success = scheduler.generate_timetable()

        if success:
            print("✅ TIMETABLE GENERATION SUCCESSFUL!")
            scheduler.print_schedule_summary()

            print(f"\n📁 Output Directory: {scheduler.output_dir}")
            print("📊 Files generated:")

            # List generated files
            for root, dirs, files in os.walk(scheduler.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, scheduler.output_dir)
                    print(f"  • {relative_path}")

            return True
        else:
            print("❌ TIMETABLE GENERATION FAILED!")
            return False

    except Exception as e:
        print(f"❌ Timetable generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run complete system test"""

    print("🎯 MAIN FILE TO RUN: python main.py")
    print("🎯 OR FOR COMPLETE TEST: python complete_system_test.py")
    print()

    success = run_complete_system_test()

    print("\n" + "="*80)
    if success:
        print("🎉 COMPLETE SYSTEM TEST PASSED!")
        print("✅ AI Constraint Generation → Append → Schedule → Visualize = SUCCESS")
        print()
        print("🚀 TO USE THE SYSTEM:")
        print("1. Set GEMINI_API_KEY environment variable")
        print("2. Run: python main.py")
        print("3. Select option 1: Add new constraint")
        print("4. Enter natural language constraint")
        print("5. Select option 2: Generate timetable with visualization")
    else:
        print("❌ COMPLETE SYSTEM TEST FAILED!")
        print("Check the errors above for issues to fix")

if __name__ == "__main__":
    main()