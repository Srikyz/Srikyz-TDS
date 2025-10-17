"""
Task templates for evaluation system.

Each template has:
- id: Unique template identifier
- name: Human-readable name
- round1: Round 1 brief, attachments, checks
- round2: Round 2 brief (modifications), attachments, checks

Templates are parametrized with seed (email, YYYY-MM-DD-HH) for variation.

Author: Evaluation System
Date: 2025-10-16
"""

import hashlib
import random
from typing import Dict, List, Any
from datetime import datetime


class TaskTemplate:
    """Task template with round 1 and round 2 configurations."""
    
    def __init__(self, template_id: str, name: str, round1: Dict, round2: Dict):
        self.id = template_id
        self.name = name
        self.round1 = round1
        self.round2 = round2
    
    def generate(self, round: int, email: str, timestamp: str) -> Dict[str, Any]:
        """Generate parametrized task based on round, email, and timestamp."""
        # Parse timestamp to get seed
        seed = f"{email}-{timestamp}"
        random.seed(hashlib.md5(seed.encode()).hexdigest())
        
        config = self.round1 if round == 1 else self.round2
        
        # Parametrize brief
        brief = config['brief']
        if 'params' in config:
            for key, options in config['params'].items():
                value = random.choice(options)
                brief = brief.replace(f"{{{key}}}", str(value))
        
        return {
            'brief': brief,
            'attachments': config.get('attachments', []),
            'checks': config.get('checks', [])
        }


