from flask import Flask, render_template, request, jsonify, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("todolistdb1-firebase-adminsdk-ibeqp-f1298a2a1e.json")  # Use the path to your downloaded service account key
firebase_admin.initialize_app(cred)
# Initialize Firestore
db = firestore.client()

@app.route('/add_task', methods=['POST'])
def add_task():
    task = request.json.get('task')
    new_task_ref = db.collection('tasks').add({
        'task_name': task,
        'is_done': False
    })
    return jsonify({'message': 'Task added successfully', 'task_id': new_task_ref[1].id})

@app.route('/')
def index():
    tasks_ref = db.collection('tasks')
    tasks = [{**task.to_dict(), 'id': task.id} for task in tasks_ref.stream()]
    return render_template('index.html', tasks=tasks)

@app.route('/update_task/<task_id>', methods=['POST'])
def update_task(task_id):
    task_ref = db.collection('tasks').document(task_id)
    task = task_ref.get()
    if task.exists:
        is_done = task.to_dict().get('is_done')
        task_ref.update({'is_done': not is_done})
        return jsonify({'message': 'Task status updated successfully'})
    return jsonify({'error': 'Task not found'}), 404

@app.route('/delete_task/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    task_ref = db.collection('tasks').document(task_id)
    task_ref.delete()
    return jsonify({'message': 'Task deleted successfully'})

@app.route('/download_pdf')
def download_pdf():
    # Fetch tasks from Firebase Firestore
    tasks_ref = db.collection('tasks').stream()
    tasks = [{'task': task.to_dict()['task_name'], 'done': task.to_dict()['is_done']} for task in tasks_ref]
    # Create a PDF in memory
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "To-Do List")
    # Add tasks to the PDF with a strikethrough for completed tasks
    y_position = 720
    for task in tasks:
        task_name = task['task']
        status = "Done" if task['done'] else "Not Done"
        if status == "Done":
            # Draw the task name
            c.drawString(100, y_position, task_name)
            # Draw a line across the task name to indicate it's done
            text_width = c.stringWidth(task_name, "Helvetica", 12)
            c.line(100, y_position + 2, 100 + text_width, y_position + 2)  # Adjust y_position for strikethrough
        else:
            # Just draw the task name without a strikethrough
            c.drawString(100, y_position, task_name)
        y_position -= 20
    c.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, as_attachment=True, download_name="ToDoList.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)