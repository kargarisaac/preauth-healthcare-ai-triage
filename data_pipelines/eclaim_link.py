# pip install xmlschema
import xmlschema
import xmltodict


def normalize_prior_authorization(xml_file_path: str) -> dict:
    """
    Normalizes prior authorization data from an XML file into a structured Python dictionary.

    The helper auto-detects two known XML formats:
      1. 2019/11 `PriorAuthorizationRequest` (DHD)
      2. 2011     `Prior.Authorization`     (HAAD / CommonTypes_20191113)

    Args:
        xml_file_path: Path to the XML file.

    Returns:
        dict: Normalised representation ready for downstream use.
    """
    with open(xml_file_path, "r", encoding="utf-8") as f:
        data = xmltodict.parse(f.read())

    root_tag = next(iter(data))

    if root_tag == "PriorAuthorizationRequest":
        return _normalize_dhd_2019(data[root_tag])
    elif root_tag == "Prior.Authorization":
        return _normalize_haad_2011(data[root_tag])
    else:
        raise ValueError(f"Unsupported root element: {root_tag}")


# ---------------------------------------------------------------------------
# Internal normalisers for each version
# ---------------------------------------------------------------------------


def _normalize_dhd_2019(payload: dict) -> dict:
    """Normalises the 2019/11 PriorAuthorizationRequest structure."""
    header = payload.get("Header", {})
    service_requests_container = payload.get("ServiceRequests", {})
    service_request_list = service_requests_container.get("ServiceRequest", [])
    if isinstance(service_request_list, dict):  # single entry returned as dict
        service_request_list = [service_request_list]

    normalized = {
        "schema_version": "2019/11",
        "sender": header.get("SenderID"),
        "receiver": header.get("ReceiverID"),
        "transaction_date": header.get("TransactionDateTime"),
        "authorization_id": payload.get("Header", {}).get("TransactionID"),
        "justification_text": payload.get("JustificationText"),
        "services": [],
    }

    for idx, svc in enumerate(service_request_list, 1):
        req_amount = svc.get("RequestedAmount", {})
        normalized["services"].append(
            {
                "id": idx,
                "activity_code": svc.get("ct:ActivityCode"),
                "diagnosis_code": svc.get("ct:DiagnosisCode"),
                "activity_date_time": svc.get("ct:ActivityDateTime"),
                "instructions": svc.get("ct:ActivityInstructions"),
                "requested_amount_currency": req_amount.get("@currency"),
                "requested_amount_value": req_amount.get("#text"),
            }
        )

    return normalized


def _normalize_haad_2011(payload: dict) -> dict:
    """Normalises the 2011 Prior.Authorization structure defined by PriorAuthorization.xsd."""
    header = payload.get("Header", {})
    auth = payload.get("Authorization", {})

    activities = auth.get("Activity", [])
    if isinstance(activities, dict):
        activities = [activities]

    normalized = {
        "schema_version": "2011",
        "sender": header.get("SenderID"),
        "receiver": header.get("ReceiverID"),
        "transaction_date": header.get("TransactionDate"),
        "record_count": header.get("RecordCount"),
        "disposition_flag": header.get("DispositionFlag"),
        "result": auth.get("Result"),
        "authorization_id": auth.get("ID"),
        "start": auth.get("Start"),
        "end": auth.get("End"),
        "comments": auth.get("Comments"),
        "services": [],
    }

    for act in activities:
        normalized["services"].append(
            {
                "id": act.get("ID"),
                "type": act.get("Type"),
                "code": act.get("Code"),
                "quantity": act.get("Quantity"),
                "net": act.get("Net"),
                "payment_amount": act.get("PaymentAmount"),
            }
        )

    return normalized


def validate_xml_against_schema(xml_file_path: str, schema_file_path: str):
    """
    Validates an XML file against a given XML Schema Definition (XSD) file.

    Args:
        xml_file_path (str): The path to the XML file to validate.
        schema_file_path (str): The path to the XSD schema file.

    Returns:
        bool: True if the XML is valid against the schema, False otherwise.
    """
    try:
        schema = xmlschema.XMLSchema11(schema_file_path)
        is_valid = schema.is_valid(xml_file_path)
        if not is_valid:
            print(f"Validation errors for {xml_file_path}:")
            for error in schema.iter_errors(xml_file_path):
                print(f"- {error.path}: {error.reason}")
        return is_valid
    except Exception as e:
        print(f"An error occurred during validation of {xml_file_path}: {e}")
        return False


if __name__ == "__main__":
    # Example usage for normalization:
    # file_path = "samples/prior_auth_request.xml"
    # file_path = "samples/sample_2.xml"
    # normalized_data = normalize_prior_authorization(file_path)
    # print("Normalized PriorAuth object:", normalized_data)

    # Validation of XML files against schemas:
    print("\n--- XML Validation ---")

    # Validate prior_auth_request.xml
    xml_file_1 = "samples/prior_auth_request.xml"
    schema_file_1 = "schemas/PriorAuthorization.xsd"
    print(f"Validating {xml_file_1} against {schema_file_1}...")
    if validate_xml_against_schema(xml_file_1, schema_file_1):
        print(f"{xml_file_1} is valid.")
    else:
        print(f"{xml_file_1} is NOT valid.")

    print("\n--- Code Impact ---")
    print(
        "The `normalize_prior_authorization` function assumes the input XML conforms to the structure expected from `prior_auth_request.xml`."
    )
    print(
        "If `sample_2.xml` is intended to be used with the normalization function, further adjustments might be needed to `normalize_prior_authorization` as its structure differs significantly."
    )
