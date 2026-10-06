"""run_demo.py - runs the FICTIONAL demonstration profile from the command line (spec section 32).

Usage:  python tools/run_demo.py            (prints to the terminal)
        python tools/run_demo.py > docs/DEMO_RUN.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.questionnaire import CATEGORY_INFO, DEMO_FIX_IDS, QUESTION_BY_ID, demo_profile_answers  # noqa: E402
from backend.services.assessment_engine import run_assessment  # noqa: E402
from backend.services.improvement_simulator import simulate_improvement  # noqa: E402


def main():
    answers = demo_profile_answers()
    r = run_assessment(answers)
    print("# Demonstration run - fictional profile\n")
    print("Entirely synthetic. Higher score = higher assessed exposure. Educational framework, not a guarantee of safety.\n")
    print(f"## Overall privacy risk\n**{r['overall']['score']}/100 - {r['overall']['level']}**\n")
    print("## Category scores\n| Category | Score |\n|---|---|")
    for k, v in r["category_scores"].items():
        print(f"| {CATEGORY_INFO[k]['label']} | {v:.0f}/100 |")
    print("\n## Top findings")
    for i, f in enumerate(r["findings"]["top_risks"], 1):
        print(f"{i}. [{f['severity']}] {f['description']}")
    print("\n## Recommendations (first of each priority)")
    for prio, items in r["recommendations"]["grouped"].items():
        if items:
            print(f"* **{prio}** ({len(items)}): {items[0]['recommendation']}")
    sim = simulate_improvement(answers, fix_ids=DEMO_FIX_IDS)
    print("\n## Improvement simulation")
    for c in sim["changes"]:
        print(f"* [x] {QUESTION_BY_ID[c['question_id']].fix}")
    print(f"\nCURRENT: {sim['before']['score']}/100 {sim['before']['level']}  ->  SIMULATED: {sim['after']['score']}/100 {sim['after']['level']}")
    print(f"**Risk reduction: {sim['risk_reduction']} points**\n")
    print(f"_{sim['disclaimer']}_")


if __name__ == "__main__":
    main()
