# pip install xmlschema
import xmlschema
from xml.etree import ElementTree as ET
import xmltodict, json


def normalize_prior_authorization(xml_file_path: str) -> dict:
    """
    Normalizes prior authorization data from an XML file into a structured Python dictionary.

    This function reads an XML file containing prior authorization request data,
    parses it, and extracts relevant fields into a flattened dictionary structure.
    It specifically handles the `PriorAuthorizationRequest` schema.

    Args:
        xml_file_path (str): The path to the XML file containing the prior authorization data.

    Returns:
        dict: A dictionary containing the normalized prior authorization data with the following keys:
            - 'sender' (str): The sender ID from the header.
            - 'receiver' (str): The receiver ID from the header.
            - 'transaction_date' (str): The transaction date and time from the header.
            - 'patient_member_id' (str): The patient's claim member ID.
            - 'patient_dob' (str): The patient's date of birth.
            - 'patient_gender' (str): The patient's gender code.
            - 'justification_text' (str): The justification text for the request.
            - 'services' (list): A list of dictionaries, each representing a service request with:
                - 'activity_code' (str): The activity code for the service.
                - 'diagnosis_code' (str): The diagnosis code for the service.
                - 'activity_date_time' (str): The activity date and time for the service.
                - 'activity_instructions' (str): Instructions for the activity.
                - 'requested_amount_currency' (str): The currency of the requested amount.
                - 'requested_amount_value' (str): The value of the requested amount.
    """
    # 1. Load the PriorAuthorization schema (it will bring in CommonTypes automatically)
    schema = xmlschema.XMLSchema11("schemas/PriorAuthorization.xsd")

    # 2. Validate an example file

    with open(xml_file_path) as f:
        data = xmltodict.parse(f.read())
    # data is now a nested Python dict
    # print(json.dumps(data["PriorAuthorizationRequest"], indent=2))

    # 4. Extract just the header and activity details we need
    raw_prior_auth_request = data.get("PriorAuthorizationRequest", {})
    header = raw_prior_auth_request.get("Header", {})
    service_requests_container = raw_prior_auth_request.get("ServiceRequests", {})
    service_request_list = service_requests_container.get("ServiceRequest", [])

    normalized = {
        "sender": header.get("SenderID"),
        "receiver": header.get("ReceiverID"),
        "transaction_date": header.get("TransactionDateTime"),
        "patient_member_id": raw_prior_auth_request.get("Patient", {}).get(
            "ct:ClaimMemberID"
        ),
        "patient_dob": raw_prior_auth_request.get("Patient", {}).get("ct:DateOfBirth"),
        "patient_gender": raw_prior_auth_request.get("Patient", {}).get(
            "ct:GenderCode"
        ),
        "justification_text": raw_prior_auth_request.get("JustificationText"),
        "services": [],
    }

    for service_req in service_request_list:
        requested_amount = service_req.get("RequestedAmount", {})
        normalized["services"].append(
            {
                "activity_code": service_req.get("ct:ActivityCode"),
                "diagnosis_code": service_req.get("ct:DiagnosisCode"),
                "activity_date_time": service_req.get("ct:ActivityDateTime"),
                "activity_instructions": service_req.get("ct:ActivityInstructions"),
                "requested_amount_currency": requested_amount.get("@currency"),
                "requested_amount_value": requested_amount.get("#text"),
            }
        )

    return normalized


if __name__ == "__main__":
    # Example usage:
    file_path = "samples/prior_auth_request.xml"
    normalized_data = normalize_prior_authorization(file_path)
    print("Normalized PriorAuth object:", normalized_data)

# 5. Send `normalized` downstream to your rules/AI pipeline
