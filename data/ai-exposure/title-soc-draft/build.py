#!/usr/bin/env python3
"""DRAFT mapping of AI Jobs titles to BLS projections occupations (SOC 2018).

Rule-based, standard library only, no network. Every rule is a hypothesis for a person to review.
Inputs : data/titles/titles.json ; data/ai-exposure/bls/2026-11-07/ai-exposure-categories.csv
Outputs: title-soc-draft.csv, review-queue.csv, family-summary.csv, summary.json (this folder)
Run    : python3 data/ai-exposure/title-soc-draft/build.py   (from the ai-jobs root)
"""
import csv, json, re, collections, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLS = ROOT / "data/ai-exposure/bls/2026-11-07/ai-exposure-categories.csv"
occ = {}
for r in csv.DictReader(open(BLS, encoding="utf-8-sig")):
    occ[r["2025 National Employment Matrix code"]] = r

H, M, L = "high", "medium", "low"
# (name, regex on normalized title, soc, confidence, families or None). First match wins.
RULES = [
 ("chief-of-staff", r"^chief of\b", "11-1021", L, None),
 ("cyber-physical", r"cyber physical", "17-2199", L, None),
 ("exec-leadership", r"\b(vp|vice president|head of|director|chief)\b.*\b(ai|ml|machine learning|data|engineering|software|technology|platform|applied|analytics)\b", "11-3021", M, None),
 ("product-leadership", r"\b(vp|vice president|head of|director)\b.*\bproduct\b", "11-9199", L, None),
 ("eng-manager", r"engineering manager|(senior )?manager,? data engineering|(data science|ml|ai|engineering|research) (manager|director)|engineering director", "11-3021", M, None),
 ("distinguished", r"distinguished engineer|technical fellow|engineering fellow", "15-1252", L, None),
 ("recruiter", r"recruiter", "13-1071", H, None),
 ("tech-writer", r"technical writer|api writer|documentation (engineer|specialist)", "27-3042", H, None),
 ("sales-engineer", r"sales engineer|presales|pre sales", "41-9031", H, None),
 ("forward-deployed", r"forward deployed|deployed engineer", "15-1252", L, None),
 ("solutions-eng", r"solutions? (engineer|architect|consultant)|customer engineer", "41-9031", L, None),
 ("customer-success", r"customer success|technical account", "41-3091", L, None),
 ("implementation", r"implementation (manager|specialist|consultant)|onboarding (specialist|manager)|engagement manager|delivery manager|professional services|migration consultant|managed services", "13-1111", L, None),
 ("support-data-analyst", r"support data analyst", "15-2051", L, None),
 ("it-support", r"help ?desk|technical support|it support|desktop support|support (engineer|specialist)", "15-1232", M, None),
 ("usajobs-appsw", r"it specialist.*appsw", "15-1252", M, None),
 ("usajobs-datamgt", r"it specialist.*datamgt", "15-1243", M, None),
 ("usajobs-sysanalysis", r"it specialist.*sysanalysis", "15-1211", M, None),
 ("usajobs-infosec", r"it specialist.*infosec", "15-1212", M, None),
 ("usajobs-network", r"it specialist.*network", "15-1241", M, None),
 ("usajobs-sysadmin", r"it specialist.*sysadmin", "15-1244", M, None),
 ("usajobs-custspt", r"it specialist.*custspt", "15-1232", M, None),
 ("project-manager", r"project manager|program manager|program lead|scrum|agile coach|delivery lead|\bpmo\b|\btpm\b", "13-1082", M, None),
 ("ds-instructor", r"(instructor|lecturer).*(science|computer)|(computer|data) science (instructor|lecturer)", "25-1021", L, None),
 ("adjunct", r"adjunct instructor", "25-1021", L, None),
 ("ds-program", r"science program", "13-1082", L, None),
 ("data-scientist", r"data scientist|data science", "15-2051", H, None),
 ("applied-scientist", r"applied scientist|decision scientist|marketing scientist|forecasting scientist|computational social scientist|machine learning scientist|ml scientist|data and applied scientist", "15-2051", M, None),
 ("sys-admin-named", r"(linux|cluster|slurm|windows|unix|storage) administrator", "15-1244", H, None),
 ("aml-kyc", r"anti money|\baml\b|\bkyc\b|sanctions|financial crimes", "13-1041", M, None),
 ("fraud", r"fraud (analyst|investigator|strategy)", "13-1031", L, None),
 ("credit", r"credit (analyst|modeling)", "13-2041", M, None),
 ("fpa", r"fp and a|fpa|revenue analyst", "13-2051", M, None),
 ("pricing-sales-analyst", r"pricing analyst|sales analyst", "13-1161", L, None),
 ("planning", r"demand planner|inventory analyst", "13-1081", M, None),
 ("procurement", r"procurement", "13-1020", M, None),
 ("smart-contract", r"smart contract (auditor|audit)", "15-1212", L, None),
 ("it-audit", r"it audit|accountant|financial audit", "13-2011", M, None),
 ("grc", r"\bgrc\b|regulatory affairs", "13-1041", M, None),
 ("pr-comms", r"public relations|communications specialist", "27-3031", M, None),
 ("brand", r"brand (strategist|manager)", "11-2021", L, None),
 ("social-media", r"social media", "13-1161", L, None),
 ("producer", r"producer", "27-2012", L, None),
 ("narrative", r"narrative designer|ux writer", "27-3043", L, None),
 ("kb-writer", r"knowledge base writer|technical content creator", "27-3042", M, None),
 ("speech-pathologist", r"speech language pathologist", "29-1127", H, None),
 ("biomedical", r"biomedical engineer|medical imaging (engineer|scientist)", "17-2031", L, None),
 ("computer-scientist", r"computer scientist", "15-1221", M, None),
 ("ontology", r"ontologist|taxonomist|taxonomy", "15-1299", L, None),
 ("project-coordinator", r"project (coordinator|analyst)|release manager", "13-1082", M, None),
 # QA / test / evaluation
 ("pentest-first", r"penetration|pentest|adversarial tester", "15-1212", H, None),
 ("policy-analyst", r"policy analyst|ai ethic|ethicist", "19-3099", L, None),
 ("ai-auditor", r"ai auditor|algorithm(ic)? auditor|bias auditor|auditor", "13-1041", L, None),
 ("comp-chemist", r"computational chemist", "19-2031", M, None),
 ("it-admin-saas", r"(salesforce|servicenow|netsuite|sap|oracle) administrator", "15-1244", L, None),
 ("it-risk", r"(it|technology|third party|cyber) risk", "15-1212", L, {"security","it-enterprise"}),
 ("devrel", r"developer (advocate|relations|evangelist|educator|marketing|experience)|devrel|evangelist|advocate", "13-1151", L, None),
 ("community", r"community (manager|engineer|specialist)", "27-3031", L, None),
 ("content-developer", r"(curriculum|course|e learning|training content|education content|technical content) developer", "25-9031", M, None),
 ("webflow", r"webflow|frontend designer", "15-1254", M, None),
 ("ml-platform", r"(ai|ml|llm|agent|inference|model serving|training) (platform|infrastructure|reliability)|data (reliability|observability)|search infrastructure", "15-1252", M, None),
 ("data-quality-eng", r"data quality engineer", "15-1252", L, None),
 ("med-device-qa", r"(medical device|hardware in the loop).*(quality|test)|(quality|test).*(medical device|hardware in the loop)", "17-2199", L, None),
 ("plc", r"\bplc\b", "17-3024", L, None),
 ("annotation", r"annotat|labeler|labeling|\brater\b|rating", "43-9021", L, None),
 ("evaluator", r"model evaluator|prompt evaluator|evaluation specialist|data quality specialist|language quality", "13-1199", L, None),
 ("qa-test", r"\bsdet\b|software development engineer in test|\bqa\b|quality assurance|test engineer|tester|automation test", "15-1253", H, None),
 ("ai-quality", r"(ai|model|ml|llm) (evaluation|quality|eval)( engineer| analyst)|evaluation engineer|quality engineer", "15-1253", M, None),
 # security, compliance, risk
 ("compliance", r"compliance|regulatory technology|regtech", "13-1041", M, None),
 ("security", r"security|cyber|penetration|pentest|appsec|infosec|threat|red team|reverse engineer|malware|smart contract audit|cryptograph", "15-1212", M, None),
 ("trust-safety", r"trust and safety|content moderat|model behavior|safeguards|abuse analyst", "13-1199", L, None),
 ("quant-risk", r"(model|market|credit|quantitative|financial|operational|liquidity) risk", "13-2054", H, None),
 ("tech-risk", r"\brisk\b", "13-2054", L, None),
 ("underwriting", r"underwrit", "13-2053", H, None),
 # science / stats
 ("or-analyst", r"operations research", "15-2031", H, None),
 ("statistician", r"statistician|biostatistic", "15-2041", H, None),
 ("actuary", r"actuar", "15-2011", H, None),
 ("economist", r"economist", "19-3011", H, None),
 ("epidemiology", r"epidemiolog", "19-1041", H, None),
 ("bioinformatics", r"bioinformatic|genomic|computational biolog", "19-1029", M, None),
 ("health-informatics", r"clinical informatics|health informatics", "15-1211", M, None),
 ("quant-analyst", r"quant(itative)? (analyst|researcher|strategist)", "13-2051", M, None),
 ("quant-dev", r"quant(itative)? (developer|engineer)", "15-1252", M, None),
 ("linguist", r"computational linguist|natural language (scientist|researcher)", "15-1221", M, None),
 ("linguist-plain", r"linguist", "19-3099", L, None),
 ("research", r"research scientist|research engineer|member of technical staff|ai residency|postdoc|ai scientist|ai researcher|safety researcher|science engineer", "15-1221", M, None),
 ("user-research", r"user research|ux research|design research", "13-1161", L, None),
 # data
 ("dba", r"database administrator|\bdba\b", "15-1242", H, None),
 ("data-architect", r"data architect|database architect|knowledge graph architect|semantic architect", "15-1243", H, None),
 ("db-engineer", r"database (engineer|developer)|vector database|graph database", "15-1243", M, None),
 ("data-engineer", r"data engineer|\betl\b|data pipeline|analytics engineer|data platform|data operations engineer|feature engineer|data infrastructure|data integration|knowledge graph|semantic engineer", "15-1252", L, None),
 ("bi", r"business intelligence|\bbi\b|looker|tableau|power bi|dashboard", "15-2051", M, None),
 ("systems-analyst", r"it business systems|business systems analyst|systems analyst", "15-1211", H, None),
 ("business-analyst", r"business analyst", "13-1111", M, None),
 ("data-analyst", r"data analyst|analytics analyst|insights analyst|reporting analyst", "15-2051", M, None),
 ("fin-analyst", r"financial analyst|finance data|investment technology|treasury|payments analyst", "13-2051", L, None),
 ("supply-chain", r"supply chain|logistics analyst", "13-1081", M, None),
 ("claims", r"claims analyst", "13-1031", M, None),
 ("marketing-analyst", r"marketing analyst|growth analyst|paid media|search marketing|\bseo\b|market research|marketing science", "13-1161", M, None),
 ("ops-analyst", r"process improvement|operations analyst|strategy and operations|management consult|business consult", "13-1111", M, None),
 # infra
 ("hpc-admin", r"hpc (administrator|systems)", "15-1244", H, None),
 ("network-admin", r"network (administrator|operations)|systems? administrator|sysadmin|it operations", "15-1244", H, None),
 ("network-eng", r"network (engineer|architect)", "15-1241", M, None),
 ("cloud-architect", r"cloud architect|infrastructure architect|systems architect", "15-1299", M, None),
 ("devops", r"devops|\bsre\b|site reliability|release engineer|build engineer|production engineer|observability|reliability engineer|capacity (engineer|planning)|container engineer|kubernetes|(cloud|infrastructure|platform) (engineer|operations)|(aws|azure|google cloud|gcp) (engineer|consultant)", "15-1244", M, None),
 # hardware / robotics
 ("hardware", r"fpga|\basic\b|hardware engineer|chip|silicon|\brtl\b", "17-2061", M, None),
 ("rf", r"rf engineer|antenna|electronics engineer", "17-2072", H, None),
 ("mechatronics", r"mechatronic", "17-3024", M, None),
 ("robotics-engineer", r"robotics engineer|robotics controls|controls engineer", "17-2199", M, None),
 ("robotics-software", r"(robotics (software|perception)|autonomy|autonomous|flight|avionics|uav|vehicle|automotive|embedded|firmware|iot|drone) (software|engineer|developer)", "15-1252", M, None),
 ("robotics-eng", r"robotics|controls engineer", "17-2199", L, None),
 # software
 ("product-manager", r"product manager|product owner|product lead|product management", "13-1082", L, None),
 ("software-eng", r"software engineer|software developer|\bsde\b|\bswe\b|software consultant|programmer", "15-1252", H, None),
 ("web-dev", r"web developer|front ?end (developer|engineer)|ui (developer|engineer)|\\bux engineer", "15-1254", M, None),
 ("ai-ml-engineer", r"\b(ai|ml|machine learning|llm|genai|generative ai|deep learning|nlp|computer vision|speech|agent|prompt|chatbot|inference|model serving|mlops|search|relevance|ranking|voice)\b.*\b(engineer|developer|architect|builder)|prompt engineer|ai builder", "15-1252", M, None),
 ("enterprise-dev", r"(crm|hubspot|salesforce|netsuite|servicenow|workday|sap|oracle|erp|rpa|low code|mainframe|enterprise applications?) (developer|engineer)|mainframe|rpa developer|low code", "15-1252", M, None),
 ("enterprise-consult", r"(crm|hubspot|salesforce|netsuite|servicenow|sap|oracle|erp) (consultant|administrator)|it consultant|technology consultant|it service management|itsm|integration (specialist|architect)|it business|digital transformation", "15-1211", L, None),
 ("integration-eng", r"integration engineer", "15-1252", L, None),
 ("developer", r"developer|programmer|\bdev\b|full ?stack|front ?end|back ?end|\bios\b|android|compiler|\bgpu\b|cuda|kernel|\bhpc\b|parallel programming|engine programmer|gameplay|game engineer|unreal|unity|\bvr\b|\bar\b|\bxr\b|engineer, game|real time engineer|3d engineer|procedural", "15-1252", M, None),
 # design
 ("lx-designer", r"learning experience designer", "25-9031", M, None),
 ("ux-designer", r"ux designer|ui designer|product designer|interaction designer|experience designer|conversational designer|voice ux|web designer|digital designer|accessibility specialist", "15-1255", M, None),
 ("service-designer", r"service designer", "15-1255", L, None),
 ("motion", r"motion graphics|animator|technical artist|3d artist|\bvfx\b", "27-1014", M, None),
 ("graphic", r"graphic designer|visual designer|brand designer", "27-1024", H, None),
 ("game-designer", r"game designer|level designer", "27-1029", L, None),
 ("human-factors", r"human factors", "17-2112", M, None),
 # marketing / content
 ("marketing-manager", r"marketing manager|growth manager|head of marketing", "11-2021", H, None),
 ("content", r"content (strategist|marketing|writer|designer)|copywriter", "27-3043", M, None),
 ("marketing-ops", r"email marketing|marketing automation|product marketing|demand gen|performance marketing|marketing specialist", "13-1161", M, None),
 # education
 ("curriculum", r"curriculum|instructional design|learning design", "25-9031", H, None),
 ("trainer", r"educator|technical trainer|trainer|training specialist|training manager|enablement|instructor|teaching|evangelist|advocate|developer relations|devrel|community manager", "13-1151", L, None),
 ("professor", r"professor|lecturer", "25-1021", L, None),
 # product / project
 ("fam-sw-engineer", r"\bengineer\b|\barchitect\b|\bdeveloper\b|\bprogrammer\b", "15-1252", M, {"ai-engineering","ml-engineering","software-engineering","search-nlp","gamedev-graphics","hpc-ai-infra"}),
 ("fam-data-engineer", r"\bengineer\b|\barchitect\b|\bdeveloper\b|\bmodeler\b", "15-1252", L, {"data-engineering"}),
 ("fam-devops", r"engineer|administrator|specialist|analyst|consultant", "15-1244", M, {"cloud-devops-sre"}),
 ("fam-security", r".", "15-1212", M, {"security"}),
 ("fam-evals", r".", "15-1253", M, {"evals-quality"}),
 ("fam-health-it", r"epic|cerner|ehr|clinical applications|interoperability", "15-1211", M, {"healthcare-ai"}),
]
CODES = {r[2] for r in RULES}
BORROWED = {"data-engineer","product-manager","annotation","evaluator","trust-safety","ontology","forward-deployed","ai-ml-engineer","ml-platform","devops","robotics-eng","robotics-engineer","developer-advocate","devrel","community","customer-success","distinguished","fam-data-engineer","user-research","game-designer","policy-analyst","ai-auditor","producer"}
FAMILY_DEFAULT = {
 "ai-engineering":"15-1252","ml-engineering":"15-1252","data-science":"15-2051","research":"15-1221","data-engineering":"15-1252",
 "analytics":"15-2051","software-engineering":"15-1252","cloud-devops-sre":"15-1244","hpc-ai-infra":"15-1252","security":"15-1212",
 "ai-governance-risk":"13-1199","evals-quality":"15-1253","ai-training-data":"13-1199","product-management":"13-1082",
 "solutions-customer":"41-9031","devrel-education":"13-1151","design-ux":"15-1255","marketing-brand":"13-1161","healthcare-ai":"15-1211",
 "fintech-quant":"13-2051","it-enterprise":"15-1211","robotics-cps":"17-2199","gamedev-graphics":"15-1252","search-nlp":"15-1252",
 "public-sector-research":"13-1111","leadership":"11-3021","early-career":None,
}
missing = [c for c in CODES | {v for v in FAMILY_DEFAULT.values() if v} if c not in occ]
assert not missing, f"codes not in the BLS list: {missing}"

