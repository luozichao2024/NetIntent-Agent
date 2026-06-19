from pipeline import run_pipeline


def test_access_control_pipeline_success():
    result = run_pipeline("禁止学生网段访问管理服务器，但允许教师网段访问。")
    assert result["intent"]["intent_type"] == "access_control"
    assert result["policy"]["policy_type"] == "acl"
    assert result["final_status"] == "success"


def test_latency_pipeline_replans_successfully():
    result = run_pipeline("保证客户端到服务器的延迟低于50ms。")
    assert result["intent"]["intent_type"] == "latency_guarantee"
    assert result["verify_result"]["need_replan"] is True
    assert result["replan_result"] is not None
    assert result["final_status"] == "success"
