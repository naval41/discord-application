import json
import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.bedrock_service import BedrockService

class BedrockProcessor:
    def __init__(self):
        self.bedrock_service = BedrockService()

    def _get_company_tools(self):
        return [
            {
                "toolSpec": {
                    "name": "company_extraction",
                    "description": "Extract the company name from the interview experience.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "is_interview_experience": {
                                    "type": "boolean",
                                    "description": "True if this is an interview experience, False if general discussion."
                                },
                                "company_name": {
                                    "type": "string",
                                    "description": "Name of the company."
                                }
                            },
                            "required": ["is_interview_experience"]
                        }
                    }
                }
            }
        ]

    def _get_interview_tools(self):
        return [
        {
            "toolSpec": {
                "name": "interview_experience_extraction",
                "description": "Interview Experience Extraction",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "For which location this interview is for"
                            },
                             "job_role_id": {
                                "type": "string",
                                "description": "ID of the specific Internal Job Role this interview best matches."
                            },
                            "number_of_rounds": {
                                "type": "integer",
                                "description": "number of interview rounds"
                            },
                            "offer_status": {
                                "type": "string",
                                "description": "Status of the offer",
                                "enum": ["Offer", "Pending", "Rejected", "Unknown"]
                            },
                            "preparation_source": {
                                "type": "string",
                                "description": "Interview preparation source which can be helpful for others to prepare for dont summarize yourself, kept description from the interview intact. This can also be advise for others around how to prepare for interview. Incase if its not present return empty. Dont return <UNKNOWN>"
                            },
                            "company_interview_process": {
                                "type": "string",
                                "description": "Describe process of taking interview at the company, generally it evolves around how company starts approaching candidate till they share result. Please dont summarize this. Also dont write it as third person, instead it should shown as candidate experience. Incase if its not present return empty. Dont return <UNKNOWN>"
                            },
                            "interview_difficulty": {
                                "type": "string",
                                "description": "Overall difficulty",
                                "enum": ["Easy", "Medium", "Hard"]
                            },
                            "overall_rating": {
                                "type": "number",
                                "description": "Rating out of 5"
                            },
                            "confidence_score": {
                                "type": "integer",
                                "description": "Confidence score 0-100 indicating the quality and completeness of this interview experience."
                            },
                            "confidence_reasoning": {
                                "type": "string",
                                "description": "Reasoning for the given confidence score."
                            },
                            "is_anonymous": {
                                "type": "boolean",
                                "description": "Is user anonymous"
                            },
                            "interview_rounds": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "sequence": {
                                            "type": "integer",
                                            "description": "interview round sequence as per candidate experience, this is mainly integer value which gives order and mostly starts with 1 and goes on"
                                        },
                                        "name": {
                                            "type": "string",
                                           "description": "interview round title as per candidate experience"
                                        },
                                         "duration": {
                                            "type": "string",
                                            "description": "Duration"
                                        },
                                        "experience": {
                                            "type": "string",
                                             "description": "Interview round experience as per candidate dont optimize this, keep as is what is present in Input. Incase if its not present return empty. Dont return <UNKNOWN>"
                                        },
                                        "difficulty": {
                                            "type": "string",
                                            "enum": ["Easy", "Medium", "Hard"]
                                        },
                                        "key_takeaways": {
                                            "type": "string", 
                                            "description": "key takeaways from the interview round as per candidate experience"
                                        }
                                    },
                                    "required": ["sequence", "name", "experience", "difficulty"]
                                }
                            }
                        },
                        "required": [
                           "job_role_id",
                           "confidence_score"
                        ]
                    }
                }
            }
        }
    ]

    def extract_company_info(self, title, summary):
        content_text = f"Title: {title}\nSummary: {summary}"
        prompt = """
        Determine if this is an interview experience. 
        Interview experience is a post where candidate shares their interview experience. 
        This experiences are shared in the form of Title and Summary. And having company name in the title.
        This experiences genenrally contains duration, number of rounds, job role, company name, 
        If so, extract the Company Name.
        """
        
        try:
            response = self.bedrock_service.converse(
                messages=[{"role": "user", "content": [{"text": content_text}, {"text": prompt}]}],
                inference_config={"maxTokens": 1024, "temperature": 0},
                tool_config={
                    "tools": self._get_company_tools(),
                    "toolChoice": {"tool": {"name": "company_extraction"}}
                }
            )

            return self.bedrock_service.extract_tool_result(response)
        except Exception as e:
            print(f"Bedrock Company Extraction Error: {e}")
            return None

    def extract_interview_details(self, title, summary, job_roles_context):
        content_text = f"Title: {title}\nSummary: {summary}"
        
        # Format job roles for context
        roles_text = "Internal Job Roles:\n"
        for role in job_roles_context:
            roles_text += f"- ID: {role['id']}, Name: {role['name']}\n"
            
        prompt = (
            f"Here are the existing Job Roles for this company:\n{roles_text}\n"
            "Analyze the interview experience. Match it to the MOST appropriate Internal Job Role ID from the list above. "
            "If no perfect match exists, pick the closest one (e.g. Software Engineer) or generic. " 
            "Then extract the rest of the interview details."
            "Please use the interview_experience_extraction tool to generate the interview experience JSON based on the content within the <content> tags. "
            "content tag contains json format content. All answers write as point of candidate experience and not as third person."
            "In interview experience, please keep format intact like HTML tags and rich text, replace these with the markdown tags."
            "Also when you are not able to get the value then put that field empty instead of having <UNKNOWN>."
            "Also current interview experience is lacking information around level, if you are able to guess based on the interview experience and from the title."
            "\n\nCONFIDENCE SCORE INSTRUCTIONS:\n"
            "Analyze the quality of this interview experience and assign a 'confidence_score' (0-100).\n"
            "- High Score (>80): Detailed description of rounds, clear questions asked, good structure.\n"
            "- Medium Score (50-79): Some details, but missing specific questions or very brief.\n"
            "- Low Score (<50): Extremely vague, one-liners, no meaningful details, or just 'I got rejected/accepted' without process details.\n"
            "- ZERO ROUNDS: If the post does not describe any specific interview rounds/questions, score MUST be below 40.\n"
            "Provide 'confidence_reasoning' explaining your score."
            )
        

        try:
            response = self.bedrock_service.converse(
                messages=[{"role": "user", "content": [{"text": content_text}, {"text": prompt}]}],
                inference_config={"maxTokens": 4096, "temperature": 0},
                tool_config={
                    "tools": self._get_interview_tools(),
                    "toolChoice": {"tool": {"name": "interview_experience_extraction"}}
                }
            )

            return self.bedrock_service.extract_tool_result(response)
        except Exception as e:
            print(f"Bedrock Detail Extraction Error: {e}")
            return None