STRIP = re.compile(r"\b(senior|sr|junior|jr|associate|staff|principal|lead|intern|internship|graduate|entry level|new grad|trainee|early career)\b|\b(i|ii|iii|iv)\b$")
def norm(t):
    t = t.lower().replace("&", " and ").replace("+", " plus ")
    t = re.sub(r"[^a-z0-9()]+", " ", t).strip()
    t = re.sub(r"\(([a-z0-9 ]+)\)", r" \1 ", t)
    return re.sub(r"\s+", " ", STRIP.sub(" ", t)).strip()

fam = json.load(open(ROOT / "data/titles/titles.json"))["families"]
rows = []
for f in fam:
    for title in f["titles"]:
        n = norm(title)
        hit = next((r for r in RULES if re.search(r[1], n) and (r[4] is None or f["key"] in r[4])), None)
        if hit:
            rule, _, soc, conf, _f = hit
        else:
            soc, conf, rule = FAMILY_DEFAULT[f["key"]], "family-default", "family-default"
            if soc is None:
                conf, rule = "none", "program-name-not-an-occupation"
        o = occ.get(soc) if soc else None
        agree = ""
        if conf != "family-default" and soc and FAMILY_DEFAULT[f["key"]] and soc != FAMILY_DEFAULT[f["key"]]:
            agree = "differs-from-family-default"
        rows.append({
            "family": f["key"], "title": title, "soc_code": soc or "", "soc_title": o["2025 National Employment Matrix title"] if o else "",
            "confidence": conf, "rule": rule, "flag": agree,
            "note": "no dedicated SOC; nearest borrowed" if rule in BORROWED else "",
            "bls_ai_exposure": o["Relative AI exposure"] if o else "",
            "employment_2025_thousands": o["Employment, 2025"] if o else "",
            "employment_change_pct_2025_35": o["Employment change, percent, 2025–35"] if o else "",
            "median_wage_2025": o["Median annual wage, dollars, 2025"] if o else "",
        })

