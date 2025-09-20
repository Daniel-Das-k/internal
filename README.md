# 🚀 AI Constraint Code Generator

**CrewAI agent that generates Python constraint code and appends it to constraints.py**

## 🎯 System Overview

This system allows users to add new timetable constraints using natural language. The CrewAI agent:

1. **Takes natural language input** (e.g., "Computer labs must be used only for practical sessions")
2. **Generates Python code** for the constraint using OR-Tools
3. **Appends the code** to the existing `constraints.py` file
4. **Makes the constraint available** for timetable optimization

## 📁 Files

- **`main.py`** - Main execution file (START HERE)
- **`constraint_code_generator.py`** - CrewAI agent that generates constraint code
- **`constraints.py`** - Base constraints file where AI appends new methods
- **`config/gemini_config.py`** - Gemini AI model configuration
- **`requirements.txt`** - Required Python packages
- **`demo.py`** - System demonstration

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
export GEMINI_API_KEY=your-gemini-api-key
```

### 3. Run the System
```bash
python main.py
```

### 4. Add Constraints
- Select option 1: "Add new constraint"
- Enter your constraint in natural language
- AI generates code and appends it to `constraints.py`

## 🔄 System Flow

```
User Input (Natural Language)
        ↓
"Computer labs must be used only for practical sessions"
        ↓
CrewAI Agent (constraint_code_generator.py)
        ↓
Generated Python Code:
def apply_computer_lab_restriction_constraint(self, model, lab_variables, theory_variables):
    # OR-Tools constraint implementation
    model.Add(constraint_conditions)
        ↓
Append to constraints.py
        ↓
New constraint method available for scheduling
```

## 📝 Example Usage

**Input:**
```
"Teachers should not work more than 18 hours per week"
```

**Generated Code:**
```python
def apply_teacher_workload_limit_constraint(self, model, lab_variables, theory_variables):
    """
    Apply teacher workload limit constraint.
    Teachers should not work more than 18 hours per week.
    """
    constraints_applied = 0

    for teacher in self.courses_df['teacher'].unique():
        # Collect all assignments for this teacher
        teacher_hours = []
        # ... implementation logic

        # Apply constraint: total hours <= 18
        model.Add(sum(teacher_hours) <= 18)
        constraints_applied += 1

    return constraints_applied
```

## 🎯 Key Features

- ✅ **Natural Language Input** - No technical syntax required
- ✅ **AI Code Generation** - CrewAI generates proper OR-Tools code
- ✅ **Dynamic File Updates** - Code automatically appended to constraints.py
- ✅ **Immediate Integration** - New constraints ready for use
- ✅ **Proper Structure** - Follows existing code patterns

## 🛠️ Technical Details

### Agent Configuration
- **Model**: Gemini 2.0 Flash (general purpose)
- **Role**: Constraint Code Generator
- **Task**: Convert natural language → Python OR-Tools code

### Code Generation
- Analyzes existing `constraints.py` structure
- Generates methods with proper signatures
- Includes docstrings and logging
- Uses `model.Add()` statements for OR-Tools
- Returns constraint count

### File Integration
- Finds proper insertion point in `constraints.py`
- Maintains code formatting and indentation
- Preserves existing methods
- Adds new methods as class methods

## 📊 Constraint Examples

| Natural Language | Generated Method |
|------------------|------------------|
| "Computer labs only for practicals" | `apply_computer_lab_restriction_constraint()` |
| "Teachers max 18 hours per week" | `apply_teacher_workload_limit_constraint()` |
| "No classes during lunch 12-1 PM" | `apply_lunch_break_constraint()` |
| "Math courses need 2-hour blocks" | `apply_math_course_block_constraint()` |

## 🔧 Integration with Scheduler

The generated constraints automatically integrate with the timetable scheduler:

```python
# In constraints.py
class TimetableConstraints:
    def apply_all_constraints(self, lab_variables, theory_variables):
        total_constraints = 0

        # Original constraints
        total_constraints += self.apply_basic_scheduling_constraints(...)

        # AI-generated constraints (automatically available)
        total_constraints += self.apply_computer_lab_restriction_constraint(...)
        total_constraints += self.apply_teacher_workload_limit_constraint(...)
        # ... more AI-generated methods

        return total_constraints
```

## 🎉 Result

Users can now add scheduling constraints by simply describing them in natural language. The AI generates the appropriate Python code and makes it immediately available for timetable optimization!

---

**Ready to start? Run `python main.py` and begin adding constraints!** 🚀