#!/usr/bin/env python3
"""
Dynamic Constraint System
Receives natural language prompts and converts them to working constraints.
"""

import re
import logging
from constraints import TimetableConstraints

class DynamicConstraintReceiver:
    """Receives and processes natural language constraints dynamically."""

    def __init__(self, base_constraints):
        self.base_constraints = base_constraints
        self.dynamic_constraints = []
        self.logger = logging.getLogger(__name__)

    def process_prompt(self, prompt):
        """Process a natural language prompt and convert to constraint."""
        prompt_lower = prompt.lower()

        # Pattern matching for common constraint types
        constraint_added = False

        # Pattern 1: Time blocking (e.g., "No classes between 8 AM and 11 AM")
        time_block_pattern = r"no classes.*between\s+(\d+)\s*(am|pm).*and\s+(\d+)\s*(am|pm)"
        time_match = re.search(time_block_pattern, prompt_lower)

        if time_match:
            start_hour = int(time_match.group(1))
            start_period = time_match.group(2)
            end_hour = int(time_match.group(3))
            end_period = time_match.group(4)

            constraint = self._create_time_block_constraint(start_hour, start_period, end_hour, end_period)
            self.dynamic_constraints.append(constraint)
            constraint_added = True

        # Pattern 2: Morning restrictions
        elif "no classes" in prompt_lower and any(word in prompt_lower for word in ["morning", "8", "9", "10", "11"]):
            constraint = self._create_morning_block_constraint()
            self.dynamic_constraints.append(constraint)
            constraint_added = True

        # Pattern 3: Teacher workload
        elif "teacher" in prompt_lower and any(word in prompt_lower for word in ["hours", "workload", "maximum"]):
            max_hours = self._extract_number(prompt)
            constraint = self._create_teacher_workload_constraint(max_hours or 8)
            self.dynamic_constraints.append(constraint)
            constraint_added = True

        # Pattern 4: Lunch break
        elif "lunch" in prompt_lower and any(word in prompt_lower for word in ["break", "time", "no classes"]):
            constraint = self._create_lunch_break_constraint()
            self.dynamic_constraints.append(constraint)
            constraint_added = True

        # Pattern 5: Room restrictions
        elif "computer" in prompt_lower and "lab" in prompt_lower:
            constraint = self._create_computer_lab_constraint()
            self.dynamic_constraints.append(constraint)
            constraint_added = True

        return constraint_added

    def _create_time_block_constraint(self, start_hour, start_period, end_hour, end_period):
        """Create a time blocking constraint."""
        # Convert to 24-hour format
        if start_period == "pm" and start_hour != 12:
            start_hour += 12
        if end_period == "pm" and end_hour != 12:
            end_hour += 12

        # Map to slot indices (assuming 8 AM = slot 0)
        start_slot = max(0, start_hour - 8)
        end_slot = max(0, end_hour - 8)

        def apply_time_block_constraint(model, lab_variables, theory_variables):
            """Block specific time slots."""
            constraints_applied = 0

            for slot_idx in range(start_slot, end_slot):
                # Block theory variables
                for course_vars in theory_variables.values():
                    for day_idx in course_vars:
                        if slot_idx in course_vars[day_idx]:
                            for room_vars in course_vars[day_idx][slot_idx].values():
                                model.Add(room_vars == 0)
                                constraints_applied += 1

                # Block lab variables
                for course_vars in lab_variables.values():
                    for day_idx in course_vars:
                        if slot_idx in course_vars[day_idx]:
                            for room_vars in course_vars[day_idx][slot_idx].values():
                                model.Add(room_vars == 0)
                                constraints_applied += 1

            return constraints_applied

        return {
            'name': f'time_block_{start_hour}_{end_hour}',
            'description': f'Block classes from {start_hour}:00 to {end_hour}:00',
            'function': apply_time_block_constraint
        }

    def _create_morning_block_constraint(self):
        """Create morning block constraint (8-11 AM)."""
        def apply_morning_block_constraint(model, lab_variables, theory_variables):
            """Block morning slots 0, 1, 2."""
            constraints_applied = 0
            morning_slots = [0, 1, 2]  # 8-11 AM

            for slot_idx in morning_slots:
                # Block theory sessions
                for course_vars in theory_variables.values():
                    for day_idx in course_vars:
                        if slot_idx in course_vars[day_idx]:
                            for room_vars in course_vars[day_idx][slot_idx].values():
                                model.Add(room_vars == 0)
                                constraints_applied += 1

                # Block lab sessions
                for course_vars in lab_variables.values():
                    for day_idx in course_vars:
                        if slot_idx in course_vars[day_idx]:
                            for room_vars in course_vars[day_idx][slot_idx].values():
                                model.Add(room_vars == 0)
                                constraints_applied += 1

            return constraints_applied

        return {
            'name': 'morning_block',
            'description': 'Block all classes from 8-11 AM',
            'function': apply_morning_block_constraint
        }

    def _create_teacher_workload_constraint(self, max_hours):
        """Create teacher workload constraint."""
        def apply_teacher_workload_constraint(model, lab_variables, theory_variables):
            """Limit teacher daily hours."""
            constraints_applied = 0

            # This would require teacher mapping - simplified for demo
            print(f"Would limit teachers to {max_hours} hours per day")
            return constraints_applied

        return {
            'name': f'teacher_workload_{max_hours}h',
            'description': f'Limit teachers to {max_hours} hours per day',
            'function': apply_teacher_workload_constraint
        }

    def _create_lunch_break_constraint(self):
        """Create lunch break constraint."""
        def apply_lunch_break_constraint(model, lab_variables, theory_variables):
            """Block lunch time slots."""
            constraints_applied = 0
            lunch_slots = [4, 5]  # Typically 12-1 PM

            for slot_idx in lunch_slots:
                for course_vars in theory_variables.values():
                    for day_idx in course_vars:
                        if slot_idx in course_vars[day_idx]:
                            for room_vars in course_vars[day_idx][slot_idx].values():
                                model.Add(room_vars == 0)
                                constraints_applied += 1

            return constraints_applied

        return {
            'name': 'lunch_break',
            'description': 'Block classes during lunch time (12-1 PM)',
            'function': apply_lunch_break_constraint
        }

    def _create_computer_lab_constraint(self):
        """Create computer lab restriction constraint."""
        def apply_computer_lab_constraint(model, lab_variables, theory_variables):
            """Ensure CS courses use computer labs."""
            constraints_applied = 0

            # This would require room type checking - simplified for demo
            print("Would ensure Computer Science courses use computer labs only")
            return constraints_applied

        return {
            'name': 'computer_lab_restriction',
            'description': 'CS courses must use computer labs',
            'function': apply_computer_lab_constraint
        }

    def _extract_number(self, text):
        """Extract number from text."""
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else None

    def apply_all_constraints(self, model, lab_variables, theory_variables):
        """Apply all dynamic constraints."""
        total_applied = 0

        for constraint in self.dynamic_constraints:
            try:
                applied = constraint['function'](model, lab_variables, theory_variables)
                total_applied += applied
                self.logger.info(f"Applied dynamic constraint '{constraint['name']}': {applied} constraints")
            except Exception as e:
                self.logger.error(f"Failed to apply constraint '{constraint['name']}': {e}")

        return total_applied

    def get_active_constraints(self):
        """Get list of active dynamic constraints."""
        return [{'name': c['name'], 'description': c['description']} for c in self.dynamic_constraints]

    def clear_constraints(self):
        """Clear all dynamic constraints."""
        self.dynamic_constraints = []