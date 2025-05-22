import os
import time
from celery import Celery, states
from celery.exceptions import Ignore
from config import Config
from weather_service import get_current_weather
from stt_service import STTService


# Initialize Celery
celery_app = Celery(
    'image_processor',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    worker_prefetch_multiplier=1,
    worker_concurrency=1,
    task_acks_late=True,
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
    result_expires=3600 * 24,  # Results expire after 24 hours
    worker_max_tasks_per_child=200,  # Restart workers after 200 tasks
)


def process_questionnaire(questionnaire: str) -> str:
    return "Hello, world!"


def prepare_query(user_text: str,
                  mode: str) -> str:
    return "Hello, world!"


def query_rag(query: str) -> str:
    time.sleep(4)
    return "Hello, world!"


@celery_app.task(bind=True, name='process_query_task')
def process_query_task(self, job_id, audio_path, questionnaire):
    """
    Process an audio and questionnaire.
    This is a stub function that simulates a long-running task.
    In a real implementation, this would call a VLM and LLM to process the data.
    """
    try:
        # Initialize STT service only when needed
        stt_service = STTService()
        
        # Mark the task as started
        self.update_state(state=states.STARTED, meta={'status': 'Task started'})
    
        n_steps = 2

        self.update_state(
                state='PROCESSING',
                meta={'current': 1, 
                      'total': n_steps, 
                      'status': f'Processing input (step 1/{n_steps})'}
            )
        if audio_path is not None:
            user_text = stt_service.transcribe(audio_path)
            mode = "audio"
        else:
            user_text = process_questionnaire(questionnaire)
            mode = "questionnaire"

        self.update_state(
                state='PROCESSING',
                meta={'current': 2, 
                      'total': n_steps, 
                      'status': f'Querying catalogue (step 2/{n_steps})'}
            )
        query = prepare_query(user_text, mode)
        rag_response = query_rag(query)
        
        # Simulate getting results from models
        result = {
            'job_id': job_id,
            "rag_response": rag_response
        }
        
        # In a real implementation, you might want to clean up the temporary image file
        if audio_path is not None:
            os.remove(audio_path)
        
        # The task will automatically transition to SUCCESS state when it returns
        return result
    
    except Exception as e:
        # If an exception occurs, mark the task as failed
        self.update_state(
            state=states.FAILURE,
            meta={'exc_type': type(e).__name__, 'exc_message': str(e)}
        )
        raise Ignore() 



# @celery_app.task(bind=True, name='process_image_task')
# def process_image_task(self, job_id, audio_path, questionnaire):
#     """
#     Process an audio and questionnaire.
#     This is a stub function that simulates a long-running task.
#     In a real implementation, this would call a VLM and LLM to process the data.
#     """
#     try:
#         # Mark the task as started
#         self.update_state(state=states.STARTED, meta={'status': 'Task started'})
        
#         # Fetch current weather for Moscow
#         weather_info = get_current_weather('Moscow')

#         # Compose weather summary text
#         weather_text = (
#             f"Current weather in Moscow: {weather_info['description']}, "
#             f"temp {weather_info['temperature']}°C (feels like {weather_info['feels_like']}°C), "
#             f"humidity {weather_info['humidity']}%, wind {weather_info['wind_speed']} m/s."
#         )

#         # Simulate a time-consuming task (e.g., running VLM and LLM models)
#         # This would be replaced with actual model inference in production
#         processing_time = 10  # seconds
#         for i in range(processing_time):
#             time.sleep(1)
#             # Update progress information
#             self.update_state(
#                 state='PROCESSING',
#                 meta={'current': i, 'total': processing_time, 'status': f'Processing step {i+1}/{processing_time}'}
#             )
        
#         # Simulate getting results from models
#         result = {
#             'job_id': job_id,
#             'image_processed': True,
#             'text_analyzed': True,
#             'text_input': text,
#             'image_path': image_path,
#             'weather': weather_info,
#             'mock_vlm_output': f"VLM analysis results for image {os.path.basename(image_path)}",
#             'mock_llm_output': f"LLM analysis results for text: '{text}'"
#         }
        
#         # In a real implementation, you might want to clean up the temporary image file
#         # os.remove(image_path)
        
#         # The task will automatically transition to SUCCESS state when it returns
#         return result
#     except Exception as e:
#         # If an exception occurs, mark the task as failed
#         self.update_state(
#             state=states.FAILURE,
#             meta={'exc_type': type(e).__name__, 'exc_message': str(e)}
#         )
#         raise Ignore() 
