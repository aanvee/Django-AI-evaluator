from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class FeedbackFormat(BaseModel):
    explanation: str = Field(description="A detailed string explaining the score.")
    strengths: str = Field(description="A single paragraph string highlighting key strengths. DO NOT return a list.")
    weaknesses: str = Field(description="A single paragraph string highlighting major weaknesses. DO NOT return a list.")
    suggestions: str = Field(description="A single paragraph string offering improvement suggestions. DO NOT return a list.")
    suggested_reading: List[str] = Field(description="A list of strings containing suggested reading topics.")

class FeedbackGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.DEEPSEEK_API_KEY,
            openai_api_base=settings.DEEPSEEK_BASE_URL,
            model_name="deepseek-chat",
            temperature=0.3
        )
        self.parser = JsonOutputParser(pydantic_object=FeedbackFormat)

    def get_system_prompt(self, similarity_score):
        # Module 5: Prompt Constraint Enforcement logic
        tone_instruction = ""
        if similarity_score < 0.3:
            tone_instruction = "CRITICAL: The student failed significantly. Be firm, highlight major gaps, and avoid any praise."
        elif similarity_score < 0.6:
            tone_instruction = "CAUTIONARY: The student has partial understanding. Be encouraging but very clear about what is missing."
        elif similarity_score < 0.85:
            tone_instruction = "POSITIVE: Good work. Provide minor corrections and suggestions for perfection."
        else:
            tone_instruction = "CELEBRATORY: Excellent work! Focus only on tiny stylistic or extra-depth points."

        return (
            "You are a 'Fair Educator' AI assessment assistant. Your job is to provide constructive, "
            "honest, and structured feedback in JSON format."
            f"\n\nTONE GUIDELINE: {tone_instruction}"
            "\n\nSTRICT GUIDELINES:"
            f"\n1. Your feedback MUST strictly reflect the similarity score of {similarity_score}/1.0."
            "\n2. Do NOT give high praise for low scores, and do NOT be overly harsh for high scores."
            "\n3. You MUST return a valid JSON object matching the schema below."
            "\n\nReturn only the JSON object."
        )

    def generate(self, question_text, model_answer, student_answer, score, raw_score):
        # Handle None inside logic instead of default parameters
        local_score = score if score is not None else 0.0
        local_raw_score = raw_score if raw_score is not None else local_score

        # Module 5: Prompt Constraint Enforcement (Tone based on thresholded score)
        system_prompt = self.get_system_prompt(local_score)
        
        user_prompt = (
            "Question: {question_text}"
            "\nModel Answer: {model_answer}"
            "\nStudent Answer: {student_answer}"
            "\n\nASSESSMENT DATA:"
            f"\n- Final Score: {local_score}/1.0"
            f"\n- Raw Similarity/Accuracy: {local_raw_score}/1.0"
            "\n\n{format_instructions}"
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt),
        ])

        try:
            # Module 4: Clean LCEL Pipeline
            chain = prompt_template | self.llm | self.parser
            
            return chain.invoke({
                "question_text": question_text,
                "model_answer": model_answer,
                "student_answer": student_answer,
                "format_instructions": self.parser.get_format_instructions()
            })
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return {
                "explanation": "Could not generate detailed feedback at this time.",
                "strengths": "N/A",
                "weaknesses": "Check similarity score for context.",
                "suggestions": "Try again later.",
                "suggested_reading": ["Review the core topic in your textbook."]
            }

# Wrapper for background task
def generate_feedback_task(submission_id):
    from evaluator.models import Submission
    try:
        submission = Submission.objects.get(id=submission_id)
        generator = FeedbackGenerator()
        
        # Ensure student_answer is always a string context
        student_answer = submission.student_answer if submission.student_answer is not None else ""
        if submission.selected_choice is not None:
             student_answer = submission.selected_choice.text
        
        # Explicit Null Handling for raw_score fallback at runtime
        final_score = submission.score if submission.score is not None else 0.0
        final_raw_score = submission.raw_score
        
        if final_raw_score is None:
            logger.warning(f"Submission {submission_id} has NULL raw_score. Falling back to score.")
            final_raw_score = final_score

        feedback = generator.generate(
            submission.question.text,
            submission.question.model_answer,
            student_answer,
            final_score,
            final_raw_score
        )
        submission.feedback = feedback
        submission.save()
    except Exception as e:
        logger.error(f"Failed background feedback generation for submission {submission_id}: {e}")