from app.ai.governance.contracts import score_case

def evaluate_case(observed:dict,expected:dict)->dict:
    evidence=tuple(observed.get('evidence',[])) if isinstance(observed,dict) else ()
    score=score_case(observed,expected,evidence)
    return {'passed':score.passed,'safety_passed':score.safety_passed,'score':score.score,'failure_category':score.failure_category}

def aggregate(results:list[dict])->dict:
    if not results:return {'cases':0,'pass_rate':None,'safety_rate':None}
    return {'cases':len(results),'pass_rate':sum(bool(r['passed']) for r in results)/len(results),'safety_rate':sum(bool(r['safety_passed']) for r in results)/len(results)}
