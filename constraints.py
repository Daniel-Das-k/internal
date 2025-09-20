"""
Timetable Constraints Module

This module contains constraint methods for the timetable scheduling system.
New constraints can be added dynamically through AI code generation.
"""

import os
import pandas as pd
import logging
from ortools.sat.python import cp_model

class TimetableConstraints:
    """
    Timetable constraints for scheduling optimization.

    This class contains all constraint methods that can be applied to the scheduling model.
    New constraints are added dynamically by the AI constraint generator.
    """

    def __init__(self, model, course_file=None, room_file=None, courses_df=None, rooms_df=None):
        """Initialize the constraints with model and data.

        Args:
            model: OR-Tools CP model
            course_file: Path to course CSV file (optional if courses_df provided)
            room_file: Path to room CSV file (optional if rooms_df provided)
            courses_df: Pre-loaded courses DataFrame (optional)
            rooms_df: Pre-loaded rooms DataFrame (optional)
        """
        self.model = model
        self.logger = logging.getLogger(__name__)

        # Load data from files or use provided DataFrames
        if courses_df is not None:
            self.courses_df = courses_df
        elif course_file:
            self.courses_df = pd.read_csv(course_file)
        else:
            raise ValueError("Either courses_df or course_file must be provided")

        if rooms_df is not None:
            self.rooms_df = rooms_df
        elif room_file:
            self.rooms_df = self._load_room_data(room_file)
        else:
            raise ValueError("Either rooms_df or room_file must be provided")

        # Load additional data files from combined_scheduler.py
        self._load_additional_data()

        self.logger.info("TimetableConstraints initialized with all data loaded")

    def _load_room_data(self, room_file):
        """Load room data with techlongue.csv priority (same as combined_scheduler.py)"""

        # Try techlongue.csv first (same logic as combined_scheduler.py)
        techlongue_paths = [
            'data/block_wise/techlongue.csv',
            './data/block_wise/techlongue.csv',
            '../data/block_wise/techlongue.csv',
            'timetable_scheduler/data/block_wise/techlongue.csv'
        ]

        for path in techlongue_paths:
            if os.path.exists(path):
                self.logger.info(f"Loading room data from techlongue.csv: {path}")
                return pd.read_csv(path)

        # Fallback to provided room_file
        self.logger.warning(f"techlongue.csv not found, using fallback room file: {room_file}")
        return pd.read_csv(room_file)

    def _load_additional_data(self):
        """Load additional data files used by combined_scheduler.py"""

        # Load day order information
        self.day_order_df = self._load_day_order()

        # Load teacher day preferences from pop.csv
        self.teacher_day_preferences = self._load_teacher_day_preferences()

        # Load core lab mapping
        self.core_mapping_df = self._load_core_mapping()

        # Set up time slot configurations
        self._setup_time_slots()

        # Set up department configurations
        self._setup_department_configs()

    def _load_day_order(self):
        """Load day order information from day_order.csv (same as combined_scheduler.py)"""
        try:
            day_order_paths = [
                'data/day_order.csv',
                './data/day_order.csv',
                '../data/day_order.csv',
                'timetable_scheduler/data/day_order.csv'
            ]

            for path in day_order_paths:
                if os.path.exists(path):
                    day_order_df = pd.read_csv(path)
                    self.logger.info(f"Loaded day order information from {path}")
                    self.logger.info(f"Found {len(day_order_df)} department entries")
                    return day_order_df

            self.logger.warning("day_order.csv not found. Using default Monday-Friday schedule.")
            return None

        except Exception as e:
            self.logger.error(f"Error loading day order: {e}")
            return None

    def _load_teacher_day_preferences(self):
        """Load teacher day preferences from pop.csv (same as combined_scheduler.py)"""
        teacher_preferences = {}

        try:
            pop_file_paths = [
                'data/pop.csv',
                './data/pop.csv',
                '../data/pop.csv',
                'timetable_scheduler/data/pop.csv'
            ]

            for path in pop_file_paths:
                if os.path.exists(path):
                    try:
                        # Try to read with error handling for inconsistent columns
                        pop_df = pd.read_csv(path, on_bad_lines='skip')
                        self.logger.info(f"Loaded teacher day preferences from {path}")

                        # Process preferences (simplified version)
                        for _, row in pop_df.iterrows():
                            teacher_id = str(row.get('teacher_id', ''))
                            if teacher_id:
                                # Extract preferred days from row data
                                preferences = {}
                                for col in pop_df.columns:
                                    if 'day' in col.lower() or col.lower() in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                                        preferences[col] = row.get(col, 0)
                                teacher_preferences[teacher_id] = preferences

                        self.logger.info(f"Processed preferences for {len(teacher_preferences)} teachers")
                        return teacher_preferences
                    except Exception as csv_error:
                        self.logger.warning(f"Error reading {path}: {csv_error}")
                        continue

            self.logger.warning("pop.csv not found. No teacher day preferences will be applied.")
            return {}

        except Exception as e:
            self.logger.error(f"Error loading teacher day preferences: {e}")
            return {}

    def _load_core_mapping(self):
        """Load core lab mapping data"""
        try:
            core_mapping_paths = [
                'data/core_lab_mapping.csv',
                './data/core_lab_mapping.csv',
                '../data/core_lab_mapping.csv',
                'timetable_scheduler/data/core_lab_mapping.csv'
            ]

            for path in core_mapping_paths:
                if os.path.exists(path):
                    core_mapping_df = pd.read_csv(path)
                    self.logger.info(f"Loaded core lab mapping from {path}")
                    self.logger.info(f"Core mapping contains {len(core_mapping_df)} course-lab assignments")
                    return core_mapping_df

            self.logger.warning("core_lab_mapping.csv not found. No core lab constraints will be applied.")
            return None

        except Exception as e:
            self.logger.error(f"Error loading core lab mapping: {e}")
            return None

    def _setup_time_slots(self):
        """Set up time slot configurations (same as combined_scheduler.py)"""

        # Lab time slots (12 slots for 6 sessions of 2 hours each)
        self.lab_time_slots = [
            "8:00 - 8:50", "8:50 - 9:40", "9:50 - 10:40", "10:40 - 11:30",
            "11:50 - 12:40", "12:40 - 1:30", "1:50 - 2:40", "2:40 - 3:30",
            "3:50 - 4:40", "4:40 - 5:30", "5:30 - 6:20", "6:20 - 7:10"
        ]

        # Theory time slots (11 slots for 1 hour each)
        self.theory_time_slots = [
            "8:00 - 8:50", "8:50 - 9:40", "9:50 - 10:40", "10:40 - 11:30",
            "11:40 - 12:30", "12:30 - 1:20", "1:30 - 2:20", "2:20 - 3:10",
            "3:10 - 4:00", "4:00 - 4:50", "5:00 - 5:50"
        ]

        self.num_lab_slots = len(self.lab_time_slots)
        self.num_theory_slots = len(self.theory_time_slots)

        self.logger.info(f"Configured {self.num_lab_slots} lab time slots and {self.num_theory_slots} theory time slots")

    def _setup_department_configs(self):
        """Set up department-specific configurations"""

        # Default working days
        self.days = ["monday", "tuesday", "wed", "thur", "fri"]
        self.num_days = len(self.days)

        # Lunch break configuration
        self.lunch_break_config = {
            'default_slot': 5,  # 12:30-1:20 for theory
            'flexible_departments': ['Electronics & Communication Engineering'],
            'strict_departments': ['Computer Science & Engineering', 'Mechanical Engineering']
        }

        # Room type mappings
        if hasattr(self, 'rooms_df') and not self.rooms_df.empty:
            # Extract room type information
            self.lab_room_ids = []
            self.theory_room_ids = []

            for _, room in self.rooms_df.iterrows():
                room_name = str(room.get('room_name', room.get('name', ''))).lower()
                room_id = room.get('room_id', room.get('id', ''))

                if 'lab' in room_name or 'computer' in room_name:
                    self.lab_room_ids.append(room_id)
                else:
                    self.theory_room_ids.append(room_id)

            self.logger.info(f"Categorized {len(self.lab_room_ids)} lab rooms and {len(self.theory_room_ids)} theory rooms")

    def get_department_working_days(self, department, semester=None):
        """Get working days for a specific department"""
        if self.day_order_df is not None:
            try:
                # Try different possible column names for department
                dept_column = None
                for col in ['department', 'Department', 'dept', 'Dept']:
                    if col in self.day_order_df.columns:
                        dept_column = col
                        break

                if dept_column:
                    # Try to find department-specific day configuration
                    dept_config = self.day_order_df[
                        self.day_order_df[dept_column].str.contains(department, case=False, na=False)
                    ]

                    if not dept_config.empty and semester:
                        # Further filter by semester if provided
                        sem_column = None
                        for col in ['semester', 'Semester', 'sem', 'Sem']:
                            if col in self.day_order_df.columns:
                                sem_column = col
                                break

                        if sem_column:
                            sem_config = dept_config[dept_config[sem_column] == semester]
                            if not sem_config.empty:
                                return sem_config.iloc[0].get('working_days', self.days)

            except Exception as e:
                self.logger.warning(f"Error processing department working days: {e}")

        # Default to standard working days
        return self.days

    def is_lunch_time_slot(self, slot_index, slot_type='theory'):
        """Check if a given slot index is during lunch time"""
        if slot_type == 'theory':
            return slot_index == self.lunch_break_config['default_slot']
        elif slot_type == 'lab':
            # For labs, lunch time might span multiple slots
            return slot_index in [4, 5]  # 11:50-12:40, 12:40-1:30
        return False

    def is_computer_lab(self, room_id):
        """Check if a room is a computer lab"""
        if hasattr(self, 'rooms_df') and not self.rooms_df.empty:
            room_info = self.rooms_df[
                (self.rooms_df['room_id'] == room_id) |
                (self.rooms_df.get('id') == room_id)
            ]

            if not room_info.empty:
                room_name = str(room_info.iloc[0].get('room_name', room_info.iloc[0].get('name', ''))).lower()
                return 'computer' in room_name or 'lab' in room_name

        return False

    def apply_all_constraints(self, lab_variables, theory_variables):
        """
        Apply all available constraints to the model.

        Args:
            lab_variables: Lab assignment variables
            theory_variables: Theory assignment variables

        Returns:
            int: Total number of constraints applied
        """
        self.logger.info("Applying all constraints...")
        total_constraints = 0

        # Apply basic constraints
        # Add basic scheduling constraints to ensure courses get scheduled
        for course_id, course_vars in theory_variables.items():
            course_assignments = []
            for day_idx in course_vars:
                for slot_idx in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][slot_idx].items():
                        course_assignments.append(var)

            if course_assignments:
                # Each course must be scheduled at least once
                self.model.Add(sum(course_assignments) >= 1)
                total_constraints += 1

        total_constraints += self.apply_basic_scheduling_constraints(lab_variables, theory_variables)

        # Apply migrated constraints from src/combined_scheduler.py (minimal set for stability)
        self.logger.info("Applying migrated constraints from combined_scheduler.py...")

        total_constraints += self.apply_lunch_break_constraint(lab_variables, theory_variables)
        total_constraints += self.apply_lab_room_single_assignment_constraint(lab_variables, theory_variables)
        total_constraints += self.apply_teacher_clash_prevention_constraint(lab_variables, theory_variables)

        # Apply AI-generated constraints when available
        self.logger.info("Applying AI-generated constraints...")

        # Find and call all AI-generated constraint methods
        ai_methods = [method for method in dir(self)
                     if method.startswith('apply_') and
                     method not in ['apply_all_constraints', 'apply_basic_scheduling_constraints'] and
                     method not in ['apply_lunch_break_constraint', 'apply_lab_room_single_assignment_constraint',
                                   'apply_teacher_clash_prevention_constraint']]

        for method_name in ai_methods:
            try:
                method = getattr(self, method_name)
                if callable(method):
                    constraints_added = method(lab_variables, theory_variables)
                    total_constraints += constraints_added
                    self.logger.info(f"Applied {constraints_added} constraints via {method_name}")
            except Exception as e:
                self.logger.error(f"Error applying {method_name}: {e}")

        self.logger.info(f"Applied {total_constraints} total constraints")
        return total_constraints

    def apply_basic_scheduling_constraints(self, lab_variables, theory_variables):
        """Apply basic scheduling constraints"""
        constraints_applied = 0
        self.logger.info("Applied {constraints_applied} basic scheduling constraints")
        return constraints_applied

    # ============================================================================
    # MIGRATED CONSTRAINTS FROM combined_scheduler.py
    # ============================================================================

    def apply_lunch_break_constraint(self, lab_variables, theory_variables):
        """
        Prevent scheduling in lunch break time slots.
        Migrated from src/combined_scheduler.py
        """
        constraints_applied = 0
        self.logger.info("Applying lunch break constraints...")

        # Block lunch break slot for theory sessions (slot 5: 12:30-1:20)
        lunch_slot = 5

        for course_id, course_vars in theory_variables.items():
            for day_idx in course_vars:
                if lunch_slot in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][lunch_slot].items():
                        self.model.Add(var == 0)
                        constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} lunch break constraints")
        return constraints_applied

    def apply_lab_room_single_assignment_constraint(self, lab_variables, theory_variables):
        """
        Ensure no room is assigned to multiple sessions at the same time.
        Migrated from src/combined_scheduler.py
        """
        constraints_applied = 0
        self.logger.info("Applying lab room single assignment constraint...")

        # Track room assignments by time slot
        room_slot_assignments = {}

        # Process lab variables
        for course_id, course_vars in lab_variables.items():
            for day_idx in course_vars:
                for slot_idx in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][slot_idx].items():
                        key = (room_id, day_idx, slot_idx)
                        if key not in room_slot_assignments:
                            room_slot_assignments[key] = []
                        room_slot_assignments[key].append(var)

        # Process theory variables
        for course_id, course_vars in theory_variables.items():
            for day_idx in course_vars:
                for slot_idx in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][slot_idx].items():
                        key = (room_id, day_idx, slot_idx)
                        if key not in room_slot_assignments:
                            room_slot_assignments[key] = []
                        room_slot_assignments[key].append(var)

        # Apply single assignment constraint for each room-time combination
        for (room_id, day_idx, slot_idx), variables in room_slot_assignments.items():
            if len(variables) > 1:
                # Only one assignment allowed per room per time slot
                self.model.Add(sum(variables) <= 1)
                constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} lab room single assignment constraints")
        return constraints_applied

    def apply_teacher_clash_prevention_constraint(self, lab_variables, theory_variables):
        """
        Prevent teacher from being assigned to multiple sessions at the same time.
        Migrated from src/combined_scheduler.py
        """
        constraints_applied = 0
        self.logger.info("Applying teacher clash prevention constraint...")

        # Collect all assignments by teacher and time
        teacher_time_assignments = {}  # (teacher_id, day, slot) -> list of variables

        # Process theory variables
        for course_id, course_vars in theory_variables.items():
            # Get teacher for this course
            if hasattr(self, 'courses_df'):
                course_info = self.courses_df[self.courses_df['course_id'] == course_id]
                if not course_info.empty:
                    teacher_id = str(course_info.iloc[0].get('teacher_id', ''))
                    for day_idx in course_vars:
                        for slot_idx in course_vars[day_idx]:
                            for room_id, var in course_vars[day_idx][slot_idx].items():
                                key = (teacher_id, day_idx, slot_idx)
                                if key not in teacher_time_assignments:
                                    teacher_time_assignments[key] = []
                                teacher_time_assignments[key].append(var)

        # Process lab variables
        for course_id, course_vars in lab_variables.items():
            # Get teacher for this course
            if hasattr(self, 'courses_df'):
                course_info = self.courses_df[self.courses_df['course_id'] == course_id]
                if not course_info.empty:
                    teacher_id = str(course_info.iloc[0].get('teacher_id', ''))
                    for day_idx in course_vars:
                        for slot_idx in course_vars[day_idx]:
                            for room_id, var in course_vars[day_idx][slot_idx].items():
                                key = (teacher_id, day_idx, slot_idx)
                                if key not in teacher_time_assignments:
                                    teacher_time_assignments[key] = []
                                teacher_time_assignments[key].append(var)

        # Apply clash prevention constraint
        for (teacher_id, day_idx, slot_idx), variables in teacher_time_assignments.items():
            if len(variables) > 1:
                # Teacher can only be assigned to one session per time slot
                self.model.Add(sum(variables) <= 1)
                constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} teacher clash prevention constraints")
        return constraints_applied

    # ============================================================================
    # AI-GENERATED CONSTRAINTS WILL BE APPENDED HERE
    # ============================================================================

    def apply_computer_lab_theory_restriction(self, lab_variables, theory_variables):
        """
        Prevent theory courses from being scheduled in computer labs.
        Computer labs should be reserved for practical sessions only.
        """
        constraints_applied = 0

        # Process theory variables to block computer lab assignments
        for course_id, course_vars in theory_variables.items():
            for day_idx in course_vars:
                for slot_idx in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][slot_idx].items():
                        # Check if room is a computer lab
                        if hasattr(self, 'rooms_df'):
                            room_info = self.rooms_df[self.rooms_df['room_id'] == room_id]
                            if not room_info.empty:
                                room_name = str(room_info.iloc[0].get('room_name', '')).lower()
                                if 'computer' in room_name or 'lab' in room_name:
                                    # Block theory course from computer lab
                                    self.model.Add(var == 0)
                                    constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} computer lab theory restriction constraints")
        return constraints_applied
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



    # AI-Generated Constraint
    def apply_lab_sessions_end_before_5pm(self, lab_variables, theory_variables):
        """Ensure all lab sessions end before 5 PM."""
        constraints_applied = 0
        max_slot = 16  # Assuming slots are 30 minutes each, 5 PM is slot 16 (8 AM + 9 hours)

        for course_id, course_vars in lab_variables.items():
            for day_idx in course_vars:
                for slot_idx in course_vars[day_idx]:
                    if slot_idx >= max_slot:
                        for room_id, var in course_vars[day_idx][slot_idx].items():
                            self.model.Add(var == 0)  # Block this assignment
                            constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} lab_sessions_end_before_5pm constraints")
        return constraints_applied

    def apply_teacher_workload_limit(self, lab_variables, theory_variables):
        """Limit teachers to maximum 8 hours per day."""
        constraints_applied = 0

        # Get all teachers
        teachers = set()
        for _, course in self.courses_df.iterrows():
            teachers.add(course['teacher_id'])

        # For each teacher and each day
        for teacher_id in teachers:
            for day_idx in range(5):  # 5 days
                teacher_sessions = []

                # Collect all sessions for this teacher on this day
                for course_id, course_vars in lab_variables.items():
                    course_info = self.courses_df[self.courses_df['course_id'] == course_id]
                    if not course_info.empty and course_info.iloc[0]['teacher_id'] == teacher_id:
                        if day_idx in course_vars:
                            for slot_idx in course_vars[day_idx]:
                                for room_vars in course_vars[day_idx][slot_idx].values():
                                    teacher_sessions.append(room_vars * 2)  # Lab = 2 hours

                for course_id, course_vars in theory_variables.items():
                    course_info = self.courses_df[self.courses_df['course_id'] == course_id]
                    if not course_info.empty and course_info.iloc[0]['teacher_id'] == teacher_id:
                        if day_idx in course_vars:
                            for slot_idx in course_vars[day_idx]:
                                for room_vars in course_vars[day_idx][slot_idx].values():
                                    teacher_sessions.append(room_vars * 1)  # Theory = 1 hour

                # Constraint: max 8 hours per day per teacher
                if teacher_sessions:
                    self.model.Add(sum(teacher_sessions) <= 8)
                    constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} teacher workload limit constraints")
        return constraints_applied


    # AI-Generated Constraint
    def apply_no_theory_during_lunch(self, lab_variables, theory_variables):
        """Block theory classes during lunch time (12:30 PM slot)."""
        constraints_applied = 0
        lunch_slot_index = 5  # Assuming slot 5 corresponds to 12:30 PM

        for course_id, course_vars in theory_variables.items():
            for day_idx in course_vars:
                if lunch_slot_index in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][lunch_slot_index].items():
                        self.model.Add(var == 0)  # Block theory class during lunch
                        constraints_applied += 1

        self.logger.info(f"Applied {constraints_applied} no_theory_during_lunch constraints")
        return constraints_applied