def write(name, rs):
    with open(HERE / name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rs[0])); w.writeheader(); w.writerows(rs)
write("title-soc-draft.csv", rows)
write("review-queue.csv", [r for r in rows if r["confidence"] in ("low", "family-default", "none") or r["flag"]])

fs = []
for f in fam:
    rs = [r for r in rows if r["family"] == f["key"]]
    c = collections.Counter(r["confidence"] for r in rs); e = collections.Counter(r["bls_ai_exposure"] or "unmapped" for r in rs)
    socs = collections.Counter(r["soc_title"] for r in rs if r["soc_title"]).most_common(3)
    fs.append({"family": f["key"], "titles": len(rs), **{k: c.get(k, 0) for k in ("high","medium","low","family-default","none")},
               **{f"exp_{k}": e.get(k, 0) for k in ("Low","Moderate","High","Very high","unmapped")},
               "top_occupations": " | ".join(f"{t} ({n})" for t, n in socs)})
write("family-summary.csv", fs)
tot = collections.Counter(r["confidence"] for r in rows)
summary = {"titles": len(rows), "confidence": dict(tot), "distinct_socs": len({r["soc_code"] for r in rows if r["soc_code"]}),
           "exposure": dict(collections.Counter(r["bls_ai_exposure"] or "unmapped" for r in rows)),
           "differs_from_family_default": sum(1 for r in rows if r["flag"])}
json.dump(summary, open(HERE / "summary.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
