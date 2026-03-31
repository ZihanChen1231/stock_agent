from app.schemas.analysis import FieldAnalysisRequest


def test_field_analysis_request_defaults() -> None:
    request = FieldAnalysisRequest(field="tech")
    assert request.top_x == 3
    assert request.past_days == 7
