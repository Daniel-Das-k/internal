#!/usr/bin/env python3
"""
Flask API Server for Timetable Generation System
Provides endpoints for constraint parsing and timetable generation
"""

import os
import json
import base64

# Set matplotlib to use non-GUI backend for Flask server
import matplotlib
matplotlib.use('Agg')  # Must be set before importing pyplot

from flask import Flask, request, jsonify
from flask_cors import CORS
from main import parse_time_constraint, time_to_slot_index, parse_time_to_24h
from ai_scheduler import AIScheduler

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global state to store current constraint
current_constraint = None
current_prompt = ""

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Timetable API Server is running"
    })

@app.route('/api/process-prompt', methods=['POST'])
def process_prompt():
    """
    Endpoint 1: Receive prompt from client and generate constraint
    Returns success message after parsing the constraint
    """
    global current_constraint, current_prompt

    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({
                "error": "No prompt provided"
            }), 400

        # Store the prompt
        current_prompt = prompt

        # Parse time constraints dynamically
        time_constraint = parse_time_constraint(prompt)

        if time_constraint:
            start_time, end_time = time_constraint
            start_slot = time_to_slot_index(start_time)
            end_slot = time_to_slot_index(end_time)

            current_constraint = {
                "type": "time_block",
                "start_time": start_time,
                "end_time": end_time,
                "start_slot": start_slot,
                "end_slot": end_slot,
                "blocked_slots": (start_slot, end_slot)
            }

            response = {
                "success": True,
                "message": "Time block constraint generated successfully",
                "constraint": {
                    "type": "time_block",
                    "description": f"Block classes from {start_time:.1f}h to {end_time:.1f}h (slots {start_slot}-{end_slot})",
                    "start_time": f"{start_time:.1f}h",
                    "end_time": f"{end_time:.1f}h",
                    "blocked_slots": f"{start_slot}-{end_slot}"
                },
                "prompt": prompt
            }
        else:
            current_constraint = None
            response = {
                "success": True,
                "message": "General scheduling constraint generated successfully",
                "constraint": {
                    "type": "general",
                    "description": "No time restrictions - classes can be scheduled across all available time slots"
                },
                "prompt": prompt
            }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "error": f"Failed to process prompt: {str(e)}"
        }), 500

@app.route('/api/generate-timetable', methods=['POST'])
def generate_timetable():
    """
    Endpoint 2: Generate timetable and return with visualization
    Uses the previously parsed constraint to generate the schedule
    """
    global current_constraint, current_prompt

    try:
        if not current_prompt:
            return jsonify({
                "error": "No prompt processed yet. Please call /api/process-prompt first."
            }), 400

        # Create scheduler based on current constraint
        if current_constraint and current_constraint["type"] == "time_block":
            scheduler = AIScheduler(
                block_morning_slots=True,
                blocked_slots=current_constraint["blocked_slots"]
            )
            mode = f"BLOCKED_{current_constraint['start_slot']}_TO_{current_constraint['end_slot']}"
        else:
            scheduler = AIScheduler(block_morning_slots=False)
            mode = "GENERAL"

        # Generate timetable
        success = scheduler.generate_timetable()

        if not success:
            return jsonify({
                "error": "Failed to generate timetable - no feasible solution found"
            }), 500

        # Analyze the generated timetable
        analysis = analyze_timetable_results(scheduler.output_dir)

        # Get only the schedule overview image as base64 data
        schedule_overview_image = get_schedule_overview_image(scheduler.output_dir)

        # Prepare response with schedule overview image
        response = {
            "success": True,
            "message": "Timetable generated successfully",
            "prompt": current_prompt,
            "mode": mode,
            "constraint": current_constraint,
            "analysis": analysis,
            "output_directory": scheduler.output_dir,
            "schedule_overview": schedule_overview_image  # Include only schedule overview image
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "error": f"Failed to generate timetable: {str(e)}"
        }), 500

@app.route('/api/get-visualization/<path:filename>', methods=['GET'])
def get_visualization(filename):
    """
    Endpoint 3: Serve visualization files as base64 encoded images
    """
    try:
        # Construct full path to visualization file
        viz_path = os.path.join("output", filename)

        if not os.path.exists(viz_path):
            return jsonify({
                "error": "Visualization file not found"
            }), 404

        # Read and encode image as base64
        with open(viz_path, 'rb') as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

        return jsonify({
            "success": True,
            "filename": filename,
            "image_data": base64_image,
            "content_type": "image/png"
        })

    except Exception as e:
        return jsonify({
            "error": f"Failed to retrieve visualization: {str(e)}"
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset_session():
    """
    Endpoint 4: Reset current session (clear constraints and prompt)
    """
    global current_constraint, current_prompt

    current_constraint = None
    current_prompt = ""

    return jsonify({
        "success": True,
        "message": "Session reset successfully"
    })

def analyze_timetable_results(output_dir):
    """Analyze the generated timetable and return summary statistics"""
    theory_file = f"{output_dir}/ai_theory_schedule.json"

    analysis = {
        'total_sessions': 0,
        'morning_sessions': 0,  # slots 0-3 (8:00 AM - 12:00 PM)
        'afternoon_sessions': 0,  # slots 4+ (12:10 PM onwards)
        'time_slots_used': [],
        'slot_details': {}
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

def get_visualization_files(output_dir):
    """Get list of available visualization files"""
    viz_dir = os.path.join(output_dir, "visualizations")
    visualizations = {}

    if os.path.exists(viz_dir):
        for filename in os.listdir(viz_dir):
            if filename.endswith('.png'):
                # Create relative path for API access
                relative_path = f"{os.path.basename(output_dir)}/visualizations/{filename}"
                visualizations[filename.replace('.png', '')] = {
                    "filename": filename,
                    "path": relative_path,
                    "url": f"/api/get-visualization/{relative_path}"
                }

    return visualizations

def get_schedule_overview_image(output_dir):
    """Get only the combined_schedule_overview.png image as base64 data"""
    viz_dir = os.path.join(output_dir, "visualizations")

    if not os.path.exists(viz_dir):
        return None

    # Target the specific file we want
    target_file = "combined_schedule_overview.png"
    file_path = os.path.join(viz_dir, target_file)

    if os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
                return {
                    "filename": target_file,
                    "image_data": base64_image,
                    "content_type": "image/png"
                }
        except Exception as e:
            print(f"Error reading {target_file}: {e}")
            return None

    # If combined_schedule_overview.png doesn't exist, try combined_analysis.png as fallback
    fallback_file = "combined_analysis.png"
    fallback_path = os.path.join(viz_dir, fallback_file)

    if os.path.exists(fallback_path):
        try:
            with open(fallback_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
                return {
                    "filename": fallback_file,
                    "image_data": base64_image,
                    "content_type": "image/png"
                }
        except Exception as e:
            print(f"Error reading {fallback_file}: {e}")
            return None

    return None

if __name__ == '__main__':
    print("🚀 Starting Timetable API Server...")
    print("📡 Endpoints available:")
    print("   POST /api/process-prompt    - Process constraint prompt")
    print("   POST /api/generate-timetable - Generate timetable")
    print("   GET  /api/get-visualization/<path> - Get visualization image")
    print("   POST /api/reset             - Reset session")
    print("   GET  /api/health            - Health check")
    print()

    app.run(debug=True, host='0.0.0.0', port=5001)