# Template definitions
TEMPLATES = {
    'image-viewer': TaskTemplate(
        template_id='image-viewer',
        name='Image Viewer',
        round1={
            'brief': '''Create a simple image viewer web application with the following features:
- Display {num_images} images in a grid layout
- Each image should be {size}px in size
- Clicking an image should show it in a modal/lightbox view
- Include next/previous buttons in the lightbox
- Use the provided image attachments
- Make it responsive and visually appealing
- Background color: {bg_color}''',
            'params': {
                'num_images': [3, 4, 5, 6],
                'size': [150, 200, 250],
                'bg_color': ['#f0f0f0', '#ffffff', '#e8e8e8', '#fafafa']
            },
            'attachments': [
                {'name': 'image1.jpg', 'type': 'image/jpeg', 'url': 'https://picsum.photos/400/300?random=1'},
                {'name': 'image2.jpg', 'type': 'image/jpeg', 'url': 'https://picsum.photos/400/300?random=2'},
                {'name': 'image3.jpg', 'type': 'image/jpeg', 'url': 'https://picsum.photos/400/300?random=3'},
                {'name': 'image4.jpg', 'type': 'image/jpeg', 'url': 'https://picsum.photos/400/300?random=4'}
            ],
            'checks': [
                {'type': 'element_exists', 'selector': 'img', 'min_count': 3},
                {'type': 'element_exists', 'selector': '.modal, .lightbox, [data-lightbox]'},
                {'type': 'click_interaction', 'selector': 'img', 'result': 'modal_opens'},
                {'type': 'element_exists', 'selector': 'button, .nav, .prev, .next'},
                {'type': 'responsive_check', 'breakpoints': [768, 1024]}
            ]
        },
        round2={
            'brief': '''Enhance your image viewer with these additional features:
- Add support for SVG images
- Implement zoom in/out functionality (buttons or mouse wheel)
- Add pan/drag capability when zoomed in
- Include a thumbnail strip at the bottom
- Add keyboard navigation (arrow keys)
- Add {animation_type} transition animations
- Include an image counter (e.g., "3 / 6")''',
            'params': {
                'animation_type': ['fade', 'slide', 'zoom', 'flip']
            },
            'attachments': [
                {'name': 'icon.svg', 'type': 'image/svg+xml', 'content': '<svg><circle cx="50" cy="50" r="40" fill="blue"/></svg>'}
            ],
            'checks': [
                {'type': 'element_exists', 'selector': 'svg, [src$=".svg"]'},
                {'type': 'element_exists', 'selector': '[class*="zoom"], button[title*="zoom"]', 'min_count': 2},
                {'type': 'element_exists', 'selector': '.thumbnails, [class*="thumb"]'},
                {'type': 'element_exists', 'selector': '.counter, [class*="count"]'},
                {'type': 'keyboard_event', 'key': 'ArrowRight', 'result': 'image_changes'},
                {'type': 'mouse_event', 'action': 'wheel', 'result': 'zoom_changes'},
                {'type': 'animation_check', 'selector': '.modal img'}
            ]
        }
    ),
    
    'calculator': TaskTemplate(
        template_id='calculator',
        name='Calculator',
        round1={
            'brief': '''Create a calculator web application with:
- Basic operations: addition, subtraction, multiplication, division
- Display showing {display_digits} digits
- Number buttons (0-9) and operation buttons
- Clear (C) and equals (=) buttons
- {layout} button layout
- Error handling for division by zero
- Visual feedback on button clicks''',
            'params': {
                'display_digits': [8, 10, 12],
                'layout': ['grid', 'vertical', 'compact']
            },
            'checks': [
                {'type': 'element_exists', 'selector': 'button', 'min_count': 15},
                {'type': 'element_exists', 'selector': 'input[type="text"], .display, #display'},
                {'type': 'click_sequence', 'buttons': ['5', '+', '3', '='], 'result': '8'},
                {'type': 'click_sequence', 'buttons': ['1', '0', '/', '2', '='], 'result': '5'},
                {'type': 'click_sequence', 'buttons': ['5', '/', '0', '='], 'result': 'Error|Infinity|NaN'},
                {'type': 'button_exists', 'text': ['C', 'Clear', 'AC']}
            ]
        },
        round2={
            'brief': '''Add advanced features to your calculator:
- Scientific functions: sin, cos, tan, sqrt, power
- Memory functions (M+, M-, MR, MC)
- Calculation history showing last {history_count} calculations
- Keyboard input support
- {feature} mode toggle
- Percentage calculation
- Parentheses support for complex expressions''',
            'params': {
                'history_count': [5, 10, 15],
                'feature': ['dark', 'scientific', 'programmer']
            },
            'checks': [
                {'type': 'element_exists', 'selector': 'button', 'min_count': 25},
                {'type': 'button_exists', 'text': ['sin', 'cos', 'tan', 'sqrt']},
                {'type': 'button_exists', 'text': ['M+', 'M-', 'MR', 'MC']},
                {'type': 'element_exists', 'selector': '.history, [class*="history"]'},
                {'type': 'keyboard_input', 'keys': '2*3', 'result': '6'},
                {'type': 'click_sequence', 'buttons': ['5', '0', '%'], 'result': '0.5|50'},
                {'type': 'parentheses_check', 'expression': '(2+3)*4', 'result': '20'}
            ]
        }
    ),
    
    'todo-list': TaskTemplate(
        template_id='todo-list',
        name='Todo List',
        round1={
            'brief': '''Create a todo list application with:
- Input field to add new tasks
- List displaying all tasks
- Checkbox to mark tasks as complete
- Delete button for each task
- Show {counter_type} counter
- {storage} storage to persist tasks
- Completed tasks should have {completed_style}
- Add button with visual feedback''',
            'params': {
                'counter_type': ['total', 'remaining', 'completed'],
                'storage': ['localStorage', 'sessionStorage'],
                'completed_style': ['strikethrough', 'gray color', 'different opacity']
            },
            'checks': [
                {'type': 'element_exists', 'selector': 'input[type="text"], input[type="search"]'},
                {'type': 'element_exists', 'selector': 'button, [type="submit"]'},
                {'type': 'element_exists', 'selector': 'ul, ol, .todo-list'},
                {'type': 'add_todo', 'text': 'Test Task', 'result': 'task_appears'},
                {'type': 'checkbox_toggle', 'result': 'style_changes'},
                {'type': 'delete_todo', 'result': 'task_removed'},
                {'type': 'storage_check', 'type': 'localStorage|sessionStorage'},
                {'type': 'element_exists', 'selector': '.counter, [class*="count"]'}
            ]
        },
        round2={
            'brief': '''Enhance your todo list with:
- Categories or tags for tasks (minimum {num_categories} categories)
- Filter buttons (All, Active, Completed)
- Edit functionality for existing tasks
- Due date picker for tasks
- Priority levels (High, Medium, Low) with color coding
- Search/filter functionality
- Drag and drop to reorder tasks
- Export to JSON functionality''',
            'params': {
                'num_categories': [3, 4, 5]
            },
            'checks': [
                {'type': 'element_exists', 'selector': 'select, [class*="category"], [class*="tag"]'},
                {'type': 'button_exists', 'text': ['All', 'Active', 'Completed']},
                {'type': 'filter_check', 'filter': 'Completed', 'result': 'shows_only_completed'},
                {'type': 'element_exists', 'selector': 'button[class*="edit"], .edit-btn'},
                {'type': 'element_exists', 'selector': 'input[type="date"], .date-picker'},
                {'type': 'element_exists', 'selector': '[class*="priority"], .high, .medium, .low'},
                {'type': 'search_functionality', 'query': 'test', 'result': 'filters_tasks'},
                {'type': 'drag_drop_check', 'result': 'order_changes'},
                {'type': 'export_check', 'format': 'json'}
            ]
        }
    ),
    
    'weather-dashboard': TaskTemplate(
        template_id='weather-dashboard',
        name='Weather Dashboard',
        round1={
            'brief': '''Create a weather dashboard with:
- Display current weather for {default_city}
- Show temperature in {temp_unit}
- Display weather condition icon/emoji
- Show humidity and wind speed
- {num_days}-day forecast
- Search box to change location
- Responsive card-based layout
- Use mock/sample data (no API required for now)''',
            'params': {
                'default_city': ['London', 'New York', 'Tokyo', 'Paris'],
                'temp_unit': ['Celsius', 'Fahrenheit'],
                'num_days': [3, 5, 7]
            },
            'checks': [
                {'type': 'element_exists', 'selector': '.temperature, [class*="temp"]'},
                {'type': 'element_exists', 'selector': '.humidity, [class*="humidity"]'},
                {'type': 'element_exists', 'selector': '.wind, [class*="wind"]'},
                {'type': 'element_exists', 'selector': 'img, .icon, .emoji'},
                {'type': 'element_exists', 'selector': '.forecast, [class*="forecast"]'},
                {'type': 'element_exists', 'selector': 'input[type="text"], input[type="search"]'},
                {'type': 'forecast_count', 'min_count': 3}
            ]
        },
        round2={
            'brief': '''Add these features to your weather dashboard:
- Hourly forecast (next {hourly_count} hours)
- Temperature chart/graph visualization
- Unit toggle (Celsius ↔ Fahrenheit)
- Save favorite locations (up to {fav_count} cities)
- Display sunrise and sunset times
- UV index indicator
- "Feels like" temperature
- Weather alerts section
- Auto-detect user location (with permission)''',
            'params': {
                'hourly_count': [12, 24],
                'fav_count': [3, 5]
            },
            'checks': [
                {'type': 'element_exists', 'selector': '.hourly, [class*="hourly"]'},
                {'type': 'chart_exists', 'type': 'line|bar|canvas'},
                {'type': 'toggle_exists', 'states': ['°C', '°F']},
                {'type': 'element_exists', 'selector': '.favorites, [class*="favorite"]'},
                {'type': 'element_exists', 'selector': '.sunrise, .sunset, [class*="sun"]'},
                {'type': 'element_exists', 'selector': '.uv, [class*="uv-index"]'},
                {'type': 'element_exists', 'selector': '.feels-like, [class*="feels"]'},
                {'type': 'geolocation_check', 'result': 'location_detected'}
            ]
        }
    ),
    
    'quiz-app': TaskTemplate(
        template_id='quiz-app',
        name='Quiz Application',
        round1={
            'brief': '''Create a quiz application with:
- {num_questions} multiple choice questions
- {choices_per_question} choices per question
- "Next" button to proceed through questions
- Display question number (e.g., "Question 3 of 10")
- Show final score at the end
- "Restart Quiz" button
- Visual feedback for selected answer
- {theme} color theme
- Questions provided in attachments''',
            'params': {
                'num_questions': [5, 10],
                'choices_per_question': [4],
                'theme': ['blue', 'green', 'purple', 'orange']
            },
            'attachments': [
                {
                    'name': 'questions.json',
                    'type': 'application/json',
                    'content': '''[
                        {"question": "What is 2+2?", "choices": ["3", "4", "5", "6"], "correct": 1},
                        {"question": "Capital of France?", "choices": ["London", "Berlin", "Paris", "Rome"], "correct": 2}
                    ]'''
                }
            ],
            'checks': [
                {'type': 'element_exists', 'selector': '.question, [class*="question"]'},
                {'type': 'element_exists', 'selector': 'input[type="radio"], button[class*="choice"]', 'min_count': 4},
                {'type': 'button_exists', 'text': ['Next', 'Continue']},
                {'type': 'element_exists', 'selector': '.progress, [class*="question-num"]'},
                {'type': 'quiz_flow', 'result': 'shows_score_at_end'},
                {'type': 'button_exists', 'text': ['Restart', 'Try Again']},
                {'type': 'selection_feedback', 'result': 'visual_change'}
            ]
        },
        round2={
            'brief': '''Enhance your quiz app with:
- Timer for each question ({time_limit} seconds)
- Progress bar showing completion percentage
- Score breakdown (correct/incorrect/skipped)
- Review mode showing all answers after completion
- Highlight correct/wrong answers with {correct_color} and {wrong_color}
- Category selection (minimum {num_categories} categories)
- Leaderboard with top {leaderboard_size} scores (localStorage)
- Sound effects for correct/wrong answers
- Difficulty levels (Easy, Medium, Hard)''',
            'params': {
                'time_limit': [30, 45, 60],
                'correct_color': ['green', 'lightgreen', '#00ff00'],
                'wrong_color': ['red', 'lightcoral', '#ff0000'],
                'num_categories': [3, 4],
                'leaderboard_size': [5, 10]
            },
            'checks': [
                {'type': 'element_exists', 'selector': '.timer, [class*="timer"]'},
                {'type': 'timer_countdown', 'result': 'time_decreases'},
                {'type': 'element_exists', 'selector': 'progress, .progress-bar'},
                {'type': 'element_exists', 'selector': '.score-breakdown, .statistics'},
                {'type': 'review_mode_check', 'result': 'shows_all_questions'},
                {'type': 'answer_highlighting', 'correct': 'green', 'wrong': 'red'},
                {'type': 'category_selection', 'min_categories': 3},
                {'type': 'element_exists', 'selector': '.leaderboard, [class*="leader"]'},
                {'type': 'difficulty_selection', 'levels': ['Easy', 'Medium', 'Hard']}
            ]
        }
    )
}


