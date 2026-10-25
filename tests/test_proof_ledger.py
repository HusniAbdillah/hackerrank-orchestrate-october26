import pytest
from deletion_audit.recommendations import assess_recommendation
from deletion_audit.agent_context import investigation_context, route_case
from deletion_audit.solver import decide_case
from test_ai_foundation import api_tools
from test_audit_recommendations import recommendation


def goal(value, kind):
    return next(e for e in value['audit_recommendation']['proof_ledger'] if e['kind'] == kind)


def test_ledger_cannot_promote_dirty_state_to_proven_treatment():
    tools = api_tools(); value = recommendation(tools); entry = goal(value, 'TREATMENT')
    source = tools.store.observations[0]
    entry.update(system_id=source.system_id,resource_id=source.resource_id,coverage_status='proven',
        accepted_source_references=[{'evidence_id':source.source_id,'observation_id':source.observation_id}])
    result = assess_recommendation(value,tools)
    assert 'LEDGER_COVERAGE_NOT_INDEPENDENTLY_ESTABLISHED' in {e['code'] for e in result['issues']}
    checked = next(e for e in result['proof_ledger'] if e['kind']=='TREATMENT')
    assert checked['independent_coverage']=='violated' and not checked['novel_fact']


def test_ledger_requires_actual_tool_inspection():
    tools = api_tools();value=recommendation(tools)
    goal(value,'IDENTITY')['tool_evidence_inspected']=['not_returned']
    result=assess_recommendation(value,tools,trace=[])
    assert 'LEDGER_OBSERVATION_NOT_TOOL_INSPECTED' in {i['code'] for i in result['issues']}


def test_ledger_rejects_unknown_source_lead_and_incomplete_categories():
    tools=api_tools();value=recommendation(tools)
    goal(value,'STATE')['admissible_source_leads']=[{'evidence_id':'invented','observation_id':'missing'}]
    value['audit_recommendation']['proof_ledger'].pop()
    result=assess_recommendation(value,tools)
    assert {'LEDGER_LEAD_NOT_ADMISSIBLE','PROOF_LEDGER_CATEGORIES_MISSING'} <= {i['code'] for i in result['issues']}


def test_incomplete_proposed_plan_cannot_have_proven_plan_ledger():
    tools=api_tools();value=recommendation(tools)
    value['audit_recommendation']['proposed_verifications']=[]
    goal(value,'PLAN')['coverage_status']='proven'
    result=assess_recommendation(value,tools)
    assert next(g for g in result['proof_ledger'] if g['kind']=='PLAN')['independent_validation']=='REJECTED'


@pytest.mark.parametrize('code',['NO_DIRECT_STATE','PRIMARY_PROFILE_VERIFICATION_UNGROUNDED','RETENTION_CONDITION_UNPROVEN','OCR_SUBJECT_LINK_UNCORROBORATED'])
def test_no_admissible_lead_means_no_paid_investigation(code):
    tools=api_tools();baseline=decide_case(tools.request,tools.store,tools.graph,tools.policy).diagnostic
    baseline['issues']=[{'code':code}]
    route=route_case(tools,baseline,investigation_context(tools,baseline))
    assert not route['eligible'] and route['irreducible']


def test_truncated_lead_inventory_does_not_claim_absence():
    tools=api_tools();base={'issues':[{'code':'NO_DIRECT_STATE'}]}
    context={'source_leads':[],'total_count':13,'shown_count':12,'truncated':True}
    assert route_case(tools,base,context)['reason']=='UNREVIEWED_ADMISSIBLE_SOURCE_PAGES'


def test_conditional_policy_route_is_not_blocked_by_legacy_empty_lead_gate(tmp_path,monkeypatch):
    import json
    from deletion_audit import agent_context
    from test_agent_corrections import agent_with_responses
    from test_ai_foundation import chat
    tools=api_tools()
    monkeypatch.setattr(agent_context,'route_case',lambda *args:{'eligible':True,'irreducible':False,
        'priority':50,'reason':'ORIGINAL_SHARED_SUPPORT_POLICY_CONTEXT'})
    agent,_=agent_with_responses(tmp_path,monkeypatch,[chat(json.dumps(recommendation(tools)))],audit_mode=True)
    base=decide_case(tools.request,tools.store,tools.graph,tools.policy).diagnostic
    assert not investigation_context(tools,base)['total_count']
    agent.investigate(tools,base)
    assert agent.events[-1]['status']=='LIVE_COMPLETED' and len(agent.ledger.records)==1
    # AI priority must affect execution, while CSV/case ordering stays canonical.
    from dataclasses import replace
    from types import SimpleNamespace
    from deletion_audit import solver
    from deletion_audit.providers import UsageLedger
    from test_solver import ROOT
    requests={f'case_{i}':replace(tools.request,case_id=f'case_{i}',request_text='Please export my data.') for i in (901,902)}
    monkeypatch.setattr(solver,'load_requests',lambda *args:requests)
    monkeypatch.setattr(solver,'ingest',lambda *args:tools.store)
    monkeypatch.setattr(solver,'enrich',lambda *args:None)
    monkeypatch.setattr(solver.IdentityGraph,'load',lambda *args:tools.graph)
    monkeypatch.setattr(agent_context,'route_case',lambda t,*args:{'eligible':True,'irreducible':False,
        'priority':int(t.request.case_id.split('_')[1]),'reason':'fixture'})
    order=[]
    stub=SimpleNamespace(audit_mode=True,max_cases=2,events=[],ledger=UsageLedger(),
        investigate=lambda t,*args:order.append(t.request.case_id) or [])
    run=solver.solve(ROOT/'dataset','sample',tmp_path/'ordered.csv',ai=stub)
    assert order==['case_902','case_901']
    assert [c['case_id'] for c in run['cases']]==['case_901','case_902']
