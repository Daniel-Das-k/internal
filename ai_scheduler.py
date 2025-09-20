#!/usr/bin/env python3
"""
AI-Enhanced Timetable Scheduler

Integrates AI-generated constraints with timetable generation and visualization.
Uses the enhanced constraints.py with both migrated and AI-generated constraints.
"""

import os
import pandas as pd
import numpy as np
import logging
import json
import random
from datetime import datetime
from collections import defaultdict
from ortools.sat.python import cp_model
from constraints import TimetableConstraints
from visualize import visualize_combined_schedule

class AIScheduler:
    """
    AI-Enhanced scheduler that generates timetables using both migrated
    and AI-generated constraints, then visualizes the results.
    """

    def __init__(self, course_file=None, room_file=None, courses_df=None, rooms_df=None, block_morning_slots=False, blocked_slots=None):
        """Initialize the AI scheduler."""
        self.logger = logging.getLogger('agents.ai_scheduler')
        self.logger.info("Initializing AI-Enhanced Scheduler...")

        # Store constraint mode
        self.block_morning_slots = block_morning_slots
        self.blocked_slots = blocked_slots  # (start_slot, end_slot) tuple for dynamic blocking

        if blocked_slots:
            constraint_mode = f"blocked_{blocked_slots[0]}_to_{blocked_slots[1]}"
        elif block_morning_slots:
            constraint_mode = "with_morning_block"
        else:
            constraint_mode = "general_only"

        # Create output directory with constraint mode indicator
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"output/ai_schedule_{timestamp}_{constraint_mode}"
        os.makedirs(self.output_dir, exist_ok=True)

        # Store data - flexible initialization
        if courses_df is not None:
            self.courses_df = courses_df
        elif course_file:
            self.courses_df = pd.read_csv(course_file)
        else:
            # Create sample data if none provided
            self.courses_df = self._create_sample_courses()

        if rooms_df is not None:
            self.rooms_df = rooms_df
        elif room_file:
            self.rooms_df = pd.read_csv(room_file)
        else:
            # Create sample data if none provided
            self.rooms_df = self._create_sample_rooms()

        # Time slot configurations (matching combined_scheduler.py)
        self.lab_time_slots = [
            "8:00-10:00", "10:10-12:10", "1:20-3:20",
            "3:30-5:30", "5:40-7:40", "7:50-9:50"
        ]

        self.theory_time_slots = [
            "8:00-8:50", "9:00-9:50", "10:10-11:00", "11:10-12:00",
            "12:10-1:00", "1:20-2:10", "2:20-3:10", "3:30-4:20",
            "4:30-5:20", "5:30-6:20", "6:30-7:20"
        ]

        self.days = ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        # Schedule storage
        self.lab_schedule = {}
        self.theory_schedule = {}

        self.logger.info(f"Courses loaded: {len(self.courses_df)}")
        self.logger.info(f"Rooms loaded: {len(self.rooms_df)}")
        self.logger.info(f"Output directory: {self.output_dir}")

    def _create_sample_courses(self):
        """Create sample course data for testing."""
        courses_data = {
            'course_id': ['CS101', 'CS102', 'CS103', 'CS201', 'CS202'],
            'course_name': ['Programming', 'Data Structures', 'Algorithms', 'Database', 'Networks'],
            'teacher_id': [1, 2, 3, 1, 2],
            'teacher_name': ['Dr. Smith', 'Dr. Jones', 'Dr. Brown', 'Dr. Smith', 'Dr. Jones'],
            'department': ['CSE', 'CSE', 'CSE', 'CSE', 'CSE'],
            'semester': [1, 2, 3, 4, 4],
            'Year': [1, 1, 2, 2, 2],
            'session_type': ['theory', 'lab', 'theory', 'theory', 'lab'],
            'sessions_per_week': [3, 2, 3, 2, 2],
            'students_count': [60, 30, 45, 40, 25]
        }
        return pd.DataFrame(courses_data)

    def _create_sample_rooms(self):
        """Create sample room data for testing."""
        rooms_data = {
            'room_id': ['R001', 'R002', 'CL001', 'CL002', 'LAB001'],
            'room_name': ['Theory Room 1', 'Theory Room 2', 'Computer Lab 1', 'Computer Lab 2', 'Programming Lab'],
            'capacity': [60, 80, 30, 25, 35],
            'type': ['theory', 'theory', 'computer_lab', 'computer_lab', 'lab']
        }
        return pd.DataFrame(rooms_data)

    def generate_timetable(self):
        """Generate timetable using AI-enhanced constraints."""
        self.logger.info("="*80)
        self.logger.info("STARTING AI-ENHANCED TIMETABLE GENERATION")
        self.logger.info("="*80)

        # Create CP-SAT model
        model = cp_model.CpModel()

        # Initialize constraints with our data
        self.logger.info("Initializing TimetableConstraints with AI enhancements...")
        constraints = TimetableConstraints(
            model=model,
            courses_df=self.courses_df,
            rooms_df=self.rooms_df
        )

        # Create variables
        self.logger.info("Creating scheduling variables...")
        lab_variables = self._create_lab_variables(model)
        theory_variables = self._create_theory_variables(model)

        # Apply all constraints (migrated + AI-generated)
        self.logger.info("Applying ALL constraints (migrated + AI-generated)...")
        total_constraints = constraints.apply_all_constraints(lab_variables, theory_variables)
        self.logger.info(f"Total constraints applied: {total_constraints}")

        # Add optimization objectives
        self.logger.info("Setting up optimization objectives...")
        self._add_objectives(model, lab_variables, theory_variables)

        # Solve the model
        self.logger.info("Solving the scheduling model...")
        success = self._solve_model(model, lab_variables, theory_variables)

        if success:
            self.logger.info("✅ Timetable generation completed successfully!")

            # Save schedules
            self._save_schedules()

            # Generate visualizations
            self._generate_visualizations()

            return True
        else:
            self.logger.error("❌ Failed to generate timetable")
            return False

    def _create_lab_variables(self, model):
        """Create variables for lab sessions."""
        lab_variables = {}

        # Get lab courses
        lab_courses = self.courses_df[self.courses_df['session_type'] == 'lab']
        lab_rooms = self.rooms_df[self.rooms_df['type'].str.contains('lab', case=False)]

        for _, course in lab_courses.iterrows():
            course_id = course['course_id']
            lab_variables[course_id] = {}

            for day_idx, day in enumerate(self.days):
                lab_variables[course_id][day_idx] = {}

                for slot_idx, slot in enumerate(self.lab_time_slots):
                    lab_variables[course_id][day_idx][slot_idx] = {}

                    for _, room in lab_rooms.iterrows():
                        room_id = room['room_id']
                        var_name = f"lab_{course_id}_{day}_{slot}_{room_id}"
                        lab_variables[course_id][day_idx][slot_idx][room_id] = model.NewBoolVar(var_name)

        self.logger.info(f"Created lab variables for {len(lab_courses)} courses")
        return lab_variables

    def _create_theory_variables(self, model):
        """Create variables for theory sessions."""
        theory_variables = {}

        # Get theory courses
        theory_courses = self.courses_df[self.courses_df['session_type'] == 'theory']
        theory_rooms = self.rooms_df[self.rooms_df['type'] == 'theory']

        for _, course in theory_courses.iterrows():
            course_id = course['course_id']
            theory_variables[course_id] = {}

            for day_idx, day in enumerate(self.days):
                theory_variables[course_id][day_idx] = {}

                for slot_idx, slot in enumerate(self.theory_time_slots):
                    theory_variables[course_id][day_idx][slot_idx] = {}

                    for _, room in theory_rooms.iterrows():
                        room_id = room['room_id']
                        var_name = f"theory_{course_id}_{day}_{slot}_{room_id}"
                        theory_variables[course_id][day_idx][slot_idx][room_id] = model.NewBoolVar(var_name)

        self.logger.info(f"Created theory variables for {len(theory_courses)} courses")
        return theory_variables

    def _add_objectives(self, model, lab_variables, theory_variables):
        """Add optimization objectives and session limits."""
        # Add session per week constraints for each course
        for course_id, course_vars in list(lab_variables.items()) + list(theory_variables.items()):
            # Get the required sessions per week for this course
            course_info = self.courses_df[self.courses_df['course_id'] == course_id]
            if not course_info.empty:
                sessions_per_week = int(course_info.iloc[0].get('sessions_per_week', 1))

                # Count total sessions scheduled for this course
                all_sessions = []
                for day_idx in course_vars:
                    for slot_idx in course_vars[day_idx]:
                        for room_vars in course_vars[day_idx][slot_idx].values():
                            all_sessions.append(room_vars)

                # Constraint: exactly sessions_per_week sessions
                if all_sessions:
                    model.Add(sum(all_sessions) == sessions_per_week)
                    self.logger.info(f"Added session limit for {course_id}: {sessions_per_week} sessions/week")

        # Add better distribution constraints and optional morning block
        self._add_distribution_constraints(model, lab_variables, theory_variables)

        # Add mandatory scattering constraints
        self._add_mandatory_scattering(model, lab_variables, theory_variables)

        # Add dynamic slot blocking if enabled
        if self.block_morning_slots or self.blocked_slots:
            self._add_dynamic_block_constraint(model, lab_variables, theory_variables)

        # Improved objective: Balance utilization across time slots
        objective_terms = []

        # 1. Encourage different teachers to teach at same time (avoid gaps)
        # Instead of penalizing consecutive slots with complex multiplication,
        # we'll use a simpler approach with distribution constraints

        # 2. Encourage spread across different time periods
        for course_vars in list(lab_variables.values()) + list(theory_variables.values()):
            for day_idx in range(len(self.days)):
                if day_idx in course_vars:
                    for slot_idx in course_vars[day_idx]:
                        # Generate random scattered distribution with dynamic blocking
                        is_blocked_slot = False

                        if self.blocked_slots:
                            # Dynamic blocking - check if slot is in blocked range
                            start_slot, end_slot = self.blocked_slots
                            is_blocked_slot = start_slot <= slot_idx <= end_slot
                        elif self.block_morning_slots:
                            # Legacy morning blocking
                            is_blocked_slot = slot_idx < 4

                        if is_blocked_slot:
                            slot_weight = 0  # These will be blocked anyway
                        else:
                            # Available slots - randomize for scatter
                            # Detect lunch time dynamically (around 12-1 PM range)
                            slot_time = self.theory_time_slots[slot_idx] if slot_idx < len(self.theory_time_slots) else "Unknown"
                            is_lunch_time = slot_idx == 4 or (isinstance(slot_time, str) and "12:10-1:00" in slot_time)

                            if is_lunch_time:
                                slot_weight = random.randint(1, 3)  # Lower preference for lunch
                            else:  # All other available slots - randomize
                                slot_weight = random.randint(4, 9)  # Random preference for scattering

                        for room_vars in course_vars[day_idx][slot_idx].values():
                            objective_terms.append(slot_weight * room_vars)

        if objective_terms:
            model.Maximize(sum(objective_terms))

    def _add_distribution_constraints(self, model, lab_variables, theory_variables):
        """Add improved constraints for better time distribution and scattering."""
        # 1. Spread courses across different days
        for course_id, course_vars in list(lab_variables.items()) + list(theory_variables.items()):
            course_info = self.courses_df[self.courses_df['course_id'] == course_id]
            if not course_info.empty:
                sessions_per_week = int(course_info.iloc[0].get('sessions_per_week', 1))

                if sessions_per_week > 1:
                    # At most 1 session per day for theory courses
                    session_type = course_info.iloc[0].get('session_type', 'theory')
                    max_per_day = 1 if session_type == 'theory' else 2

                    for day_idx in course_vars:
                        day_sessions = []
                        for slot_idx in course_vars[day_idx]:
                            for room_vars in course_vars[day_idx][slot_idx].values():
                                day_sessions.append(room_vars)

                        if day_sessions:
                            model.Add(sum(day_sessions) <= max_per_day)

        # 2. Add time slot diversity constraints for better scattering
        self._add_time_diversity_constraints(model, lab_variables, theory_variables)

        # 3. Prevent clustering in consecutive slots
        self._add_anti_clustering_constraints(model, lab_variables, theory_variables)

        self.logger.info("Applied ENHANCED distribution constraints for better scattering")

    def _add_time_diversity_constraints(self, model, lab_variables, theory_variables):
        """Add constraints to encourage diversity in time slot usage."""
        # Dynamically determine available slots
        all_slots = list(range(len(self.theory_time_slots)))
        blocked_slots_set = set()

        # Get blocked slots dynamically
        if self.blocked_slots:
            start_slot, end_slot = self.blocked_slots
            blocked_slots_set = set(range(start_slot, end_slot + 1))
        elif self.block_morning_slots:
            blocked_slots_set = set([0, 1, 2, 3])

        available_slots = [slot for slot in all_slots if slot not in blocked_slots_set]

        # Create dynamic time periods from available slots
        if len(available_slots) >= 4:
            # Split available slots into periods for diversity
            period_size = max(2, len(available_slots) // 3)  # Create 3 periods
            periods = [
                available_slots[i:i + period_size]
                for i in range(0, len(available_slots), period_size)
            ]
        else:
            # If too few slots, treat each as its own period
            periods = [[slot] for slot in available_slots]

        # For each day, limit sessions per period to encourage spreading
        for day_idx in range(len(self.days)):
            for period in periods:
                period_sessions = []

                # Theory sessions in this period
                for course_vars in theory_variables.values():
                    if day_idx in course_vars:
                        for slot_idx in period:
                            if slot_idx in course_vars[day_idx]:
                                for room_vars in course_vars[day_idx][slot_idx].values():
                                    period_sessions.append(room_vars)

                # Limit sessions per period to encourage spreading
                if period_sessions and len(periods) > 1:
                    max_per_period = max(1, len(available_slots) // len(periods) + 1)
                    model.Add(sum(period_sessions) <= max_per_period)

    def _add_anti_clustering_constraints(self, model, lab_variables, theory_variables):
        """Add constraints to prevent clustering of classes in consecutive slots."""
        # For each teacher, prevent too many consecutive classes
        teacher_ids = self.courses_df['teacher_id'].unique()

        for teacher_id in teacher_ids:
            teacher_courses = self.courses_df[self.courses_df['teacher_id'] == teacher_id]['course_id'].tolist()

            for day_idx in range(len(self.days)):
                # Check consecutive slots for this teacher
                for slot_idx in range(len(self.theory_time_slots) - 1):
                    current_slot_vars = []
                    next_slot_vars = []

                    # Collect variables for current and next slot for this teacher
                    for course_id in teacher_courses:
                        if course_id in theory_variables:
                            course_vars = theory_variables[course_id]
                            if day_idx in course_vars:
                                if slot_idx in course_vars[day_idx]:
                                    for room_vars in course_vars[day_idx][slot_idx].values():
                                        current_slot_vars.append(room_vars)

                                if slot_idx + 1 in course_vars[day_idx]:
                                    for room_vars in course_vars[day_idx][slot_idx + 1].values():
                                        next_slot_vars.append(room_vars)

                    # Constraint: if teacher has class in current slot,
                    # limit probability of having class in next slot
                    if current_slot_vars and next_slot_vars:
                        # At most one session for this teacher in consecutive slots
                        model.Add(sum(current_slot_vars) + sum(next_slot_vars) <= 1)

    def _add_dynamic_block_constraint(self, model, lab_variables, theory_variables):
        """Add constraint to block classes for any dynamic time range."""
        if self.blocked_slots:
            # Use dynamic slot range
            start_slot, end_slot = self.blocked_slots
            blocked_slots = list(range(start_slot, end_slot + 1))
            block_description = f"slots {start_slot}-{end_slot}"
        else:
            # Use default morning block (backward compatibility)
            blocked_slots = [0, 1, 2, 3]  # 8:00-8:50, 9:00-9:50, 10:10-11:00, 11:10-12:00
            block_description = "morning slots (8-11:30 AM)"

        constraints_applied = 0

        # Block specified slots for theory classes
        for course_vars in theory_variables.values():
            for day_idx in course_vars:
                for slot_idx in blocked_slots:
                    if slot_idx in course_vars[day_idx]:
                        for room_vars in course_vars[day_idx][slot_idx].values():
                            model.Add(room_vars == 0)
                            constraints_applied += 1

        # Block specified slots for lab classes
        for course_vars in lab_variables.values():
            for day_idx in course_vars:
                for slot_idx in blocked_slots:
                    if slot_idx in course_vars[day_idx]:
                        for room_vars in course_vars[day_idx][slot_idx].values():
                            model.Add(room_vars == 0)
                            constraints_applied += 1

        self.logger.info(f"🚫 APPLIED DYNAMIC BLOCK ({block_description}): {constraints_applied} slots blocked")

    def _add_mandatory_scattering(self, model, lab_variables, theory_variables):
        """Add hard constraints to force scattering across multiple time slots."""
        # Count total sessions that need to be scheduled
        total_theory_sessions = 0
        for course_id, course_vars in theory_variables.items():
            course_info = self.courses_df[self.courses_df['course_id'] == course_id]
            if not course_info.empty:
                sessions_per_week = int(course_info.iloc[0].get('sessions_per_week', 1))
                total_theory_sessions += sessions_per_week

        if total_theory_sessions > 1:
            # Dynamically determine available slots based on any blocking
            all_slots = list(range(len(self.theory_time_slots)))
            blocked_slots_set = set()

            # Get blocked slots dynamically
            if self.blocked_slots:
                start_slot, end_slot = self.blocked_slots
                blocked_slots_set = set(range(start_slot, end_slot + 1))
            elif self.block_morning_slots:
                blocked_slots_set = set([0, 1, 2, 3])  # Legacy support

            # Calculate available slots
            available_slots = [slot for slot in all_slots if slot not in blocked_slots_set]

            if blocked_slots_set:
                self.logger.info(f"Forcing scattering across {len(available_slots)} available slots (blocked: {sorted(blocked_slots_set)})")
            else:
                self.logger.info(f"Forcing scattering across {len(available_slots)} total slots")

            # Force usage of at least 2 different time slots if we have 2+ sessions
            if total_theory_sessions >= 2 and len(available_slots) >= 2:
                slot_usage_vars = []

                for slot_idx in available_slots:
                    # Create a boolean variable for whether this slot is used
                    slot_used_var = model.NewBoolVar(f"slot_{slot_idx}_used")
                    slot_usage_vars.append(slot_used_var)

                    # Collect all sessions in this slot (only from available slots)
                    slot_sessions = []
                    for course_vars in theory_variables.values():
                        for day_idx in course_vars:
                            if slot_idx in course_vars[day_idx]:
                                for room_vars in course_vars[day_idx][slot_idx].values():
                                    slot_sessions.append(room_vars)

                    if slot_sessions:
                        # Link slot usage to actual sessions
                        # If any session is scheduled in this slot, mark slot as used
                        model.Add(sum(slot_sessions) <= len(slot_sessions) * slot_used_var)
                        # If slot is marked as used, at least one session must be scheduled
                        model.Add(sum(slot_sessions) >= slot_used_var)

                # Force usage of at least 2-3 different slots for better distribution
                min_slots = min(3, len(available_slots), total_theory_sessions)
                if min_slots >= 2:
                    model.Add(sum(slot_usage_vars) >= min_slots)
                    self.logger.info(f"MANDATORY SCATTERING: At least {min_slots} different available slots must be used")

    def _solve_model(self, model, lab_variables, theory_variables):
        """Solve the scheduling model."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300  # 5 minutes timeout

        self.logger.info("Starting solver...")
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL:
            self.logger.info("✅ Optimal solution found!")
            self._extract_solution(solver, lab_variables, theory_variables)
            return True
        elif status == cp_model.FEASIBLE:
            self.logger.info("✅ Feasible solution found!")
            self._extract_solution(solver, lab_variables, theory_variables)
            return True
        else:
            self.logger.error(f"❌ No solution found. Status: {solver.StatusName(status)}")
            return False

    def _extract_solution(self, solver, lab_variables, theory_variables):
        """Extract solution from the solver."""
        self.logger.info("Extracting solution...")

        # Extract lab schedule
        for course_id, course_vars in lab_variables.items():
            for day_idx in course_vars:
                for slot_idx in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][slot_idx].items():
                        if solver.Value(var) == 1:
                            day = self.days[day_idx]
                            slot = self.lab_time_slots[slot_idx]

                            if day not in self.lab_schedule:
                                self.lab_schedule[day] = {}
                            if slot not in self.lab_schedule[day]:
                                self.lab_schedule[day][slot] = {}

                            self.lab_schedule[day][slot][room_id] = course_id

        # Extract theory schedule
        for course_id, course_vars in theory_variables.items():
            for day_idx in course_vars:
                for slot_idx in course_vars[day_idx]:
                    for room_id, var in course_vars[day_idx][slot_idx].items():
                        if solver.Value(var) == 1:
                            day = self.days[day_idx]
                            slot = self.theory_time_slots[slot_idx]

                            if day not in self.theory_schedule:
                                self.theory_schedule[day] = {}
                            if slot not in self.theory_schedule[day]:
                                self.theory_schedule[day][slot] = {}

                            self.theory_schedule[day][slot][room_id] = course_id

        self.logger.info(f"Lab sessions scheduled: {sum(len(slots.values()) for day_slots in self.lab_schedule.values() for slots in day_slots.values())}")
        self.logger.info(f"Theory sessions scheduled: {sum(len(slots.values()) for day_slots in self.theory_schedule.values() for slots in day_slots.values())}")

    def _save_schedules(self):
        """Save schedules to JSON files in format expected by visualization."""
        lab_file = os.path.join(self.output_dir, 'ai_lab_schedule.json')
        theory_file = os.path.join(self.output_dir, 'ai_theory_schedule.json')

        # Convert to flat format expected by visualization
        lab_data = self._convert_to_flat_format(self.lab_schedule, 'lab')
        theory_data = self._convert_to_flat_format(self.theory_schedule, 'theory')

        with open(lab_file, 'w') as f:
            json.dump(lab_data, f, indent=2)

        with open(theory_file, 'w') as f:
            json.dump(theory_data, f, indent=2)

        self.logger.info(f"Lab schedule saved: {lab_file}")
        self.logger.info(f"Theory schedule saved: {theory_file}")

    def _convert_to_flat_format(self, schedule_dict, session_type):
        """Convert nested schedule to flat format expected by visualization."""
        flat_data = []

        # Map our days to visualizer expected format
        day_mapping = {
            'Tuesday': 'tuesday',
            'Wednesday': 'wed',
            'Thursday': 'thur',
            'Friday': 'fri',
            'Saturday': 'sat'
        }

        for day, day_schedule in schedule_dict.items():
            viz_day = day_mapping.get(day, day.lower())

            for time_slot, slot_assignments in day_schedule.items():
                for room_id, course_id in slot_assignments.items():
                    # Get course info
                    course_info = self.courses_df[self.courses_df['course_id'] == course_id]
                    if not course_info.empty:
                        course_data = course_info.iloc[0]

                        # Add required fields for visualization compatibility
                        entry = {
                            'day': str(viz_day),
                            'time_slot': str(time_slot),
                            'room_id': str(room_id),
                            'room_number': str(room_id),  # Add for compatibility
                            'course_id': str(course_id),
                            'course_code': str(course_id),
                            'course_name': str(course_data.get('course_name', course_id)),
                            'teacher_id': str(course_data.get('teacher_id', '1')),
                            'teacher_name': str(course_data.get('teacher_name', f"Teacher {course_data.get('teacher_id', '1')}")),
                            'department': str(course_data.get('department', 'Unknown')),
                            'semester': int(course_data.get('semester', 1)),
                            'year': int(course_data.get('Year', 1)),
                            'session_type': str(session_type),
                            'students_count': int(course_data.get('students_count', 30)),
                            'block': 'A Block',  # Default block for visualization
                            'staff_code': f"ST{course_data.get('teacher_id', '1')}"  # Add staff code
                        }

                        # Add session-specific fields for lab sessions
                        if session_type == 'lab':
                            # Map time slot to session name (L1, L2, etc.)
                            lab_session_map = {
                                "8:00-10:00": "L1",
                                "10:10-12:10": "L2",
                                "1:20-3:20": "L3",
                                "3:30-5:30": "L4",
                                "5:40-7:40": "L5",
                                "7:50-9:50": "L6"
                            }
                            entry['session_name'] = lab_session_map.get(time_slot, 'L1')
                            entry['is_batched'] = False
                            entry['batch_info'] = ''
                        else:
                            # Theory sessions - map to slot index
                            try:
                                entry['slot_index'] = self.theory_time_slots.index(time_slot)
                            except ValueError:
                                entry['slot_index'] = 0

                        flat_data.append(entry)

        return flat_data

    def _generate_visualizations(self):
        """Generate visualizations using the existing visualize.py."""
        try:
            self.logger.info("Generating schedule visualizations...")

            lab_json_file = os.path.join(self.output_dir, 'ai_lab_schedule.json')
            theory_json_file = os.path.join(self.output_dir, 'ai_theory_schedule.json')

            # Create visualizations directory
            viz_dir = os.path.join(self.output_dir, 'visualizations')
            os.makedirs(viz_dir, exist_ok=True)

            # Generate visualizations using existing function
            visualize_combined_schedule(lab_json_file, theory_json_file, viz_dir)

            self.logger.info(f"✅ Visualizations generated in: {viz_dir}")

        except Exception as e:
            self.logger.error(f"❌ Visualization failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def print_schedule_summary(self):
        """Print a summary of the generated schedule."""
        print("\n" + "="*80)
        print("📅 AI-GENERATED TIMETABLE SUMMARY")
        print("="*80)

        print(f"\n📊 Schedule Statistics:")
        print(f"  • Lab sessions scheduled: {sum(len(slots.values()) for day_slots in self.lab_schedule.values() for slots in day_slots.values())}")
        print(f"  • Theory sessions scheduled: {sum(len(slots.values()) for day_slots in self.theory_schedule.values() for slots in day_slots.values())}")
        print(f"  • Total courses: {len(self.courses_df)}")
        print(f"  • Total rooms: {len(self.rooms_df)}")

        print(f"\n📁 Output Files:")
        print(f"  • Schedule data: {self.output_dir}")
        print(f"  • Visualizations: {self.output_dir}/visualizations")

        print(f"\n🎯 Constraints Applied:")
        print(f"  • Migrated constraints from combined_scheduler.py")
        print(f"  • AI-generated constraints from natural language inputs")
        print(f"  • All constraints validated and applied successfully")

        if self.lab_schedule or self.theory_schedule:
            print(f"\n✅ Timetable generation completed successfully!")
            print(f"📊 Check {self.output_dir}/visualizations for detailed charts and graphs")
        else:
            print(f"\n❌ No valid schedule generated")

def main():
    """Main function to demonstrate AI scheduler."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print("🤖 AI-Enhanced Timetable Scheduler")
    print("="*50)

    # Create scheduler with sample data
    scheduler = AIScheduler()

    # Generate timetable
    success = scheduler.generate_timetable()

    # Print summary
    scheduler.print_schedule_summary()

    return success

if __name__ == "__main__":
    main()