def get_template(template_id: str) -> TaskTemplate:
    """Get a template by ID."""
    return TEMPLATES.get(template_id)


def get_random_template(seed: str) -> TaskTemplate:
    """Get a random template based on seed."""
    random.seed(hashlib.md5(seed.encode()).hexdigest())
    return random.choice(list(TEMPLATES.values()))


def generate_task_id(template_id: str, brief: str, attachments: List[Dict]) -> str:
    """Generate task ID: {template_id}-{hash[:5]}."""
    content = f"{brief}{str(attachments)}"
    hash_value = hashlib.sha256(content.encode()).hexdigest()[:5]
    return f"{template_id}-{hash_value}"


if __name__ == "__main__":
    # Test templates
    import json
    
    print("Available Templates:")
    for template_id, template in TEMPLATES.items():
        print(f"\n{template_id}: {template.name}")
        
        # Generate Round 1
        task1 = template.generate(1, "test@example.com", "2025-10-16-12")
        print(f"  Round 1: {task1['brief'][:100]}...")
        print(f"  Checks: {len(task1['checks'])}")
        
        # Generate Round 2
        task2 = template.generate(2, "test@example.com", "2025-10-16-13")
        print(f"  Round 2: {task2['brief'][:100]}...")
        print(f"  Checks: {len(task2['checks'])}")
