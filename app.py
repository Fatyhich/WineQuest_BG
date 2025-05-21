import os
import uuid
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from celery.result import AsyncResult
from celery import states
from celery_worker import process_query_task, celery_app
from config import Config
import redis

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Initialize Redis client
redis_client = redis.Redis.from_url(Config.CELERY_RESULT_BACKEND)

@app.route('/', methods=['GET'])
def health_check():
    """
    Simple health check endpoint.
    """
    redis_health = True
    try:
        redis_client.ping()
    except:
        redis_health = False
    
    return jsonify({
        "status": "healthy",
        "redis_connected": redis_health
    })

@app.route('/api/process', methods=['POST'])
def process_image():
    """
    API endpoint to receive an image and text for processing.
    Returns a job_id that can be used to check the status.
    """
    # Check if request has the required data
    if 'audio' in request.files:
        audio = request.files['audio']
        questionnaire = None
    elif 'questionnaire' in request.form:
        questionnaire = request.form['questionnaire']
        audio = None
    else:
        return jsonify({"error": "Missing audio or questionnaire"}), 400
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Save the audio temporarily
    if audio is not None:
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{audio.filename}")
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        audio.save(audio_path)
    else:
        audio_path = None
    
    # Send the task to Celery workers
    task = process_query_task.apply_async(args=[job_id, audio_path, questionnaire], task_id=job_id)
    
    return jsonify({
        "job_id": job_id,
        "status": "processing"
    }), 202


@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    API endpoint to check the status of a processing job.
    """
    # Get task result from Celery
    task = AsyncResult(job_id, app=celery_app)
    
    # Check Redis directly for more reliable state information
    task_meta_key = f'celery-task-meta-{job_id}'
    redis_data = redis_client.get(task_meta_key)
    
    if redis_data:
        try:
            # Parse the Redis data for more accurate state information
            redis_result = json.loads(redis_data.decode('utf-8'))
            task_status = redis_result.get('status')
            task_result = redis_result.get('result')
            
            if task_status == 'SUCCESS':
                return jsonify({
                    'status': 'completed',
                    'result': task_result
                })
            elif task_status == 'FAILURE':
                return jsonify({
                    'status': 'failed',
                    'message': str(redis_result.get('traceback', 'Task failed'))
                })
        except (json.JSONDecodeError, AttributeError):
            # If we can't parse the Redis data, fall back to Celery's status
            pass
    
    # Fall back to Celery's status checking
    if task.state == states.SUCCESS:
        return jsonify({
            'status': 'completed',
            'result': task.result
        })
    elif task.state == states.FAILURE:
        return jsonify({
            'status': 'failed',
            'message': str(task.info) if task.info else 'Task failed'
        })
    elif task.state == states.PENDING:
        return jsonify({
            'status': 'pending',
            'message': 'Job is pending or does not exist'
        })
    elif task.state == states.STARTED or task.state == 'PROCESSING':
        return jsonify({
            'status': 'processing',
            'message': 'Job is processing',
            'progress': task.info if task.info else {}
        })
    else:
        # Any other state
        return jsonify({
            'status': 'processing',
            'message': f'Current state: {task.state}',
            'info': task.info if task.info else {}
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=Config.DEBUG)