#!/usr/bin/env python3
"""
Constraint Code Generator

CrewAI agent that generates Python code for new constraints and appends them
to the existing constraints.py file based on natural language input.
"""

import os
import re
from crewai import Agent, Task, Crew, Process
from config.gemini_config import get_gemini_config

class ConstraintCodeGenerator:
    """
    CrewAI agent system that generates constraint code and appends it to constraints.py
    """

    def __init__(self):
        self.config = get_gemini_config()
        self.constraints_file = "/Users/danieldas/Documents/timetable-scheduler/agents/constraints.py"

    def create_code_generator_agent(self):
        """Create CrewAI agent that generates constraint code"""

        llm = self.config.get_general_purpose_llm()

        agent = Agent(
            role='Constraint Code Generator',
            goal='Generate Python code for timetable constraints based on natural language requirements',
            backstory="""You are an expert Python developer specializing in OR-Tools constraint programming
            and timetable scheduling. You write clean, efficient constraint code that integrates seamlessly
            with existing timetable scheduling systems. You understand how to use model.Add() statements
            and create proper constraint methods.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

        return agent

    def generate_constraint_code(self, user_constraint: str) -> str:
        """
        Generate Python code for a new constraint based on user input

        Args:
            user_constraint: Natural language constraint description

        Returns:
            str: Generated Python code for the constraint
        """

        print(f"🤖 Generating code for constraint: '{user_constraint}'")

        agent = self.create_code_generator_agent()

        # Read existing constraints.py to understand the current structure
        existing_code = self._read_existing_constraints()

        task = Task(
            description=f"""
            Generate Python code for a new constraint method based on this requirement:
            "{user_constraint}"

            EXISTING CONSTRAINTS.PY STRUCTURE:
            {existing_code[:2000]}...  # First 2000 chars for context

            CRITICAL REQUIREMENTS:
            1. Method signature MUST be: def apply_[descriptive_name](self, lab_variables, theory_variables)
            2. NO model parameter - use self.model.Add() instead of model.Add()
            3. Variables structure: lab_variables[course_id][day_idx][slot_idx][room_id] = BoolVar
            4. Variables structure: theory_variables[course_id][day_idx][slot_idx][room_id] = BoolVar
            5. Access course data via self.courses_df and room data via self.rooms_df
            6. Use proper iteration patterns shown below
            7. Always return constraints_applied count

            CORRECT VARIABLE ACCESS PATTERN:
            ```python
            for course_id, course_vars in theory_variables.items():
                for day_idx in course_vars:
                    for slot_idx in course_vars[day_idx]:
                        for room_id, var in course_vars[day_idx][slot_idx].items():
                            # var is a BoolVar - use: self.model.Add(var == 0)
            ```

            CORRECT METHOD TEMPLATE:
            ```python
            def apply_descriptive_constraint_name(self, lab_variables, theory_variables):
                \"\"\"Apply [constraint description]\"\"\"
                constraints_applied = 0

                # Example: Block theory courses from computer labs
                for course_id, course_vars in theory_variables.items():
                    for day_idx in course_vars:
                        for slot_idx in course_vars[day_idx]:
                            for room_id, var in course_vars[day_idx][slot_idx].items():
                                # Check if room is computer lab
                                room_info = self.rooms_df[self.rooms_df['room_id'] == room_id]
                                if not room_info.empty:
                                    room_name = room_info.iloc[0].get('room_name', '')
                                    if 'lab' in room_name.lower() or 'computer' in room_name.lower():
                                        self.model.Add(var == 0)  # Block this assignment
                                        constraints_applied += 1

                self.logger.info(f"Applied {{constraints_applied}} constraint_name constraints")
                return constraints_applied
            ```

            RETURN ONLY THE PYTHON CODE - NO EXPLANATIONS OR MARKDOWN.
            """,
            agent=agent,
            expected_output="Complete Python method code for the constraint"
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()
        return str(result)

    def _read_existing_constraints(self) -> str:
        """Read the current constraints.py file"""
        try:
            with open(self.constraints_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "# constraints.py file not found"

    def append_constraint_to_file(self, constraint_code: str, constraint_name: str) -> bool:
        """
        Append the generated constraint code to constraints.py

        Args:
            constraint_code: Generated Python code for the constraint
            constraint_name: Name/description of the constraint for logging

        Returns:
            bool: True if successfully appended
        """

        try:
            # Clean up the generated code
            cleaned_code = self._clean_generated_code(constraint_code)

            # Read existing file
            existing_content = self._read_existing_constraints()

            # Find the insertion point (before the last line or class end)
            insertion_point = self._find_insertion_point(existing_content)

            # Create the new content
            new_content = (
                existing_content[:insertion_point] +
                "\n    # AI-Generated Constraint\n" +
                cleaned_code + "\n\n" +
                existing_content[insertion_point:]
            )

            # Write back to file
            with open(self.constraints_file, 'w') as f:
                f.write(new_content)

            print(f"✅ Successfully appended constraint '{constraint_name}' to constraints.py")
            return True

        except Exception as e:
            print(f"❌ Error appending constraint to file: {e}")
            return False

    def _clean_generated_code(self, raw_code: str) -> str:
        """Clean up the generated code by removing markdown and formatting properly"""

        # Remove markdown code blocks
        code = re.sub(r'```python\n?', '', raw_code)
        code = re.sub(r'```\n?', '', code)

        # Remove any leading/trailing whitespace
        code = code.strip()

        # Ensure proper indentation (methods should be indented as class methods)
        lines = code.split('\n')
        indented_lines = []
        for line in lines:
            if line.strip():  # Non-empty line
                if not line.startswith('    '):  # Not already indented
                    indented_lines.append('    ' + line)
                else:
                    indented_lines.append(line)
            else:
                indented_lines.append(line)

        return '\n'.join(indented_lines)

    def _find_insertion_point(self, content: str) -> int:
        """Find the best place to insert new constraint code"""

        # Look for the end of the class (before any aliases or end of file)
        lines = content.split('\n')

        # Find the last method definition or the end of the class
        last_method_end = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('def ') and '    def ' in line:
                # Find the end of this method
                method_start = i
                j = i + 1
                while j < len(lines):
                    if (lines[j].strip() and
                        not lines[j].startswith('    ') and
                        not lines[j].startswith('\t')):
                        last_method_end = j
                        break
                    j += 1

        if last_method_end > 0:
            # Insert before the line that ends the last method
            return len('\n'.join(lines[:last_method_end]))
        else:
            # Insert at the end of the file
            return len(content)

    def process_user_constraint(self, user_constraint: str) -> bool:
        """
        Complete pipeline: generate code and append to constraints.py

        Args:
            user_constraint: Natural language constraint description

        Returns:
            bool: True if successful
        """

        print("🚀 Processing User Constraint")
        print(f"Input: {user_constraint}")

        # Step 1: Generate code
        print("\n📝 Step 1: Generating constraint code...")
        constraint_code = self.generate_constraint_code(user_constraint)

        if not constraint_code:
            print("❌ Failed to generate constraint code")
            return False

        print("✅ Constraint code generated")
        print("Generated code preview:")
        print("-" * 40)
        print(constraint_code[:300] + "..." if len(constraint_code) > 300 else constraint_code)

        # Step 2: Append to file
        print("\n📄 Step 2: Appending to constraints.py...")
        success = self.append_constraint_to_file(constraint_code, user_constraint)

        if success:
            print(f"\n🎯 SUCCESS: Constraint added to constraints.py!")
            print(f"   - New constraint method available")
            print(f"   - File updated with AI-generated code")
            print(f"   - Ready to use in timetable scheduling")

        return success


def main():
    """Demo the constraint code generation system"""

    generator = ConstraintCodeGenerator()

    # Example constraints to test
    test_constraints = [
        "Computer labs must be used only for practical sessions",
        "Teachers should not work more than 18 hours per week",
        "No classes during lunch time between 12-1 PM"
    ]

    print("🎯 Constraint Code Generator Demo")
    print("=" * 50)

    for i, constraint in enumerate(test_constraints, 1):
        print(f"\n{'='*60}")
        print(f"CONSTRAINT {i}")
        print(f"{'='*60}")

        success = generator.process_user_constraint(constraint)

        if success:
            print("✅ Constraint successfully added!")
        else:
            print("❌ Failed to add constraint!")

        if i < len(test_constraints):
            input("\nPress Enter to continue to next constraint...")


if __name__ == "__main__":
    main()