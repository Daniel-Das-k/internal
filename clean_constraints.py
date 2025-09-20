#!/usr/bin/env python3
"""
Clean Constraints Script

Removes AI-generated methods with wrong signatures from constraints.py
"""

import re

def clean_constraints_file():
    """Remove problematic AI-generated constraint methods"""

    with open('/Users/danieldas/Documents/timetable-scheduler/agents/constraints.py', 'r') as f:
        content = f.read()

    # Find and remove methods with wrong signatures (self, model, ...)
    # These are the problematic AI-generated methods
    patterns_to_remove = [
        r'def apply_max_teaching_hours_constraint\(self, model, assignment_vars\):.*?(?=\n    def|\n\n|\Z)',
        r'def apply_computer_lab_restriction_constraint\(self, model, lab_variables, theory_variables\):.*?(?=\n    def|\n\n|\Z)',
        r'def apply_senior_professor_morning_preference\(self, model, prof_vars, time_slots, senior_professors\):.*?(?=\n    def|\n\n|\Z)',
        r'def apply_evenly_distributed_core_subjects\(self, model, day_variables, course_type=\'core\'\):.*?(?=\n    def|\n\n|\Z)',
        r'def apply_first_year_end_time_constraint\(self, model, time_slots, first_year_groups\):.*?(?=\n    def|\n\n|\Z)',
        r'def apply_max_teacher_work_hours_constraint\(self, model, variables, teacher_id, max_hours\):.*?(?=\n    def|\n\n|\Z)',
    ]

    cleaned_content = content

    for pattern in patterns_to_remove:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL)

    # Remove extra whitespace
    cleaned_content = re.sub(r'\n\n\n+', '\n\n', cleaned_content)

    # Write cleaned content back
    with open('/Users/danieldas/Documents/timetable-scheduler/agents/constraints.py', 'w') as f:
        f.write(cleaned_content)

    print("✅ Cleaned constraints.py - removed problematic AI-generated methods")

if __name__ == "__main__":
    clean_constraints_file()