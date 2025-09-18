import json
import os
from retell import Retell

# Initialize Retell client
client = Retell(api_key=os.environ["RETELL_API_KEY"])


def get_or_create_patient_agent():
    """Get existing agent or create new one if it doesn't exist"""

    # # First, try to find existing agent by name
    # agents = client.agent.list()

    # for agent in agents:
    #     if agent.agent_name == "Patient Care Agent":
    #         return agent.agent_id

    # If no existing agent found, create new one
    return create_patient_agent()


general_prompt = """You are a medical assistant calling patients to discuss their medical data.

You have access to patient medical data in JSON format through {{patient_data}}.

Your role:
1. Parse the JSON data from {{patient_data}} to understand the patient's medical information
2. Greet the patient by name (extract name from the JSON)
3. Explain their medical data in simple, understandable terms
4. Answer any questions they have about their medical results, diagnosis, treatment, etc.
5. Be empathetic, professional, and helpful
6. Try to explain as simple as possible and avoid complex medical jargon
7. Do not use long sentences and try to be concise.
Simple, short and clear. That's how you should talk to the patient.

Instructions:
- The {{patient_data}} contains JSON with fields like patient_name, medical_records, test_results, diagnosis, treatment_plan, etc.
- Extract the patient's name from the JSON and use it in your greeting
- Explain medical information clearly and avoid complex medical jargon
- If they ask about specific test results or treatments, refer to the information in the JSON data
- Be supportive and reassuring while being accurate about their medical information

Initial message: Parse {{patient_data}} to get the patient's name and medical information, then say "Hello [patient_name], this is calling from your doctor's office. I'm calling to discuss your recent medical results and answer any questions you might have about them."

Remember: All medical information you discuss should come from the {{patient_data}} JSON. Do not make up or assume any medical information not present in the data."""


def create_patient_agent():
    """Create a new patient care agent (only called if none exists)"""

    # Create Retell LLM
    llm_response = client.llm.create(
        general_prompt=general_prompt,
        model="gpt-5",
        model_temperature=0.3
    )

    # Create agent
    agent_response = client.agent.create(
        agent_name="Patient Care Agent",
        voice_id="11labs-Adrian",
        voice_speed=0.8,
        response_engine={
            "type": "retell-llm",
            "llm_id": llm_response.llm_id
        }
    )

    return agent_response.agent_id


def make_patient_call(patient_data):
    """Make a call using existing agent with patient-specific data"""

    # Get existing agent (or create if doesn't exist)
    agent_id = get_or_create_patient_agent()

    call_response = client.call.create_phone_call(
        from_number="+12293184505",
        # to_number="+15103690090",
        to_number="+16104004327",
        override_agent_id=agent_id,

        # Pass patient-specific data
        retell_llm_dynamic_variables={"patient_data": json.dumps(patient_data)}
    )

    return call_response
