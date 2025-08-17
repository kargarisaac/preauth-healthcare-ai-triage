from pathlib import Path

import pytest


def test_pipeline_forward_intake_and_context_populated():
    from preauth_system.pipeline_module import PreAuthPipeline

    # Use the known demo fixture path from the repo docs
    xml_path = Path(
        "data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml"
    )
    if not xml_path.exists():
        pytest.skip(f"Fixture not found: {xml_path}")

    pipe = PreAuthPipeline()
    out = pipe.forward(xml_path=str(xml_path), xml_format="eclaim")

    # Basic structure is present
    assert isinstance(out, dict)
    assert "intake" in out
    assert "context" in out

    # Intake contains parsed patient info with services list
    intake = out["intake"]
    assert isinstance(intake.get("patient_info"), dict)
    services = intake.get("patient_info", {}).get("services", [])
    assert isinstance(services, list)
    assert len(services) >= 1

    # Context exposes unified_record presence boolean
    context = out["context"]
    assert isinstance(context.get("unified_record_present"), bool)

    # If patient_id was resolved, it should match fixture id
    pid = intake.get("patient_id")
    if pid is not None:
        assert pid == "Patient_007"


